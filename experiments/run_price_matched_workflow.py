"""Plan and, only after the matching freeze, run the price-matched workflow replication.

Default behavior is pure planning.  The compatibility pilot has its own approval manifest and tag;
the main run remains independently gated.  Paid flags refuse before constructing Docker or Bedrock
clients unless the exact stage-specific approval, tag, maxTokens, cap, and hashes all match.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.run_stage_benchmark import plan_stage_benchmark, run_stage_benchmark
from experiments.run_workflow_grid import execute_plan, plan_grid
from src.bedrock.models import InferenceSettings, ModelRegistry, ModelSpec, Pricing
from src.bedrock.provenance import hash_file, hash_tree
from src.bedrock.usage import UsageLimits
from src.contracts import STAGES, StageId, WorkflowRunRecord, enumerate_paths, parse_path_id
from src.evaluation.cleaning import load_project
from src.storage import STAGE_BENCHMARK, RunStore
from src.workflow.orchestrator import PROJECTS_DIR, WorkflowOrchestrator
from src.workflow.stages import GateDecision, SandboxGate, prompt_input_token_upper_bound

REPO = Path(__file__).resolve().parents[1]
BRIEF = REPO / "docs/PRICE_MATCHED_WORKFLOW_BRIEF.md"
PLAN_DOC = REPO / "docs/PRICE_MATCHED_WORKFLOW_PLAN.md"
VERIFICATION = REPO / "results/processed/independent_v2/price_matched_model_verification.json"
APPROVAL_MANIFEST = REPO / "results/processed/price_matched_workflow_protocol_manifest.json"
PILOT_TAG = "price-matched-workflow-pilot-v1"
MAIN_TAG_V1 = "price-matched-workflow-main-v1"
MAIN_TAG_V1_1 = "price-matched-workflow-main-v1.1"
PREVIOUS_MAIN_TAG = MAIN_TAG_V1_1
MAIN_TAG = "price-matched-workflow-main-v1.2"
SANDBOX_IMAGE_ID = "sha256:88988a15503bdb96538c3dd62244a79879d5c7848397db18b1267ccfd0a9727a"
SELECTED_MAX_TOKENS = 16384
HARD_CAP_USD = 100.0
MAX_TOKEN_OPTIONS = (4096, 16384)
RETRY_ATTEMPTS = 5
PROJECTS = ("customer_churn", "energy_consumption", "retail_sales", "support_operations")
PILOT_PROJECT = "retail_sales"
REPEAT_PATHS = ("A-A-A", "A-A-C", "A-C-A", "A-C-C", "B-B-B", "C-C-C")
MODEL_MAP = {"A": "sonnet_4_6", "B": "kimi_k3", "C": "glm_5"}
MODEL_LABELS = {"A": "Sonnet 4.6", "B": "Kimi K3", "C": "GLM 5"}
PILOT_EXPERIMENT = "expA_price_matched_workflow_pilot_v3"
STAGE_EXPERIMENT = "expA_price_matched_workflow_v3"
WORKFLOW_EXPERIMENT = "expB_price_matched_workflow_v3"
RAW_ROOT = REPO / "results/raw"
LEDGER = RAW_ROOT / "ledgers/price_matched_workflow.json"
INVOCATIONS = RAW_ROOT / "price_matched_workflow/invocations.jsonl"
EVENTS = RAW_ROOT / "price_matched_workflow/execution_events.jsonl"
PILOT_SUMMARY = RAW_ROOT / "price_matched_workflow/pilot_summary.json"
PILOT_RECORDS = RAW_ROOT / "stage_benchmark" / f"{PILOT_EXPERIMENT}.jsonl"
PILOT_META = RAW_ROOT / "stage_benchmark" / f"{PILOT_EXPERIMENT}.meta.json"
STAGE_RECORDS = RAW_ROOT / "stage_benchmark" / f"{STAGE_EXPERIMENT}.jsonl"
WORKFLOW_RECORDS = RAW_ROOT / "workflow_runs" / f"{WORKFLOW_EXPERIMENT}.jsonl"
PART_A_CHECKPOINT = RAW_ROOT / "price_matched_workflow/part_a_cost_checkpoint.json"
MAIN_GRID_CHECKPOINT = RAW_ROOT / "price_matched_workflow/main_grid_cost_checkpoint.json"
MAIN_SUMMARY = RAW_ROOT / "price_matched_workflow/main_summary.json"
DOCKER_RERUN_SUMMARY = RAW_ROOT / "price_matched_workflow/docker_void_rerun_summary.json"
ROUTING_OUT = REPO / "results/routing/price_matched_workflow_v3_primary"
APPROVED_DOCKER_VOID_CELLS = (
    ("energy_consumption", "C-C-A", 0),
    ("energy_consumption", "C-C-B", 0),
    ("energy_consumption", "C-C-C", 0),
    ("retail_sales", "A-A-A", 0),
    ("retail_sales", "A-A-B", 0),
)

# Realistic planning assumptions. Inputs start from observed Sonnet workflow means; tokenizer
# factors and output factors come from the completed price-matched independent run. All stages are
# assumed to execute. A 2% attempt allowance approximates the observed 13/810 retry rate.
SONNET_INPUT_MEAN = {"cleaning": 2011.5, "analysis": 2589.285714285714, "reporting": 3498.676470588235}
SONNET_OUTPUT_MEDIAN = {"cleaning": 3004.5, "analysis": 2024.5, "reporting": 1994.0}
INPUT_FACTOR = {"A": {"code": 1.0, "report": 1.0}, "B": {"code": 447 / 459, "report": 1846 / 2136}, "C": {"code": 368 / 459, "report": 1790 / 2136}}
OUTPUT_FACTOR = {"A": {"code": 1.0, "report": 1.0}, "B": {"code": 1726 / 322, "report": 7718 / 1449}, "C": {"code": 228 / 322, "report": 1112.5 / 1449}}
REALISTIC_ATTEMPT_FACTOR = 1.02


class PinnedImageSandboxGate(SandboxGate):
    """Keep shared gate semantics while this runner executes by the exact verified image ID.

    The verification record retains its human-facing tag as optional metadata. This runner never
    gives that tag to Docker: the proxy below delegates availability to the real ID-pinned executor
    and exists only so the shared gate can validate the unchanged metadata record.
    """

    def check(self, executor: Any) -> GateDecision:
        if getattr(executor, "image", None) != SANDBOX_IMAGE_ID:
            return GateDecision(False, f"executor is not pinned to required image ID {SANDBOX_IMAGE_ID}")
        try:
            tag = json.loads(self.verification_path.read_text(encoding="utf-8")).get("image")
        except (OSError, json.JSONDecodeError, AttributeError):
            return super().check(executor)

        class VerificationView:
            image = tag

            @staticmethod
            def availability():
                return executor.availability()

        return super().check(VerificationView())


@dataclass(frozen=True)
class DockerVoidRerunPlan:
    eligible: tuple[WorkflowRunRecord, ...]
    pending: tuple[WorkflowRunRecord, ...]
    completed_reruns: tuple[WorkflowRunRecord, ...]


def _verification_rows() -> dict[str, dict[str, Any]]:
    rows = json.loads(VERIFICATION.read_text())["models"]
    by_alias = {row["alias"]: row for row in rows}
    if set(MODEL_MAP.values()) - set(by_alias):
        raise ValueError("price-matched model verification is incomplete")
    return by_alias


def registry(max_tokens: int) -> ModelRegistry:
    if max_tokens not in MAX_TOKEN_OPTIONS:
        raise ValueError(f"max_tokens must be one of {MAX_TOKEN_OPTIONS}")
    verified = _verification_rows()
    models = {}
    for alias, source_alias in MODEL_MAP.items():
        row = verified[source_alias]
        if not (row["verified"] and row["invoke_access"]["access_eligible"]
                and row["invoke_access"]["compatibility_verified"]):
            raise ValueError(f"{source_alias} lacks verified price/access evidence")
        models[alias] = ModelSpec(
            alias=alias, name=MODEL_LABELS[alias], family=row["provider"],
            model_id=row["callable_model_id"], base_model_id=row["base_model_id"],
            pricing=Pricing(input_per_mtok=row["input_per_mtok"],
                            output_per_mtok=row["output_per_mtok"],
                            source="saved official AWS Price List snapshots; verified by price_matched_model_verification.json",
                            retrieved="2026-11-18"),
            inference=InferenceSettings(max_tokens=max_tokens,
                                        temperature=None if alias == "B" else 0.0),
        )
    return ModelRegistry(region="us-east-1", aws_profile="xai-bedrock", models=models)


def _entry(phase: str, project: str, stage: str, alias: str, *, path: str | None = None,
           repeat: int = 0) -> dict[str, Any]:
    return {"phase": phase, "project": project, "stage": stage, "model_alias": alias,
            "path_id": path, "repeat_index": repeat}


def call_inventory() -> list[dict[str, Any]]:
    rows = []
    for stage in STAGES:
        for alias in MODEL_MAP:
            rows.append(_entry("pilot", PILOT_PROJECT, stage.value, alias))
    for project in PROJECTS:
        for stage in STAGES:
            for alias in MODEL_MAP:
                rows.append(_entry("part_a", project, stage.value, alias))
    paths = enumerate_paths(list(MODEL_MAP), 3)
    for project in PROJECTS:
        for path in paths:
            for stage, alias in zip(STAGES, parse_path_id(path)):
                rows.append(_entry("part_b_main", project, stage.value, alias, path=path))
        for repeat in (1, 2):
            for path in REPEAT_PATHS:
                for stage, alias in zip(STAGES, parse_path_id(path)):
                    rows.append(_entry("part_b_repeats", project, stage.value, alias,
                                       path=path, repeat=repeat))
    return rows


def _input_bound(project: str, stage: str) -> int:
    spec, _, pdir = load_project(PROJECTS_DIR / project)
    return prompt_input_token_upper_bound(StageId(stage), spec, pdir, "v3")


def _cost(reg: ModelRegistry, alias: str, input_tokens: float, output_tokens: float) -> float:
    price = reg.get(alias).pricing
    return (input_tokens * price.input_per_mtok + output_tokens * price.output_per_mtok) / 1_000_000


def _budget(rows: list[dict[str, Any]], max_tokens: int) -> dict[str, Any]:
    reg = registry(max_tokens)
    worst_by_model: dict[str, dict[str, float]] = {}
    realistic_by_model: dict[str, dict[str, float]] = {}
    for alias in MODEL_MAP:
        subset = [row for row in rows if row["model_alias"] == alias]
        worst_in = sum(_input_bound(row["project"], row["stage"]) for row in subset) * RETRY_ATTEMPTS
        worst_out = len(subset) * max_tokens * RETRY_ATTEMPTS
        realistic_in = 0.0
        realistic_out = 0.0
        for row in subset:
            kind = "report" if row["stage"] == "reporting" else "code"
            realistic_in += SONNET_INPUT_MEAN[row["stage"]] * INPUT_FACTOR[alias][kind]
            realistic_out += min(max_tokens, SONNET_OUTPUT_MEDIAN[row["stage"]] * OUTPUT_FACTOR[alias][kind])
        realistic_in *= REALISTIC_ATTEMPT_FACTOR
        realistic_out *= REALISTIC_ATTEMPT_FACTOR
        worst_by_model[alias] = {"logical_calls": len(subset), "maximum_api_attempts": len(subset) * RETRY_ATTEMPTS,
                                 "input_tokens": worst_in, "output_tokens": worst_out,
                                 "cost_usd": _cost(reg, alias, worst_in, worst_out)}
        realistic_by_model[alias] = {"logical_calls": len(subset),
                                     "expected_api_attempts": len(subset) * REALISTIC_ATTEMPT_FACTOR,
                                     "input_tokens": realistic_in, "output_tokens": realistic_out,
                                     "cost_usd": _cost(reg, alias, realistic_in, realistic_out)}
    def total(d):
        return {"logical_calls": sum(v["logical_calls"] for v in d.values()),
                "api_attempts": sum(v.get("maximum_api_attempts", v.get("expected_api_attempts", 0)) for v in d.values()),
                "input_tokens": sum(v["input_tokens"] for v in d.values()),
                "output_tokens": sum(v["output_tokens"] for v in d.values()),
                "cost_usd": sum(v["cost_usd"] for v in d.values())}
    return {"maxTokens": max_tokens,
            "static_worst_case": {"assumption": "all stages run; five paid API attempts per logical call; every attempt reaches maxTokens",
                                  "by_model": worst_by_model, "total": total(worst_by_model)},
            "realistic_estimate": {"assumption": "all stages run; 1.02 attempts/call; original Sonnet workflow means/medians scaled by completed price-matched tokenizer/output ratios and capped at maxTokens",
                                   "by_model": realistic_by_model, "total": total(realistic_by_model)}}


def build_plan() -> dict[str, Any]:
    rows = call_inventory()
    pilot = [row for row in rows if row["phase"] == "pilot"]
    main = [row for row in rows if row["phase"] != "pilot"]
    counts = Counter(row["phase"] for row in rows)
    options = {}
    for max_tokens in MAX_TOKEN_OPTIONS:
        options[str(max_tokens)] = {"pilot": _budget(pilot, max_tokens),
                                    "main": _budget(main, max_tokens),
                                    "combined": _budget(rows, max_tokens)}
    return {
        "protocol": "price-matched-workflow-v1",
        "status": "main_approved_pending_freeze_tag",
        "user_decision": {
            "wording": "16384, $100 cap",
            "date": "2026-11-19",
            "selected_maxTokens": SELECTED_MAX_TOKENS,
            "hard_budget_cap_usd": HARD_CAP_USD,
            "pilot_approved": True,
            "main_approved": True,
            "pilot_requires_separate_explicit_approval": True,
            "main_requires_separate_explicit_approval": True,
        },
        "main_approval": {
            "wording": "Approve the main run (504 calls, about $43 expected, $100 cap)",
            "date": "2026-11-19",
            "logical_call_ceiling": 504,
            "realistic_estimate_usd_rounded": 43,
            "hard_budget_cap_usd": HARD_CAP_USD,
        },
        "fixed": {"projects": list(PROJECTS), "prompt_version": "v3",
                  "validators": {"primary": "v3", "secondary": "v3.1 post-hoc"},
                  "handoff_policy": "continue_with_actual_artifact", "mode": "fresh",
                  "repeat_paths": list(REPEAT_PATHS), "router_config": "configs/routing.yaml",
                  "cost_router_config": "configs/routing_cost_posthoc.yaml"},
        "models": [{"alias": alias, "source_alias": MODEL_MAP[alias], "label": MODEL_LABELS[alias],
                    "temperature": None if alias == "B" else 0.0,
                    "temperature_field": "omitted" if alias == "B" else "sent"}
                   for alias in MODEL_MAP],
        "call_counts": {**dict(sorted(counts.items())), "pilot": len(pilot), "main": len(main),
                        "combined": len(rows)},
        "compatibility_pilot": {"project": PILOT_PROJECT, "logical_calls": len(pilot),
                                "order": "stage-major then A/B/C", "quality_analysis_forbidden": True,
                                "main_training_eligible": False,
                                "outcome": {"executed": 9, "api_success": 9, "parsed": 9,
                                            "stopReason_end_turn": 9, "parameter_failures": 0,
                                            "ledger_spend_usd": 0.449949}},
        "budget_options": options,
        "selected_budget": options[str(SELECTED_MAX_TOKENS)],
        "execution_gate": {"default": "plan only", "pilot_tag": PILOT_TAG,
                           "main_tag": MAIN_TAG,
                           "approval_manifest": str(APPROVAL_MANIFEST.relative_to(REPO)
                                                    if APPROVAL_MANIFEST.is_relative_to(REPO)
                                                    else APPROVAL_MANIFEST),
                           "network_or_model_calls_during_cp7c_preparation": 0},
    }


def protocol_hashes() -> dict[str, Any]:
    files = [BRIEF, PLAN_DOC, Path(__file__), VERIFICATION,
             REPO / "configs/routing.yaml", REPO / "configs/routing_cost_posthoc.yaml",
             REPO / "configs/analysis_price_matched_workflow_v3.yaml",
             REPO / "sandbox/Dockerfile", REPO / "results/raw/sandbox_verification.json",
             REPO / "results/verification/sandbox_verification.json",
             REPO / "experiments/run_stage_benchmark.py", REPO / "experiments/run_workflow_grid.py",
             REPO / "experiments/build_price_matched_workflow_pilot_manifest.py",
             REPO / "experiments/build_price_matched_workflow_main_manifest.py",
             REPO / "experiments/evaluate_routing.py", REPO / "experiments/validate_counterfactuals.py",
             REPO / "experiments/rescore_reporting_v3_1.py",
             REPO / "src/workflow/orchestrator.py", REPO / "src/workflow/stages.py",
             REPO / "src/workflow/executor.py",
             REPO / "src/contracts/records.py", REPO / "src/analysis/reruns.py",
             REPO / "src/analysis/io.py", REPO / "src/analysis/pipeline.py",
             REPO / "src/evaluation/cleaning.py", REPO / "src/evaluation/analysis.py",
             REPO / "src/evaluation/reporting_v3.py", REPO / "src/evaluation/reporting_v3_1.py",
             REPO / "src/routing/strategies.py", REPO / "src/routing/router.py",
             REPO / "src/routing/estimation.py", REPO / "src/routing/cost_posthoc.py",
             PILOT_RECORDS, PILOT_META, PILOT_SUMMARY]
    return {"files": {str(path.relative_to(REPO)): hash_file(path) for path in files},
            "prompts_v3_tree": hash_tree(REPO / "prompts/v3"),
            "projects_tree": hash_tree(REPO / "datasets/projects"),
            "pricing_snapshots_tree": hash_tree(REPO / "results/raw/pricing")}


def _current_tags() -> set[str]:
    out = subprocess.run(["git", "tag", "--points-at", "HEAD"], cwd=REPO, check=True,
                         text=True, capture_output=True).stdout
    return set(out.split())


def verify_paid_approval(kind: str) -> dict[str, Any]:
    if kind not in ("pilot", "main"):
        raise ValueError(kind)
    if not APPROVAL_MANIFEST.exists():
        raise SystemExit("no paid-call approval manifest exists")
    manifest = json.loads(APPROVAL_MANIFEST.read_text())
    if not manifest.get(f"{kind}_approved"):
        raise SystemExit(f"{kind} has no explicit user approval")
    required_status = ("pilot_frozen_paid_execution_approved" if kind == "pilot"
                       else "main_frozen_paid_execution_approved")
    if manifest.get("status") != required_status:
        raise SystemExit(f"price-matched workflow {kind} protocol is not frozen and paid-approved")
    tag = PILOT_TAG if kind == "pilot" else MAIN_TAG
    if manifest.get(f"{kind}_required_tag") != tag or tag not in _current_tags():
        raise SystemExit(f"paid {kind} execution requires exact tag {tag} at HEAD")
    if manifest.get("selected_max_tokens") != SELECTED_MAX_TOKENS:
        raise SystemExit("approved maxTokens decision is missing or invalid")
    cap = manifest.get("hard_budget_cap_usd")
    if cap != HARD_CAP_USD:
        raise SystemExit("approved positive hard budget cap is missing")
    if manifest.get("hashes") != protocol_hashes():
        raise SystemExit("frozen protocol hashes do not match the working tree")
    return manifest


def _limits(plan: dict[str, Any], max_tokens: int, cap: float) -> UsageLimits:
    worst = plan["budget_options"][str(max_tokens)]["combined"]["static_worst_case"]["total"]
    return UsageLimits(max_calls=int(worst["api_attempts"]),
                       max_input_tokens=int(worst["input_tokens"]),
                       max_output_tokens=int(worst["output_tokens"]), max_budget_usd=cap)


def _append_event(event: dict[str, Any]) -> None:
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _ledger_state() -> dict[str, Any] | None:
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else None


def _read_task_records(path: Path) -> list[dict[str, Any]]:
    """Read one exact task-record JSONL; never scan the raw directory or invocation log."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _completed_task_run_ids() -> dict[str, set[str]]:
    """Resume evidence comes only from the two main task files, never ``*.jsonl`` globs."""
    return {
        "part_a": {row["run_id"] for row in _read_task_records(STAGE_RECORDS)},
        "part_b": {row["run_id"] for row in _read_task_records(WORKFLOW_RECORDS)},
    }


def _display_path(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def _task_record_progress() -> dict[str, Any]:
    completed = _completed_task_run_ids()
    workflow_rows = _read_task_records(WORKFLOW_RECORDS)
    original_workflow_rows = [row for row in workflow_rows if row.get("rerun_of") is None]
    rerun_rows = [row for row in workflow_rows if row.get("rerun_of") is not None]
    return {
        "part_a": {"path": _display_path(STAGE_RECORDS),
                   "completed_records": len(completed["part_a"]), "expected_records": 36,
                   "group_fields": ["project_id", "stage", "model_alias"]},
        "part_b": {"path": _display_path(WORKFLOW_RECORDS),
                   "completed_records": len(completed["part_b"]), "expected_original_records": 156,
                   "original_records": len(original_workflow_rows), "rerun_records": len(rerun_rows),
                   "main_grid_records": sum(row.get("repeat_index") == 0 for row in original_workflow_rows),
                   "repeat_records": sum(row.get("repeat_index") in (1, 2) for row in original_workflow_rows),
                   "group_fields": ["project_id", "path_id", "repeat_index"]},
    }


def _is_docker_sandbox_void(record: WorkflowRunRecord) -> bool:
    if record.rerun_of is not None or record.repeat_index != 0 or \
            record.feasibility.outcome != "void_infra":
        return False
    for stage in record.stages:
        detail = (stage.failure_detail or "").casefold()
        if stage.status.value == "infra_error" and "sandbox gate refused execution" in detail and \
                ("docker daemon check failed" in detail or "docker info" in detail):
            return True
    return False


def plan_docker_void_reruns(records: list[WorkflowRunRecord]) -> DockerVoidRerunPlan:
    by_id = {record.run_id: record for record in records}
    if len(by_id) != len(records):
        raise ValueError("duplicate workflow run_id in Docker-void rerun source")
    eligible = tuple(record for record in records if _is_docker_sandbox_void(record))
    eligible_ids = {record.run_id for record in eligible}
    reruns = [record for record in records if record.rerun_of is not None]
    counts = Counter(record.rerun_of for record in reruns)
    duplicate_refs = sorted(run_id for run_id, count in counts.items() if count > 1)
    if duplicate_refs:
        raise ValueError(f"Docker void already has multiple rerun records: {duplicate_refs}")
    unrelated = sorted(record.run_id for record in reruns if record.rerun_of not in eligible_ids)
    if unrelated:
        raise ValueError(f"rerun record does not reference an eligible Docker void: {unrelated}")
    completed = tuple(record for record in reruns if record.rerun_of in eligible_ids)
    completed_original_ids = {record.rerun_of for record in completed}
    pending = tuple(record for record in eligible if record.run_id not in completed_original_ids)
    return DockerVoidRerunPlan(eligible=eligible, pending=pending, completed_reruns=completed)


def workflow_record_prefix_sha256(count: int = 156) -> str:
    lines = WORKFLOW_RECORDS.read_bytes().splitlines(keepends=True)
    if len(lines) < count:
        raise ValueError(f"workflow record file has {len(lines)} lines; expected at least {count}")
    return hashlib.sha256(b"".join(lines[:count])).hexdigest()


def _parameter_failure(stage_record, invocation) -> bool:
    detail = " ".join(filter(None, [stage_record.failure_detail,
                                     json.dumps(invocation.error) if invocation and invocation.error else None])).casefold()
    markers = ("validationexception", "doesn't support", "does not support",
               "unsupported field", "temperature field", "maxtokens field")
    return stage_record.status.value == "infra_error" and any(marker in detail for marker in markers)


def _pilot_record(item: dict[str, Any], benchmark_record, client) -> dict[str, Any]:
    stage = benchmark_record.record
    invocations = [record for record in client.logger.read_all()
                   if record.context.run_id == benchmark_record.run_id
                   and record.context.stage_id == item["stage"]
                   and record.status != "parse_error"]
    invocation = invocations[-1] if invocations else None
    return {
        "run_id": benchmark_record.run_id,
        "project_id": item["project_id"],
        "stage": item["stage"],
        "model_alias": item["model"],
        "model_id": stage.model_id,
        "stage_status": stage.status.value,
        "call_status": invocation.status if invocation else None,
        "error": invocation.error if invocation else None,
        "parameter_failure": _parameter_failure(stage, invocation),
        "effective_parameters": invocation.inference_settings if invocation else None,
        "input_tokens": stage.input_tokens,
        "output_tokens": stage.output_tokens,
        "reasoning_chars": invocation.reasoning_chars if invocation else None,
        "stopReason": invocation.stop_reason if invocation else None,
        "parse_ok": stage.parse_ok,
        "structural_ok": stage.structural_ok,
        "latency_ms": invocation.latency_ms if invocation else None,
        "cost_usd": invocation.incurred_cost_usd if invocation else stage.cost_usd,
        "quality_inspected": False,
    }


def _runtime(max_tokens: int, cap: float):
    """Construct Docker and Bedrock only after approval; classify preflight as non-model evidence."""
    from src.bedrock.client import BedrockClient
    from src.workflow.executor import DockerExecutor
    executor = DockerExecutor(image=SANDBOX_IMAGE_ID)
    gate = PinnedImageSandboxGate()
    decision = gate.check(executor)
    if not decision.ok or decision.image_id is None:
        reason = (f"required immutable sandbox image {SANDBOX_IMAGE_ID} failed preflight; "
                  f"no short-name fallback is permitted: {decision.reason}")
        _append_event({"classification": "sandbox_unavailable", "void_infra": True,
                       "model_failure": False, "reason": reason, "model_calls_made": 0})
        raise SystemExit(f"sandbox_unavailable before any model call: {reason}")
    client = BedrockClient(registry(max_tokens), limits=_limits(build_plan(), max_tokens, cap),
                           ledger_path=LEDGER, log_path=INVOCATIONS, cache_dir=None)
    return executor, gate, decision.image_id, client


def execute_pilot(manifest: dict[str, Any]) -> dict[str, Any]:
    max_tokens, cap = manifest["selected_max_tokens"], manifest["hard_budget_cap_usd"]
    reg = registry(max_tokens)
    plan = plan_stage_benchmark([PILOT_PROJECT], registry=reg, max_tokens=max_tokens,
                                experiment_id=PILOT_EXPERIMENT, results_root=RAW_ROOT)
    executor, gate, image_id, client = _runtime(max_tokens, cap)
    stopped, executed, records = set(), [], []
    with executor.image_lease(image_id):
        store = RunStore(PILOT_EXPERIMENT, root=RAW_ROOT, kind=STAGE_BENCHMARK)
        for item in plan["planned"]:
            if item["model"] in stopped:
                records.append({"run_id": item["run_id"], "project_id": item["project_id"],
                                "stage": item["stage"], "model_alias": item["model"],
                                "stage_status": "skipped_after_parameter_failure",
                                "parameter_failure": None, "quality_inspected": False})
                continue
            record = run_stage_benchmark(client, executor, store, item["project_id"],
                                         StageId(item["stage"]), item["model"],
                                         item["repeat_index"], gate=gate, max_tokens=max_tokens)
            executed.append(record.run_id)
            pilot_record = _pilot_record(item, record, client)
            records.append(pilot_record)
            if pilot_record["parameter_failure"]:
                stopped.add(item["model"])
    summary = {"status": "pilot_complete_pending_review", "executed": executed,
               "planned_logical_calls": 9, "records": records,
               "stopped_models_after_parameter_failure": sorted(stopped),
               "automatic_parameter_changes": 0, "quality_analyzed": False,
               "ledger_state": _ledger_state()}
    _write_json(PILOT_SUMMARY, summary)
    return summary


def _main_grid_checkpoint(cap: float) -> dict[str, Any]:
    current = _ledger_state()
    part_a = json.loads(PART_A_CHECKPOINT.read_text())
    if current is None or part_a.get("ledger_state") is None:
        raise SystemExit("cannot compute main-grid checkpoint without ledger states")
    spent = float(current["spent_usd_priced"])
    before_grid = float(part_a["ledger_state"]["spent_usd_priced"])
    grid_actual = spent - before_grid
    if grid_actual < -1e-12:
        raise SystemExit("ledger spend moved backwards since the Part A checkpoint")
    inventory = call_inventory()
    grid_rows = [row for row in inventory if row["phase"] == "part_b_main"]
    repeat_rows = [row for row in inventory if row["phase"] == "part_b_repeats"]
    grid_realistic = _budget(grid_rows, SELECTED_MAX_TOKENS)["realistic_estimate"]["total"]["cost_usd"]
    repeat_realistic = _budget(repeat_rows, SELECTED_MAX_TOKENS)["realistic_estimate"]["total"]["cost_usd"]
    ratio = repeat_realistic / grid_realistic
    projected_repeats = grid_actual * ratio
    projected_total = spent + projected_repeats
    return {"status": "main_grid_complete_manual_resume_required",
            "hard_cap_usd": cap, "ledger_state": current,
            "pilot_and_part_a_spend_usd": before_grid,
            "main_grid_actual_usd": grid_actual,
            "repeat_projection_method": "main-grid actual spend multiplied by pre-frozen realistic repeat/main-grid cost ratio",
            "realistic_repeat_to_main_grid_cost_ratio": ratio,
            "projected_repeats_usd": projected_repeats,
            "projected_total_usd": projected_total,
            "projection_within_cap": projected_total <= cap,
            "repeats_started": False}


def execute_main(manifest: dict[str, Any], continue_after_part_a: bool,
                 continue_after_main_grid: bool) -> dict[str, Any]:
    max_tokens, cap = manifest["selected_max_tokens"], manifest["hard_budget_cap_usd"]
    if continue_after_main_grid and not continue_after_part_a:
        raise SystemExit("--continue-after-main-grid also requires --continue-after-part-a")
    checkpoint_at_start = None
    if continue_after_main_grid:
        if not MAIN_GRID_CHECKPOINT.exists():
            raise SystemExit("main-grid checkpoint must exist from a prior stopped invocation")
        checkpoint_at_start = json.loads(MAIN_GRID_CHECKPOINT.read_text())
        if checkpoint_at_start.get("status") != "main_grid_complete_manual_resume_required":
            raise SystemExit("main-grid checkpoint status is not resumable")
        if checkpoint_at_start.get("hard_cap_usd") != cap or \
                checkpoint_at_start.get("repeats_started") is not False:
            raise SystemExit("main-grid checkpoint cap or phase does not match the frozen protocol")
        if not checkpoint_at_start.get("projection_within_cap"):
            raise SystemExit("main-grid projection exceeds the hard cap; repeats remain blocked")
    reg = registry(max_tokens)
    stage_plan = plan_stage_benchmark(list(PROJECTS), registry=reg, max_tokens=max_tokens,
                                      experiment_id=STAGE_EXPERIMENT, results_root=RAW_ROOT)
    executor, gate, image_id, client = _runtime(max_tokens, cap)
    summary: dict[str, Any] = {"part_a_executed": [], "part_b": None,
                               "task_record_progress_at_start": _task_record_progress()}
    with executor.image_lease(image_id):
        stage_store = RunStore(STAGE_EXPERIMENT, root=RAW_ROOT, kind=STAGE_BENCHMARK)
        for item in stage_plan["planned"]:
            record = run_stage_benchmark(client, executor, stage_store, item["project_id"],
                                         StageId(item["stage"]), item["model"],
                                         item["repeat_index"], gate=gate, max_tokens=max_tokens)
            summary["part_a_executed"].append(record.run_id)
        checkpoint = {"status": "part_a_complete_manual_cost_check_required",
                      "completed_stage_records": len(stage_store.load_records()),
                      "expected_stage_records": 36,
                      "ledger_state": _ledger_state()}
        if not PART_A_CHECKPOINT.exists():
            _write_json(PART_A_CHECKPOINT, checkpoint)
        else:
            checkpoint = json.loads(PART_A_CHECKPOINT.read_text())
            if checkpoint.get("completed_stage_records") != 36:
                raise SystemExit("saved Part A checkpoint is incomplete or inconsistent")
        if not continue_after_part_a:
            summary["status"] = "part_a_complete_manual_cost_check_required"
            summary["task_record_progress"] = _task_record_progress()
            return summary
        store = RunStore(WORKFLOW_EXPERIMENT, root=RAW_ROOT)
        orch = WorkflowOrchestrator(client, executor, store, gate=gate, mode="fresh",
                                    max_tokens=max_tokens, protocol="v3")
        main = plan_grid(list(PROJECTS), 3, repeats=1, experiment_id=WORKFLOW_EXPERIMENT,
                         registry=reg, max_tokens=max_tokens, results_root=RAW_ROOT, protocol="v3")
        repeats = plan_grid(list(PROJECTS), 3, paths=list(REPEAT_PATHS), repeats=2, repeat_start=1,
                            experiment_id=WORKFLOW_EXPERIMENT, registry=reg, max_tokens=max_tokens,
                            results_root=RAW_ROOT, protocol="v3")
        summary["part_b"] = {"main": execute_plan(main, orch), "repeats": None}
        grid_checkpoint = _main_grid_checkpoint(cap)
        _write_json(MAIN_GRID_CHECKPOINT, grid_checkpoint)
        if not continue_after_main_grid:
            summary["status"] = "main_grid_complete_manual_resume_required"
            summary["main_grid_checkpoint"] = grid_checkpoint
            summary["task_record_progress"] = _task_record_progress()
            return summary
        # A resume invocation may only proceed if rerunning the completed plans made no spend change.
        if checkpoint_at_start["ledger_state"] != grid_checkpoint["ledger_state"]:
            raise SystemExit("ledger changed since the reviewed main-grid checkpoint; repeats blocked")
        summary["part_b"]["repeats"] = execute_plan(repeats, orch)
        summary["status"] = "paid_records_complete_offline_routing_pending"
        summary["ledger_state"] = _ledger_state()
        summary["task_record_progress"] = _task_record_progress()
        _write_json(MAIN_SUMMARY, summary)
    return summary


def execute_docker_void_reruns(manifest: dict[str, Any]) -> dict[str, Any]:
    """Append one outcome-blind rerun for each approved Docker void; never rewrite originals."""
    store = RunStore(WORKFLOW_EXPERIMENT, root=RAW_ROOT)
    records = store.load_records()
    plan = plan_docker_void_reruns(records)
    amendment = manifest.get("docker_void_rerun", {})
    approved_ids = set(amendment.get("approved_original_run_ids", []))
    eligible_ids = {record.run_id for record in plan.eligible}
    if eligible_ids != approved_ids:
        raise SystemExit("eligible Docker voids do not match the frozen rerun manifest")
    if workflow_record_prefix_sha256() != amendment.get("original_156_record_prefix_sha256"):
        raise SystemExit("the original 156 workflow records changed; Docker void rerun refused")
    cells = {(record.project_id, record.path_id, record.repeat_index) for record in plan.eligible}
    if cells != set(APPROVED_DOCKER_VOID_CELLS):
        raise SystemExit("eligible Docker void cells do not match the approved five-cell amendment")
    if not plan.pending:
        summary = {"status": "docker_void_reruns_already_complete", "executed": [],
                   "skipped_existing_reruns": [record.run_id for record in plan.completed_reruns],
                   "original_records_preserved": sorted(eligible_ids), "ledger_state": _ledger_state()}
        _write_json(DOCKER_RERUN_SUMMARY, summary)
        return summary

    max_tokens, cap = manifest["selected_max_tokens"], manifest["hard_budget_cap_usd"]
    executor, gate, image_id, client = _runtime(max_tokens, cap)
    orch = WorkflowOrchestrator(client, executor, store, gate=gate, mode="fresh",
                                max_tokens=max_tokens, protocol="v3")
    existing_ids = {record.run_id for record in records}
    expected_ids = {
        original.run_id: orch.run_id(original.project_id, original.path_id,
                                     original.repeat_index, infra_attempt=1)
        for original in plan.pending
    }
    collisions = sorted(run_id for run_id in expected_ids.values() if run_id in existing_ids)
    if collisions:
        raise SystemExit(f"rerun run_id exists without a matching rerun_of record: {collisions}")

    executed = []
    fixed_targets = list(plan.pending)
    with executor.image_lease(image_id):
        for original in fixed_targets:  # fixed before execution; outcomes never alter selection
            rerun = orch.run_path(original.project_id, original.path_id, WORKFLOW_EXPERIMENT,
                                  original.repeat_index, infra_attempt=1, rerun_of=original.run_id)
            executed.append({"run_id": rerun.run_id, "rerun_of": original.run_id,
                             "project_id": original.project_id, "path_id": original.path_id,
                             "repeat_index": original.repeat_index,
                             "outcome": rerun.feasibility.outcome})
    summary = {"status": "docker_void_reruns_complete_pending_analysis", "executed": executed,
               "skipped_existing_reruns": [record.run_id for record in plan.completed_reruns],
               "selection_was_outcome_blind": True, "original_records_preserved": sorted(eligible_ids),
               "ledger_state": _ledger_state()}
    _write_json(DOCKER_RERUN_SUMMARY, summary)
    return summary


def run_offline_routing() -> dict[str, Any]:
    """Create prospective traces first, then validate; load only the two new experiment files."""
    from experiments.evaluate_routing import run_predict
    from experiments.validate_counterfactuals import run_validate
    from src.analysis.reruns import resolve_workflow_reruns
    from src.routing.config import load_routing_config
    from src.routing.data import load_records, read_jsonl

    stage_path = RAW_ROOT / "stage_benchmark" / f"{STAGE_EXPERIMENT}.jsonl"
    workflow_path = RAW_ROOT / "workflow_runs" / f"{WORKFLOW_EXPERIMENT}.jsonl"
    if not stage_path.exists() or not workflow_path.exists():
        raise SystemExit("offline routing requires completed new Part A and Part B record files")
    workflow_raw = read_jsonl(workflow_path)
    rerun_plan = plan_docker_void_reruns(workflow_raw)
    if rerun_plan.pending:
        raise SystemExit(f"offline routing waits for {len(rerun_plan.pending)} approved Docker void rerun(s)")
    workflow_effective, rerun_audit = resolve_workflow_reruns(workflow_raw)
    store = load_records([*read_jsonl(stage_path), *workflow_effective])
    if len(store.stage_records) != 36 or len(store.workflow_runs) != 156:
        raise SystemExit(f"new-only record count mismatch: stage={len(store.stage_records)} "
                         f"workflow={len(store.workflow_runs)}")
    if {r.experiment_id for r in store.stage_records} != {STAGE_EXPERIMENT} or \
            {r.experiment_id for r in store.workflow_runs} != {WORKFLOW_EXPERIMENT}:
        raise SystemExit("routing input contains an experiment outside the new price-matched replication")
    cfg = load_routing_config(REPO / "configs/routing.yaml")
    manifest = run_predict(store, cfg, ROUTING_OUT)
    validation = run_validate(store, cfg, ROUTING_OUT)
    return {"phase": "offline_routing_complete", "new_stage_records": len(store.stage_records),
            "raw_workflow_records": len(workflow_raw), "rerun_resolution": rerun_audit,
            "new_workflow_records": len(store.workflow_runs), "predict": manifest,
            "validations": validation["n_validations"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--execute-approved-pilot", action="store_true")
    group.add_argument("--execute-approved-main", action="store_true")
    group.add_argument("--rerun-docker-voids", action="store_true")
    group.add_argument("--run-offline-routing", action="store_true")
    parser.add_argument("--continue-after-part-a", action="store_true")
    parser.add_argument("--continue-after-main-grid", action="store_true")
    args = parser.parse_args(argv)
    if args.rerun_docker_voids and (args.continue_after_part_a or args.continue_after_main_grid):
        parser.error("--rerun-docker-voids cannot be combined with main-run continuation flags")
    plan = build_plan()
    if args.run_offline_routing:
        print(json.dumps(run_offline_routing(), indent=2, sort_keys=True))
        return 0
    if not args.execute_approved_pilot and not args.execute_approved_main and not args.rerun_docker_voids:
        print(json.dumps(plan, indent=2, sort_keys=True))
        print("PLAN ONLY: main approved at maxTokens 16384 under the shared $100 cap; "
              f"paid execution still requires tag {MAIN_TAG}; no AWS/Docker client created.")
        return 0
    kind = "pilot" if args.execute_approved_pilot else "main"
    manifest = verify_paid_approval(kind)
    result = (execute_pilot(manifest) if kind == "pilot" else
              execute_docker_void_reruns(manifest) if args.rerun_docker_voids else
              execute_main(manifest, args.continue_after_part_a, args.continue_after_main_grid))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
