"""Plan and, only after a reviewed freeze, execute the CP8 workflow continuations.

The default command is offline and prints a plan.  The paid path requires all of:
``--execute-approved-continuations``, an approval manifest, the exact ``continuation-v1`` tag at
HEAD, matching protocol/inventory hashes, and an explicit user-approval record.  It never changes
the frozen workflow records or diagnostic replay outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from experiments.run_price_matched_workflow import registry as price_matched_registry
from src.analysis.reruns import resolve_workflow_reruns
from src.bedrock.models import ModelRegistry, load_registry
from src.bedrock.provenance import hash_file, hash_tree
from src.bedrock.usage import UsageLimits
from src.contracts import ResourceLimits, StageId, StageStatus, WorkflowRunRecord
from src.evaluation.cleaning import load_project
from src.workflow.handoff import StageArtifacts, build_and_save
from src.workflow.stages import StageContext, prompt_input_token_upper_bound, run_reporting

REPO = Path(__file__).resolve().parents[1]
TAG = "continuation-v1"
EXPERIMENT_ID = "continuation_v1_posthoc_v3"
MANIFEST = REPO / "results/processed/continuation_protocol_manifest.json"
DIAGNOSTICS = REPO / "results/processed/diagnostics_posthoc.json"
PINNED_IMAGE = "sha256:88988a15503bdb96538c3dd62244a79879d5c7848397db18b1267ccfd0a9727a"
HARD_CAP_USD = 15.0
RETRY_ATTEMPTS = 5
APPROVAL_QUESTION = "花费上限 $15（预计实际约 $1.41），补跑这 40 次，行吗？"
APPROVAL_WORDING = "批准了"
APPROVAL_DATE = "2026-11-19"
LEDGER = REPO / "results/raw/ledgers/continuations.json"
INVOCATIONS = REPO / "results/raw/continuations/invocations.jsonl"
RECORDS = REPO / "results/raw/workflow_continuations/continuation_v1.jsonl"
RUNS = REPO / "results/raw/continuations/runs"
EVENTS = REPO / "results/raw/continuations/execution_events.jsonl"

GROUPS = {
    "original_4096": {
        "part_b": REPO / "results/raw/workflow_runs/expB_paths_v3.jsonl",
        "invocations": REPO / "results/raw/invocations.jsonl",
        "experiment": "expB_paths_v3",
        "max_tokens": 4096,
        "names": {"A": "Sonnet 4.6", "B": "Nova Pro", "C": "gpt-oss-120b"},
    },
    "price_matched_16384": {
        "part_b": REPO / "results/raw/workflow_runs/expB_price_matched_workflow_v3.jsonl",
        "invocations": REPO / "results/raw/price_matched_workflow/invocations.jsonl",
        "experiment": "expB_price_matched_workflow_v3",
        "max_tokens": 16384,
        "names": {"A": "Sonnet 4.6", "B": "Kimi K3", "C": "GLM 5"},
    },
}


@dataclass(frozen=True)
class ContinuationCell:
    group: str
    original: WorkflowRunRecord
    failed_stage_index: int
    replay: dict[str, Any]

    @property
    def remaining(self) -> tuple[tuple[int, StageId, str], ...]:
        stages = (StageId.CLEANING, StageId.ANALYSIS, StageId.REPORTING)
        return tuple((i, stages[i], self.original.models[i])
                     for i in range(self.failed_stage_index + 1, len(self.original.models)))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _registry(group: str) -> ModelRegistry:
    if group == "original_4096":
        return load_registry(REPO / "configs/models.yaml")
    if group == "price_matched_16384":
        return price_matched_registry(16384)
    raise ValueError(group)


def _effective(group: str) -> list[WorkflowRunRecord]:
    raw = [WorkflowRunRecord.model_validate(row) for row in read_jsonl(GROUPS[group]["part_b"])]
    return resolve_workflow_reruns(raw)[0] if group == "price_matched_16384" else raw


def eligible_cells() -> list[ContinuationCell]:
    replay_rows = json.loads(DIAGNOSTICS.read_text())["serialization_replay"]["records"]
    rows: list[ContinuationCell] = []
    for group in GROUPS:
        effective = {run.run_id: run for run in _effective(group)}
        for replay in replay_rows:
            if replay["group"] != group or replay["part"] != "B" or \
                    not replay["would_pass_without_serialization_bug"]:
                continue
            run = effective.get(replay["run_id"])
            if run is None:
                continue
            index = ("cleaning", "analysis", "reporting").index(replay["stage"])
            failed = run.stages[index]
            if "Object of type int64 is not JSON serializable" not in str(failed.failure_detail):
                raise ValueError(f"diagnostic replay does not match frozen failure: {run.run_id}")
            downstream = run.stages[index + 1:]
            never_ran = all(stage.status in (StageStatus.BLOCKED_BY_INVALID_ARTIFACT,
                                             StageStatus.NOT_RUN_UPSTREAM_FAILURE)
                            for stage in downstream)
            if downstream and never_ran:
                rows.append(ContinuationCell(group, run, index, replay))
    rows.sort(key=lambda cell: (cell.group, cell.original.project_id, cell.original.path_id,
                                cell.original.repeat_index, cell.original.run_id))
    return rows


def inventory_sha256(cells: list[ContinuationCell]) -> str:
    payload = [{"group": c.group, "continued_from": c.original.run_id,
                "recovered_stage": c.replay["stage"], "recovered_output_sha256": c.replay["output_sha256"],
                "remaining": [(stage.value, alias) for _, stage, alias in c.remaining]}
               for c in cells]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _observed_means(group: str) -> dict[tuple[str, str], dict[str, float]]:
    effective_ids = {run.run_id for run in _effective(group)}
    rows = [row for row in read_jsonl(GROUPS[group]["invocations"])
            if row["context"]["experiment_id"] == GROUPS[group]["experiment"]
            and row["context"]["run_id"] in effective_ids and row["status"] == "success"]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model_alias"], row["context"]["stage_id"])].append(row)
    return {key: {"n": len(values),
                  "mean_input_tokens": sum(v["input_tokens"] for v in values) / len(values),
                  "mean_output_tokens": sum(v["output_tokens"] for v in values) / len(values)}
            for key, values in grouped.items()}


def _cost(registry: ModelRegistry, alias: str, input_tokens: float, output_tokens: float) -> float:
    pricing = registry.get(alias).pricing
    return (input_tokens * pricing.input_per_mtok + output_tokens * pricing.output_per_mtok) / 1_000_000


def budget(cells: list[ContinuationCell]) -> dict[str, Any]:
    calls = [(cell, stage, alias) for cell in cells for _, stage, alias in cell.remaining]
    result: dict[str, Any] = {"static_worst_case": {"by_group_alias": {}},
                              "realistic_estimate": {"by_group_alias": {}}}
    for group in GROUPS:
        registry = _registry(group)
        means = _observed_means(group)
        max_tokens = GROUPS[group]["max_tokens"]
        for alias in "ABC":
            subset = [(cell, stage) for cell, stage, model in calls
                      if cell.group == group and model == alias]
            if not subset:
                continue
            worst_input = 0
            realistic_input = realistic_output = 0.0
            observed_n = 0
            stages = Counter()
            for cell, stage in subset:
                spec, _, pdir = load_project(REPO / "datasets/projects" / cell.original.project_id)
                worst_input += prompt_input_token_upper_bound(stage, spec, pdir, "v3") * RETRY_ATTEMPTS
                observed = means[(alias, stage.value)]
                realistic_input += observed["mean_input_tokens"]
                realistic_output += observed["mean_output_tokens"]
                observed_n = int(observed["n"])
                stages[stage.value] += 1
            worst_output = len(subset) * max_tokens * RETRY_ATTEMPTS
            key = f"{group}|{alias}"
            result["static_worst_case"]["by_group_alias"][key] = {
                "logical_calls": len(subset), "maximum_attempts": len(subset) * RETRY_ATTEMPTS,
                "stages": dict(sorted(stages.items())), "input_tokens": worst_input,
                "output_tokens": worst_output, "cost_usd": _cost(registry, alias, worst_input, worst_output)}
            result["realistic_estimate"]["by_group_alias"][key] = {
                "logical_calls": len(subset), "assumed_attempts": len(subset),
                "stages": dict(sorted(stages.items())), "observed_sample_n": observed_n,
                "input_tokens": realistic_input, "output_tokens": realistic_output,
                "cost_usd": _cost(registry, alias, realistic_input, realistic_output)}
    for view in result.values():
        values = view["by_group_alias"].values()
        view["total"] = {"logical_calls": sum(v["logical_calls"] for v in values),
                         "attempts": sum(v["maximum_attempts"] if "maximum_attempts" in v
                                         else v["assumed_attempts"] for v in values),
                         "input_tokens": sum(v["input_tokens"] for v in values),
                         "output_tokens": sum(v["output_tokens"] for v in values),
                         "cost_usd": sum(v["cost_usd"] for v in values)}
    result["static_worst_case"]["assumption"] = \
        "five paid attempts per logical call; conservative prompt bound and full group maxTokens on every attempt"
    result["realistic_estimate"]["assumption"] = \
        "one attempt per logical call; observed successful Part B mean input/output tokens for the same group, alias and stage"
    result["proposed_hard_cap_usd"] = HARD_CAP_USD
    result["cap_below_static_worst_case"] = HARD_CAP_USD < result["static_worst_case"]["total"]["cost_usd"]
    return result


def build_plan() -> dict[str, Any]:
    cells = eligible_cells()
    recovered = Counter((cell.group, cell.replay["model_alias"], cell.replay["stage"]) for cell in cells)
    calls = Counter((cell.group, alias, stage.value) for cell in cells for _, stage, alias in cell.remaining)
    return {
        "protocol": "continuation-v1-posthoc", "status": "paid_approved_pending_freeze_tag",
        "label": "post-hoc corrected-view continuation; frozen records remain authoritative",
        "eligible_cells": len(cells), "inventory_sha256": inventory_sha256(cells),
        "recovered_stage_counts": {"|".join(key): value for key, value in sorted(recovered.items())},
        "remaining_call_counts": {"|".join(key): value for key, value in sorted(calls.items())},
        "budget": budget(cells),
        "settings": {"original_4096": {"maxTokens": 4096, "temperature": 0},
                     "price_matched_16384": {"maxTokens": 16384,
                                              "temperature": {"A": 0, "B": "omitted", "C": 0}},
                     "prompt_version": "v3", "pinned_image": PINNED_IMAGE,
                     "retry_policy": "existing transient-only policy, maximum five attempts"},
        "compatibility_smoke_test": {"needed": False,
            "reason": "the same six models, API schemas, parameters and prompt version already completed the source runs"},
        "execution_gate": {"default": "plan only", "required_flag": "--execute-approved-continuations",
                           "required_tag": TAG, "manifest": str(MANIFEST.relative_to(REPO)),
                           "explicit_paid_approval_present": True,
                           "approval_question": APPROVAL_QUESTION,
                           "approval_wording": APPROVAL_WORDING, "approval_date": APPROVAL_DATE},
        "outputs": {"records": str(RECORDS.relative_to(REPO)), "runs": str(RUNS.relative_to(REPO)),
                    "invocations": str(INVOCATIONS.relative_to(REPO)), "ledger": str(LEDGER.relative_to(REPO)),
                    "complete_record_lines": 40,
                    "progress_field": "continued_from"},
    }


def protocol_hashes() -> dict[str, Any]:
    files = [REPO / "docs/CORRECTED_VIEW_RULES.md", REPO / "docs/CONTINUATION_PROTOCOL.md",
             REPO / "docs/reviews/2026-11-19_cp8a_review.md", Path(__file__),
             REPO / "experiments/build_continuation_manifest.py",
             REPO / "experiments/analyze_diagnostics_posthoc.py",
             REPO / "experiments/run_price_matched_workflow.py",
             DIAGNOSTICS, GROUPS["original_4096"]["part_b"],
             GROUPS["price_matched_16384"]["part_b"], REPO / "configs/models.yaml",
             GROUPS["original_4096"]["invocations"], GROUPS["price_matched_16384"]["invocations"],
             REPO / "results/processed/independent_v2/price_matched_model_verification.json",
             REPO / "src/bedrock/client.py", REPO / "src/bedrock/usage.py",
             REPO / "src/bedrock/models.py", REPO / "src/contracts/records.py",
             REPO / "src/workflow/handoff.py", REPO / "src/workflow/stages.py",
             REPO / "src/workflow/executor.py", REPO / "src/evaluation/reporting_v3.py"]
    return {"files": {str(path.relative_to(REPO)): hash_file(path) for path in files},
            "replay_tree": hash_tree(REPO / "results/processed/diagnostics_posthoc_replay"),
            "prompts_v3_tree": hash_tree(REPO / "prompts/v3"),
            "projects_tree": hash_tree(REPO / "datasets/projects")}


def _tags_at_head() -> set[str]:
    result = subprocess.run(["git", "tag", "--points-at", "HEAD"], cwd=REPO, check=True,
                            text=True, capture_output=True)
    return set(result.stdout.split())


def verify_frozen_approval() -> dict[str, Any]:
    if not MANIFEST.exists():
        raise SystemExit("no continuation freeze/approval manifest exists")
    manifest = json.loads(MANIFEST.read_text())
    if manifest.get("status") != "continuation_frozen_paid_execution_approved":
        raise SystemExit("continuation protocol is not frozen and paid-approved")
    expected_approval = {"question": APPROVAL_QUESTION, "wording": APPROVAL_WORDING,
                         "date": APPROVAL_DATE}
    if manifest.get("paid_execution_approved") is not True or manifest.get("approval") != expected_approval:
        raise SystemExit("continuation execution lacks explicit user approval wording")
    if manifest.get("required_tag") != TAG or TAG not in _tags_at_head():
        raise SystemExit(f"continuation execution requires exact tag {TAG} at HEAD")
    if manifest.get("hard_budget_cap_usd") != HARD_CAP_USD:
        raise SystemExit("continuation hard cap differs from the reviewed $15 proposal")
    if manifest.get("logical_call_ceiling") != 40 or manifest.get("complete_record_lines") != 40 or \
            manifest.get("ledger_path") != str(LEDGER.relative_to(REPO)):
        raise SystemExit("continuation call count, progress target, or separate ledger differs from approval")
    cells = eligible_cells()
    if manifest.get("eligible_cells") != len(cells) or manifest.get("inventory_sha256") != inventory_sha256(cells):
        raise SystemExit("continuation inventory differs from the frozen manifest")
    if manifest.get("hashes") != protocol_hashes():
        raise SystemExit("continuation protocol hashes differ from the frozen manifest")
    return manifest


def continuation_run_id(cell: ContinuationCell) -> str:
    payload = f"{EXPERIMENT_ID}|{cell.group}|{cell.original.run_id}|{cell.replay['output_sha256']}"
    return f"{EXPERIMENT_ID}-{hashlib.sha256(payload.encode()).hexdigest()[:16]}"


def _artifact_file(stage, suffix: str) -> Path:
    path = next((REPO / p for p in stage.output_artifacts if p.endswith(suffix)), None)
    if path is None or not path.is_file():
        raise FileNotFoundError(f"saved artifact ending {suffix!r} not found")
    return path


def original_cleaning_artifact(cell: ContinuationCell) -> StageArtifacts:
    stage = cell.original.stages[0]
    parsed_path = _artifact_file(stage, "/parsed.json")
    code_path = _artifact_file(stage, "/code.py")
    parsed = json.loads(parsed_path.read_text())
    cleaned = _artifact_file(stage, "/output/" + parsed["output_filename"])
    summary = next((REPO / p for p in stage.output_artifacts if p.endswith("/output/cleaning_summary.json")), None)
    summary_obj = json.loads(summary.read_text()) if summary and summary.is_file() else None
    return StageArtifacts(stage=StageId.CLEANING, model_alias=stage.model_alias, parsed_output=parsed,
                          executed_code=code_path.read_text(),
                          files={"cleaned_csv": str(cleaned)} | ({"cleaning_summary": str(summary)} if summary and summary.is_file() else {}),
                          verified_results={"cleaning_summary": summary_obj,
                                            "cleaned_csv_sha256": hash_file(cleaned)},
                          validation_status="passed" if stage.validation and stage.validation.hard_pass else "failed")


def recovered_analysis_artifact(cell: ContinuationCell) -> StageArtifacts:
    if cell.replay["stage"] != "analysis" or not cell.replay["frozen_validation"]["hard_pass"]:
        raise ValueError("frozen continuation inventory currently permits recovered analysis passes only")
    parsed_path, code_path = REPO / cell.replay["parsed_path"], REPO / cell.replay["code_path"]
    output = REPO / cell.replay["output_path"]
    if hash_file(output) != cell.replay["output_sha256"]:
        raise ValueError(f"recovered artifact hash mismatch: {cell.original.run_id}")
    if cell.replay["execution"]["sandbox_image"] != PINNED_IMAGE:
        raise ValueError(f"recovered artifact did not execute in the pinned image: {cell.original.run_id}")
    return StageArtifacts(stage=StageId.ANALYSIS, model_alias=cell.replay["model_alias"],
                          parsed_output=json.loads(parsed_path.read_text()), executed_code=code_path.read_text(),
                          files={"findings": str(output)}, verified_results={"findings": json.loads(output.read_text())},
                          validation_status="passed")


def build_continuation_handoff(cell: ContinuationCell, path: Path):
    if [(stage.value, alias) for _, stage, alias in cell.remaining] != [("reporting", cell.original.models[2])]:
        raise ValueError("frozen continuation-v1 inventory must contain reporting-only continuations")
    spec, _, _ = load_project(REPO / "datasets/projects" / cell.original.project_id)
    upstream = [original_cleaning_artifact(cell), recovered_analysis_artifact(cell)]
    return build_and_save(spec, cell.original.path_id, StageId.REPORTING, upstream, path)


def _existing_records() -> list[dict[str, Any]]:
    return read_jsonl(RECORDS)


def pending_cells(cells: list[ContinuationCell], existing: list[dict[str, Any]] | None = None) -> list[ContinuationCell]:
    completed = {row["continued_from"] for row in (existing if existing is not None else _existing_records())}
    return [cell for cell in cells if cell.original.run_id not in completed]


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _runtime(group: str, limits: UsageLimits):
    from src.bedrock.client import BedrockClient
    return BedrockClient(_registry(group), limits=limits, ledger_path=LEDGER,
                         log_path=INVOCATIONS, cache_dir=None)


def execute_cell(cell: ContinuationCell, client: Any) -> dict[str, Any]:
    run_id = continuation_run_id(cell)
    run_dir = RUNS / run_id
    if run_dir.exists():
        raise FileExistsError(f"continuation run directory already exists without a record: {run_dir}")
    run_dir.mkdir(parents=True)
    spec, ground_truth, pdir = load_project(REPO / "datasets/projects" / cell.original.project_id)
    handoff = build_continuation_handoff(cell, run_dir / "reporting/handoff_in.json")
    pkg, size, elapsed = handoff
    context = StageContext(client=client, executor=None, gate=None, spec=spec, project_dir=pdir,
                           ground_truth=ground_truth, experiment_id=EXPERIMENT_ID, run_id=run_id,
                           path_id=cell.original.path_id, repeat_index=cell.original.repeat_index,
                           use_cache=False, max_tokens=GROUPS[cell.group]["max_tokens"],
                           resource_limits=ResourceLimits(), reproducibility_rerun=True, protocol="v3")
    recovered = recovered_analysis_artifact(cell)
    result = run_reporting(context, cell.original.models[2], pkg,
                           (str(run_dir / "reporting/handoff_in.json"), size, elapsed),
                           run_dir / "reporting", recovered.files["findings"])
    record = {
        "contract_version": "continuation-1.0", "run_id": run_id, "experiment_id": EXPERIMENT_ID,
        "continued_from": cell.original.run_id, "group": cell.group,
        "project_id": cell.original.project_id, "path_id": cell.original.path_id,
        "repeat_index": cell.original.repeat_index, "recovered_stage": cell.replay["stage"],
        "recovered_output_sha256": cell.replay["output_sha256"],
        "recovered_stage_validation": cell.replay["frozen_validation"],
        "remaining_stages": [result.record.model_dump(mode="json")],
        "outcome": ("void_infra" if result.record.status == StageStatus.INFRA_ERROR else
                    "complete_for_corrected_view"),
        "corrected_view_only": True, "frozen_original_modified": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "continuation_record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def execute_approved(manifest: dict[str, Any]) -> dict[str, Any]:
    cells = eligible_cells()
    pending = pending_cells(cells)
    plan_budget = budget(cells)
    limits = UsageLimits(max_calls=int(plan_budget["static_worst_case"]["total"]["attempts"]),
                         max_input_tokens=int(plan_budget["static_worst_case"]["total"]["input_tokens"]),
                         max_output_tokens=int(plan_budget["static_worst_case"]["total"]["output_tokens"]),
                         max_budget_usd=manifest["hard_budget_cap_usd"])
    executed = []
    clients: dict[str, Any] = {}
    for cell in pending:
        clients.setdefault(cell.group, _runtime(cell.group, limits))
        record = execute_cell(cell, clients[cell.group])
        _append_jsonl(RECORDS, record)
        executed.append(record["run_id"])
    return {"status": "continuations_complete_pending_corrected_view_analysis",
            "eligible": len(cells), "already_complete": len(cells) - len(pending),
            "executed": executed, "records": str(RECORDS.relative_to(REPO)),
            "ledger": str(LEDGER.relative_to(REPO))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-approved-continuations", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute_approved_continuations:
        print(json.dumps(build_plan(), indent=2, sort_keys=True))
        print(f"PLAN ONLY: paid execution requires explicit approval, manifest, flag, and tag {TAG}.")
        return 0
    manifest = verify_frozen_approval()
    print(json.dumps(execute_approved(manifest), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
