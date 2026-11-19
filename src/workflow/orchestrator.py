"""Workflow orchestrator (Experiment B): run one path cleaning -> analysis [-> reporting].

run_path(project_id, path_id, experiment_id, repeat_index) -> WorkflowRunRecord (contracts v1.2),
appended to the RunStore and mirrored to results/raw/runs/<run_id>/run_record.json.

Identical for every path: prompts (prompts/<PROMPT_VERSION>), inference settings (one
max_tokens, registry temperature), client RetryPolicy, ResourceLimits, handoff policy, failure
policy, validators. Paths differ ONLY in which model alias runs each stage.

Modes
-----
"fresh" (PRIMARY, experiment B): every model call is a fresh call (use_cache=False; the client
    neither reads nor writes the response cache; InvocationContext.repeat_index is set, so the client
    refuses any cache use). Every run has its own artifact directory runs/<run_id>/; no model output
    or generated artifact is shared between paths or repeats.
"shared_prefix" (OPTIONAL cost-saving mode): identical stage requests within one
    (experiment, project, repeat) may be served from the client's cache (namespace below), so paths
    with a common prefix reuse that prefix's model outputs. Code is still re-executed in each run's
    own directory. StageRunRecord.cache_hit marks reused outputs and shared_with_run_ids lists the
    other runs of the same grid with the same prefix. It MUST use a different experiment_id from the
    primary one (the store pins one mode per experiment_id), so results are never mixed.

Failure policies (pluggable, `failure_policy=`; contracts v1.2)
---------------------------------------------------------------
"continue_with_actual_artifact" (DEFAULT for Experiment B, user-approved 2026-11-18): after a stage
    FAILS, the next stage still runs on the ACTUAL upstream artifact if it is structurally consumable
    (StageRunRecord.structural_ok: cleaned CSV exists, parses, has every schema column / findings.json
    exists, parses as an object, has every required key). Canonical data is never substituted. If the
    artifact is not consumable, the next stage and all later stages are BLOCKED_BY_INVALID_ARTIFACT
    (failure_detail names the artifact; no model call). After an INFRA_ERROR, later stages are
    NOT_RUN_UPSTREAM_FAILURE (the run is void anyway). A PropagationSummary is recorded.
"terminate_on_mandatory_failure": after the first non-PASSED stage, later stages are
    NOT_RUN_UPSTREAM_FAILURE.

Outcome (strict, unchanged by the policy): feasible (every stage PASSED) / infeasible (a
model-attributable FAILED stage; blocked stages are attributed upstream) / void_infra (an INFRA_ERROR
stage). See src/workflow/stages.py for the failure classification.

Development mode: a 2-letter path ("A-B") runs cleaning -> analysis only; a 3-letter path runs all
three stages.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from src.bedrock.provenance import config_hash, hash_tree, make_run_id
from src.contracts import (
    QUALITY_METRICS,
    STAGES,
    Feasibility,
    PropagationSummary,
    ResourceLimits,
    StageId,
    StageRunRecord,
    StageStatus,
    WorkflowEfficiency,
    WorkflowRunRecord,
    enumerate_paths,
    n_switches,
    parse_path_id,
)
from src.evaluation.cleaning import load_project
from src.storage import RunStore

from .handoff import HANDOFF_POLICY_VERSION, StageArtifacts, build_and_save
from .stages import (
    PROMPT_VERSION,
    PROTOCOLS,
    SandboxGate,
    StageContext,
    StageResult,
    not_run_record,
    run_analysis,
    run_cleaning,
    run_reporting,
    template_hashes,
)

WORKFLOW_VERSION = "1.0"
PROJECTS_DIR = Path(__file__).resolve().parents[2] / "datasets" / "projects"
PRIMARY_EXPERIMENT_ID = "expB_paths"
SHARED_PREFIX_EXPERIMENT_ID = "expB_shared_prefix"
Mode = Literal["fresh", "shared_prefix"]
MODES = ("fresh", "shared_prefix")


# ------------------------------------------------------------------ failure policies
# Decision after a stage: ("continue", None) | ("not_run", None) | ("block", detail)
_ARTIFACT_OF = {StageId.CLEANING: "cleaned_csv", StageId.ANALYSIS: "findings"}


@dataclass(frozen=True)
class TerminateOnMandatoryFailure:
    name: str = "terminate_on_mandatory_failure"

    def after(self, result: StageResult) -> tuple[str, str | None]:
        return ("continue", None) if result.passed else ("not_run", None)


@dataclass(frozen=True)
class ContinueWithActualArtifact:
    name: str = "continue_with_actual_artifact"

    def after(self, result: StageResult) -> tuple[str, str | None]:
        rec = result.record
        if result.passed:
            return "continue", None
        if rec.status == StageStatus.INFRA_ERROR:
            return "not_run", None
        key = _ARTIFACT_OF.get(rec.stage)
        if (key and rec.structural_ok and result.artifacts is not None and key in result.artifacts.files
                and Path(result.artifacts.files[key]).is_file()):
            return "continue", None
        why = ("no structured output (parse failure)" if rec.parse_ok is False else
               "missing or not structurally consumable")
        if rec.validation is not None:
            from .stages import ANALYSIS_STRUCTURAL_CHECKS, CLEANING_STRUCTURAL_CHECKS
            names = CLEANING_STRUCTURAL_CHECKS if rec.stage == StageId.CLEANING else ANALYSIS_STRUCTURAL_CHECKS
            failed = [c.name for c in rec.validation.checks if c.name in names and not c.passed]
            if failed:
                why = "failed structural checks " + ", ".join(failed)
        return "block", f"upstream {rec.stage.value} artifact '{key}' unusable: {why}"


FAILURE_POLICIES: dict[str, Any] = {
    "terminate_on_mandatory_failure": TerminateOnMandatoryFailure(),
    "continue_with_actual_artifact": ContinueWithActualArtifact(),
}
DEFAULT_FAILURE_POLICY = "continue_with_actual_artifact"


def get_failure_policy(name: str):
    if name not in FAILURE_POLICIES:
        raise NotImplementedError(f"failure policy {name!r} is not implemented ({sorted(FAILURE_POLICIES)})")
    return FAILURE_POLICIES[name]


class RunAlreadyCompleted(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowOrchestrator:
    def __init__(self, client: Any, executor: Any, store: RunStore, *, gate: SandboxGate | None = None,
                 mode: Mode = "fresh", projects_dir: str | Path = PROJECTS_DIR, max_tokens: int | None = None,
                 resource_limits: ResourceLimits | None = None, failure_policy: str = DEFAULT_FAILURE_POLICY,
                 reproducibility_rerun: bool = True, aliases: list[str] | None = None,
                 protocol: str = "v2"):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        if mode == "shared_prefix" and store.experiment_id == PRIMARY_EXPERIMENT_ID:
            raise ValueError("shared-prefix mode must not use the primary experiment_id")
        if mode == "fresh" and store.experiment_id == SHARED_PREFIX_EXPERIMENT_ID:
            raise ValueError("fresh mode must not write into the shared-prefix experiment")
        if store.kind != "workflow_runs":
            raise ValueError("orchestrator needs a workflow_runs store")
        self.client = client
        self.executor = executor
        self.store = store            # mode is pinned on the first run_path (planning writes nothing)
        self.mode = mode
        self.gate = gate or SandboxGate()
        self.projects_dir = Path(projects_dir)
        self.max_tokens = max_tokens
        self.resource_limits = resource_limits or ResourceLimits()
        self.policy = get_failure_policy(failure_policy)
        self.reproducibility_rerun = reproducibility_rerun
        if protocol not in PROTOCOLS:
            raise ValueError(f"unknown protocol {protocol!r}")
        # v3 (prospective primary) and v2 (frozen pilot) results must never share an experiment_id.
        if (protocol == "v3") != store.experiment_id.endswith("_v3"):
            raise ValueError(f"protocol {protocol!r} cannot write into experiment {store.experiment_id!r} "
                             "(v3 experiment ids must end with '_v3'; v2 ids must not)")
        self.protocol = protocol
        self.prompt_version = PROTOCOLS[protocol]["prompt_version"]
        self.aliases = sorted(aliases or client.registry.aliases)
        self._dataset_hash: dict[str, str] = {}

    # ------------------------------------------------------------------ identity
    def dataset_hash(self, project_id: str) -> str:
        if project_id not in self._dataset_hash:
            self._dataset_hash[project_id] = hash_tree(self.projects_dir / project_id)
        return self._dataset_hash[project_id]

    def _settings(self, n_stages: int) -> dict:
        """Everything (besides models/prompt version/dataset) that defines the configuration."""
        return {
            "workflow_version": WORKFLOW_VERSION,
            "prompt_templates": template_hashes(self.prompt_version),
            "handoff_policy": HANDOFF_POLICY_VERSION,
            "failure_policy": self.policy.name,
            "mode": self.mode,
            "n_stages": n_stages,
            "max_tokens": self.max_tokens,
            "resource_limits": self.resource_limits.model_dump(mode="json"),
            "reproducibility_rerun": self.reproducibility_rerun,
        } | ({} if self.protocol == "v2" else {   # v2 keys unchanged so frozen-v2 run_ids stay stable
            "protocol": self.protocol,
            "reporting_validator": PROTOCOLS[self.protocol]["reporting_validator"],
        })

    def config_hash(self, project_id: str, n_stages: int) -> str:
        return config_hash(self.client.registry, self.prompt_version, self.dataset_hash(project_id),
                           extra=self._settings(n_stages))

    def run_id(self, project_id: str, path_id: str, repeat_index: int = 0, infra_attempt: int = 0) -> str:
        n = len(parse_path_id(path_id))
        extra = {"settings": self._settings(n), "project_id": project_id, "path_id": path_id,
                 "repeat_index": repeat_index}
        if infra_attempt:
            extra["infra_attempt"] = infra_attempt
        return make_run_id(self.store.experiment_id, self.client.registry, self.prompt_version,
                           self.dataset_hash(project_id), extra=extra)

    def _shared_peers(self, project_id: str, path_id: str, repeat_index: int, stage_idx: int,
                      infra_attempt: int) -> list[str]:
        models = parse_path_id(path_id)
        prefix = models[: stage_idx + 1]
        peers = [p for p in enumerate_paths(self.aliases, len(models))
                 if parse_path_id(p)[: stage_idx + 1] == prefix and p != path_id]
        return [self.run_id(project_id, p, repeat_index, infra_attempt) for p in peers]

    # ------------------------------------------------------------------ main
    def run_path(self, project_id: str, path_id: str, experiment_id: str | None = None, repeat_index: int = 0,
                 *, infra_attempt: int = 0, rerun_of: str | None = None,
                 on_stage: Callable[[StageRunRecord], None] | None = None
                 ) -> WorkflowRunRecord:
        experiment_id = experiment_id or self.store.experiment_id
        if experiment_id != self.store.experiment_id:
            raise ValueError(f"experiment_id {experiment_id!r} != store experiment {self.store.experiment_id!r}")
        models = list(parse_path_id(path_id))
        if len(models) not in (2, 3):
            raise ValueError("paths must have 2 (development: cleaning->analysis) or 3 stages")
        unknown = set(models) - set(self.aliases)
        if unknown:
            raise ValueError(f"unknown model aliases {sorted(unknown)}")
        self.store._pin_mode(self.mode)
        run_id = self.run_id(project_id, path_id, repeat_index, infra_attempt)
        if self.store.is_completed(run_id):
            raise RunAlreadyCompleted(f"{run_id} already has a record; completed runs are never re-run")
        run_dir = self.store.prepare_run_dir(run_id)
        spec, gt, pdir = load_project(self.projects_dir / project_id)
        started = _now()
        t0 = time.perf_counter()

        ctx = StageContext(
            client=self.client, executor=self.executor, gate=self.gate, spec=spec, project_dir=pdir,
            ground_truth=gt, experiment_id=experiment_id, run_id=run_id, path_id=path_id,
            repeat_index=repeat_index,
            use_cache=self.mode == "shared_prefix",
            cache_namespace=(f"{experiment_id}|{project_id}|r{repeat_index}|a{infra_attempt}|"
                             f"{self.config_hash(project_id, len(models))[:16]}"
                             if self.mode == "shared_prefix" else None),
            max_tokens=self.max_tokens, resource_limits=self.resource_limits,
            reproducibility_rerun=self.reproducibility_rerun,
            protocol=self.protocol,
        )

        records: list[StageRunRecord] = []
        upstream: list[StageArtifacts] = []
        stopped: tuple[str, str | None] | None = None      # ("not_run", None) | ("block", detail)
        for i, alias in enumerate(models):
            stage = STAGES[i]
            if stopped is not None:
                if stopped[0] == "block":
                    records.append(StageRunRecord(
                        stage=stage, model_alias=alias, model_id=ctx.model_id(alias), prompt_version=self.prompt_version,
                        invocation_ids=[], status=StageStatus.BLOCKED_BY_INVALID_ARTIFACT, failure_detail=stopped[1],
                        cost_usd=None, cost_status="not_incurred"))
                else:
                    records.append(not_run_record(stage, alias, ctx.model_id(alias), self.prompt_version))
                continue
            sdir = run_dir / stage.value
            pkg, size, hms = build_and_save(spec, path_id, stage, upstream, sdir / "handoff_in.json")
            info = (str(sdir / "handoff_in.json"), size, hms)
            if stage == StageId.CLEANING:
                res = run_cleaning(ctx, alias, pkg, info, sdir)
            elif stage == StageId.ANALYSIS:
                res = run_analysis(ctx, alias, pkg, info, sdir, upstream[-1].files.get("cleaned_csv", ""))
            else:
                res = run_reporting(ctx, alias, pkg, info, sdir, upstream[-1].files.get("findings", ""))
            rec = res.record
            if self.mode == "shared_prefix":
                rec = rec.model_copy(update={"shared_with_run_ids": self._shared_peers(
                    project_id, path_id, repeat_index, i, infra_attempt)})
            (sdir / "stage_record.json").write_text(rec.model_dump_json(indent=2), encoding="utf-8")
            records.append(rec)
            if on_stage:
                on_stage(rec)
            if res.artifacts is not None:
                upstream.append(res.artifacts)
            action, detail = self.policy.after(res)
            if action != "continue":
                stopped = (action, detail)

        record = WorkflowRunRecord(
            run_id=run_id, experiment_id=experiment_id, project_id=project_id, path_id=path_id, models=models,
            repeat_index=repeat_index, rerun_of=rerun_of,
            config_hash=self.config_hash(project_id, len(models)),
            failure_policy=self.policy.name, started_at=started, finished_at=_now(), stages=records,
            feasibility=feasibility_of(records),
            quality={r.stage.value: dict(r.validation.quality) for r in records if r.validation},
            conditional_quality={r.stage.value: dict(r.conditional_validation.quality)
                                 for r in records if r.conditional_validation},
            efficiency=efficiency_of(records, path_id, (time.perf_counter() - t0) * 1000),
            propagation=(propagation_of(records) if self.policy.name == "continue_with_actual_artifact" else None),
            final_artifacts=_final_artifacts(records),
        )
        self.store.append(record)
        return record


# ------------------------------------------------------------------ aggregation
def feasibility_of(records: list[StageRunRecord]) -> Feasibility:
    first_bad = next((r for r in records if r.status != StageStatus.PASSED), None)
    has_infra = any(r.status == StageStatus.INFRA_ERROR for r in records)
    outcome = "feasible" if first_bad is None else ("void_infra" if has_infra else "infeasible")
    return Feasibility(outcome=outcome, stage_status={r.stage.value: r.status for r in records},
                       first_failure_stage=first_bad.stage if first_bad else None,
                       failure_type=first_bad.failure_type if first_bad else None)


_UNIT_METRICS = {s.value: set(m) - {"unsupported_claim_count"} for s, m in QUALITY_METRICS.items()}


def propagation_of(records: list[StageRunRecord]) -> PropagationSummary:
    """PropagationSummary (contracts v1.2) from the stage records alone (descriptive, not causal)."""
    ran = [r for r in records if r.status not in (StageStatus.BLOCKED_BY_INVALID_ARTIFACT,
                                                  StageStatus.NOT_RUN_UPSTREAM_FAILURE)]
    executable = {r.stage.value: (r in ran and r.status != StageStatus.INFRA_ERROR and r.structural_ok is True)
                  for r in records}
    severity: dict[str, dict[str, float]] = {}
    for prev, cur in zip(records, records[1:]):
        if cur in ran and prev.validation is not None:
            unit = _UNIT_METRICS[prev.stage.value]
            severity[cur.stage.value] = {m: 1.0 - v for m, v in prev.validation.quality.items() if m in unit}
    last = records[-1]
    e2e = dict(last.validation.quality) if last.validation is not None else {}
    impact: dict[str, dict[str, float]] = {}
    for r in records:
        if r.validation is not None and r.conditional_validation is not None:
            gt, cq = r.validation.quality, r.conditional_validation.quality
            impact[r.stage.value] = {m: cq[m] - gt[m] for m in sorted(set(gt) & set(cq))}
    return PropagationSummary(
        downstream_executable=executable, upstream_error_severity=severity, end_to_end_accuracy=e2e,
        propagation_impact=impact,
        blocked_stages=[r.stage.value for r in records if r.status == StageStatus.BLOCKED_BY_INVALID_ARTIFACT])


def _sum(values: list[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return sum(vals) if vals else None


def efficiency_of(records: list[StageRunRecord], path_id: str, end_to_end_ms: float) -> WorkflowEfficiency:
    called = [r for r in records if r.invocation_ids]
    fresh = [r for r in called if not r.cache_hit]
    incurred = [r for r in called if r.cost_status != "not_incurred"]
    if not incurred:
        cost, status = (0.0, "not_incurred") if called else (None, "not_incurred")
    elif all(r.cost_usd is not None and r.cost_status == "estimated" for r in incurred):
        cost, status = sum(r.cost_usd for r in incurred), "estimated"
    elif any(r.cost_usd is not None for r in incurred):
        cost, status = None, "partial"          # never a partial sum presented as the total
    else:
        cost, status = None, "unavailable"
    return WorkflowEfficiency(
        total_api_latency_ms=_sum([r.timings.generation_ms for r in fresh]),
        total_execution_ms=_sum([r.timings.execution_ms for r in records]),
        total_validation_ms=_sum([r.timings.validation_ms for r in records]),
        total_handoff_ms=_sum([r.timings.handoff_ms for r in records]),
        end_to_end_ms=end_to_end_ms,
        input_tokens=sum(r.input_tokens or 0 for r in fresh),
        output_tokens=sum(r.output_tokens or 0 for r in fresh),
        cost_usd=cost, cost_status=status,
        n_calls=len(fresh),
        n_cache_hits=sum(1 for r in called if r.cache_hit),
        n_switches=n_switches(path_id),
        handoff_bytes_total=sum(r.handoff_size_bytes or 0 for r in records),
    )


def _final_artifacts(records: list[StageRunRecord]) -> list[str]:
    last = records[-1]
    return list(last.output_artifacts) if last.status == StageStatus.PASSED else []
