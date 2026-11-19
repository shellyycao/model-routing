"""Run records and the three-part evaluation framework.

The framework deliberately keeps three groups SEPARATE (no weighted composite score):
  A. Feasibility  - hard gate: mandatory stages executed, artifacts present, mandatory checks passed
  B. Quality      - per-stage quality metrics, each reported on its own
  C. Efficiency   - latency, tokens, verifiable cost, execution time, switches

Feasibility is computed from EVERY mandatory stage. A failed intermediate stage makes the
workflow infeasible even if a downstream artifact happens to look valid, and the failure
remains visible in `stages`. Runs voided by infrastructure problems are kept but marked
`void_infra` so they are not counted as model infeasibility.

v1.1 (2026-11-17, review fixes B3, M3, M9, M11): structural validation of runs; tri-state
outcome; artifact hashes; quality basis; failure policy; cache-hit visibility; prompt hash.

v1.2 (2026-11-18, benchmark-validity review B1; user-approved pre-experiment design change):
failure policy `continue_with_actual_artifact` so upstream errors can propagate downstream.
Under it, a downstream stage runs whenever the ACTUAL upstream artifact exists and passes the
minimum structural checks, even if the upstream stage failed semantic validation; the artifact
is never replaced by canonical data. If it cannot be consumed, the stage is
BLOCKED_BY_INVALID_ARTIFACT (attributed upstream, not to the downstream model). Strict
feasibility (all stages PASSED) is still the `outcome`; propagated outcomes are recorded
separately in `PropagationSummary`.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .execution import ExecutionResult, ValidationResult
from .ids import STAGES, StageId, parse_path_id

CONTRACT_VERSION = "1.2"

# Stage-quality metric names (group B). Values are in [0, 1] unless noted.
QUALITY_METRICS: dict[StageId, tuple[str, ...]] = {
    StageId.CLEANING: ("cleaning_correctness", "data_integrity", "schema_compliance"),
    StageId.ANALYSIS: ("numerical_accuracy", "calculation_coverage", "reproducibility"),
    StageId.REPORTING: ("numerical_consistency", "finding_coverage", "unsupported_claim_count"),  # count, not [0,1]
}

CostStatus = Literal["estimated", "partial", "unavailable", "not_incurred"]


class StageStatus(str, Enum):
    PASSED = "passed"                        # executed and all mandatory checks passed
    FAILED = "failed"                        # executed (or attempted) and failed a mandatory requirement
    NOT_RUN_UPSTREAM_FAILURE = "not_run_upstream_failure"   # terminated by failure policy
    INFRA_ERROR = "infra_error"              # sandbox/API infra problem: run is void, not a model failure
    BLOCKED_BY_INVALID_ARTIFACT = "blocked_by_invalid_artifact"  # upstream artifact missing/structurally unusable


class FailureType(str, Enum):
    API_ERROR = "api_error"
    PARSE_ERROR = "parse_error"
    TRUNCATED = "truncated"                  # model hit maxTokens
    EXECUTION_ERROR = "execution_error"
    TIMEOUT = "timeout"
    INVALID_OUTPUT = "invalid_output"
    VALIDATION_FAILED = "validation_failed"
    SECURITY_VIOLATION = "security_violation"
    INFRA = "infra"


class StageTimings(BaseModel):
    generation_ms: float | None = None       # model API wall clock (fresh calls only)
    execution_ms: float | None = None        # sandbox runtime
    validation_ms: float | None = None
    handoff_ms: float | None = None          # building/serialising the handoff package


class StageRunRecord(BaseModel):
    stage: StageId
    model_alias: str
    model_id: str
    prompt_version: str
    prompt_hash: str | None = None           # sha256 of the exact prompt template (Rule 5)
    invocation_ids: list[str]                # -> results/raw/invocations.jsonl
    cache_hit: bool = False                  # True if the model output was reused, not freshly generated
    shared_with_run_ids: list[str] = Field(default_factory=list)  # runs sharing this exact stage output (prefix reuse)
    status: StageStatus
    structural_ok: bool | None = None        # v1.2: output artifact meets minimum structural requirements for consumption
    failure_type: FailureType | None = None
    failure_detail: str | None = None
    parse_ok: bool | None = None
    execution: ExecutionResult | None = None
    validation: ValidationResult | None = None                       # basis: ground_truth
    conditional_validation: ValidationResult | None = None           # basis: conditional_reference (optional)
    input_artifacts: list[str] = Field(default_factory=list)
    output_artifacts: list[str] = Field(default_factory=list)
    input_artifact_hashes: dict[str, str] = Field(default_factory=dict)    # path -> sha256
    output_artifact_hashes: dict[str, str] = Field(default_factory=dict)   # path -> sha256
    handoff_in_path: str | None = None
    handoff_size_bytes: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None            # None = unavailable (never 0 by default)
    cost_status: CostStatus = "unavailable"
    timings: StageTimings = Field(default_factory=StageTimings)

    @model_validator(mode="after")
    def _consistency(self):
        if self.validation and self.validation.quality_basis != "ground_truth":
            raise ValueError("`validation` must use quality_basis='ground_truth'")
        if self.conditional_validation and self.conditional_validation.quality_basis != "conditional_reference":
            raise ValueError("`conditional_validation` must use quality_basis='conditional_reference'")
        if self.status == StageStatus.PASSED and self.failure_type is not None:
            raise ValueError("PASSED stage cannot have a failure_type")
        if self.status in (StageStatus.FAILED, StageStatus.INFRA_ERROR) and self.failure_type is None:
            raise ValueError(f"{self.status.value} stage must record a failure_type")
        if self.status == StageStatus.BLOCKED_BY_INVALID_ARTIFACT and not self.failure_detail:
            raise ValueError("blocked stage must state which upstream artifact was unusable (failure_detail)")
        if self.status in (StageStatus.BLOCKED_BY_INVALID_ARTIFACT, StageStatus.NOT_RUN_UPSTREAM_FAILURE) \
                and self.invocation_ids:
            raise ValueError("a stage that did not run cannot have model invocations")
        return self


Outcome = Literal["feasible", "infeasible", "void_infra"]


class Feasibility(BaseModel):
    outcome: Outcome
    stage_status: dict[str, StageStatus]
    first_failure_stage: StageId | None = None
    failure_type: FailureType | None = None

    @property
    def feasible(self) -> bool:
        return self.outcome == "feasible"


class WorkflowEfficiency(BaseModel):
    total_api_latency_ms: float | None = None     # fresh calls only
    total_execution_ms: float | None = None
    total_validation_ms: float | None = None
    total_handoff_ms: float | None = None
    end_to_end_ms: float | None = None            # wall clock; NOT equal to API latency
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = None                 # None if ANY call is unpriced
    cost_status: CostStatus = "unavailable"
    n_calls: int = 0
    n_cache_hits: int = 0                         # stages whose output was reused (efficiency not comparable)
    n_switches: int = 0
    handoff_bytes_total: int = 0


FailurePolicy = Literal["terminate_on_mandatory_failure", "continue_with_actual_artifact"]


class PropagationSummary(BaseModel):
    """v1.2: outcomes under error propagation. All keys are stage values; metrics use QUALITY_METRICS names.

    - downstream_executable: stage ran on the actual upstream artifact and produced a structurally valid output
    - upstream_error_severity: for stage i, the GROUND-TRUTH quality of stage i-1's artifact expressed as
      error (1 - metric) for [0,1] metrics; empty for the first stage
    - end_to_end_accuracy: ground-truth quality metrics of the LAST stage of the path
    - propagation_impact: conditional_quality - ground_truth quality per stage/metric, i.e. how much of the
      stage's gap to ground truth is explained by its inputs differing from canonical. This is a descriptive
      decomposition, NOT a causal model-switching cost; upstream data errors, formatting differences and
      stochasticity all contribute.
    """

    downstream_executable: dict[str, bool]
    upstream_error_severity: dict[str, dict[str, float]] = Field(default_factory=dict)
    end_to_end_accuracy: dict[str, float] = Field(default_factory=dict)
    propagation_impact: dict[str, dict[str, float]] = Field(default_factory=dict)
    blocked_stages: list[str] = Field(default_factory=list)


class WorkflowRunRecord(BaseModel):
    contract_version: str = CONTRACT_VERSION
    run_id: str
    experiment_id: str
    project_id: str
    path_id: str
    models: list[str]
    repeat_index: int = 0
    rerun_of: str | None = Field(default=None, exclude_if=lambda value: value is None)
    # additive: original void_infra run ID for an approved rerun; absent from legacy JSON when null
    config_hash: str                         # hash of models/prompts/dataset/config
    failure_policy: FailurePolicy = "terminate_on_mandatory_failure"
    started_at: str
    finished_at: str | None = None
    stages: list[StageRunRecord]
    feasibility: Feasibility                 # group A
    quality: dict[str, dict[str, float]] = Field(default_factory=dict)              # group B vs ground truth
    conditional_quality: dict[str, dict[str, float]] = Field(default_factory=dict)  # group B vs conditional reference
    efficiency: WorkflowEfficiency           # group C
    propagation: PropagationSummary | None = None        # required under continue_with_actual_artifact
    final_artifacts: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _structure_and_gate(self):
        if self.rerun_of == self.run_id:
            raise ValueError("rerun_of cannot reference the record itself")
        path_models = list(parse_path_id(self.path_id))
        if self.models != path_models:
            raise ValueError(f"models {self.models} do not match path_id {self.path_id}")
        n = len(path_models)
        # Every stage of the path must have a record (incl. not-run ones) — a missing record must not pass the gate.
        if len(self.stages) != n:
            raise ValueError(f"path {self.path_id} needs {n} stage records, got {len(self.stages)}")
        for i, s in enumerate(self.stages):
            if s.stage != STAGES[i]:
                raise ValueError(f"stage record {i} is {s.stage.value}, expected {STAGES[i].value}")
            if s.model_alias != path_models[i]:
                raise ValueError(f"stage {s.stage.value} ran model {s.model_alias}, path says {path_models[i]}")
        statuses = {s.stage.value: s.status for s in self.stages}
        if self.feasibility.stage_status != statuses:
            raise ValueError("feasibility.stage_status does not match stage records")

        first_bad = next((s for s in self.stages if s.status != StageStatus.PASSED), None)
        has_infra = any(s.status == StageStatus.INFRA_ERROR for s in self.stages)
        expected = "feasible" if first_bad is None else ("void_infra" if has_infra else "infeasible")
        if self.feasibility.outcome != expected:
            raise ValueError(f"feasibility.outcome={self.feasibility.outcome!r} but stage records imply {expected!r}")
        if first_bad is not None and self.feasibility.first_failure_stage != first_bad.stage:
            raise ValueError("first_failure_stage must be the first non-PASSED stage")
        NOT_RUN, BLOCKED = StageStatus.NOT_RUN_UPSTREAM_FAILURE, StageStatus.BLOCKED_BY_INVALID_ARTIFACT
        if self.failure_policy == "terminate_on_mandatory_failure":
            if any(s.status == BLOCKED for s in self.stages):
                raise ValueError("BLOCKED_BY_INVALID_ARTIFACT is only used under continue_with_actual_artifact")
            # Once a mandatory stage fails, later stages must not run.
            if first_bad is not None:
                idx = self.stages.index(first_bad)
                for s in self.stages[idx + 1:]:
                    if s.status != NOT_RUN:
                        raise ValueError("stages after a failure must be NOT_RUN_UPSTREAM_FAILURE under the terminate policy")
        else:  # continue_with_actual_artifact
            if self.propagation is None:
                raise ValueError("continue_with_actual_artifact runs must record a PropagationSummary")
            if any(s.status == NOT_RUN and not any(t.status == StageStatus.INFRA_ERROR for t in self.stages)
                   for s in self.stages):
                raise ValueError("under the continue policy a non-run stage is BLOCKED_BY_INVALID_ARTIFACT "
                                 "(NOT_RUN_UPSTREAM_FAILURE only after an infra error)")
            # Once a stage is blocked/not run, everything after it is too (no artifact to consume).
            stopped = False
            for s in self.stages:
                if stopped and s.status not in (BLOCKED, NOT_RUN):
                    raise ValueError("a stage cannot run after an upstream stage was blocked or not run")
                stopped = stopped or s.status in (BLOCKED, NOT_RUN, StageStatus.INFRA_ERROR)
            blocked = [s.stage.value for s in self.stages if s.status == BLOCKED]
            if sorted(self.propagation.blocked_stages) != sorted(blocked):
                raise ValueError("propagation.blocked_stages must list exactly the BLOCKED stages")
            if self.stages and self.stages[0].status == BLOCKED:
                raise ValueError("the first stage reads raw input and cannot be blocked by an upstream artifact")
        return self


class StageBenchmarkRecord(BaseModel):
    """Experiment A: one model on one stage with CANONICAL upstream inputs."""

    contract_version: str = CONTRACT_VERSION
    run_id: str
    experiment_id: str
    project_id: str
    stage: StageId
    model_alias: str
    repeat_index: int = 0
    canonical_inputs: list[str]
    canonical_input_hashes: dict[str, str] = Field(default_factory=dict)
    config_hash: str
    record: StageRunRecord

    @model_validator(mode="after")
    def _consistency(self):
        if self.record.stage != self.stage or self.record.model_alias != self.model_alias:
            raise ValueError("StageBenchmarkRecord stage/model must match its StageRunRecord")
        return self
