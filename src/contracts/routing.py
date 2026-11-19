"""Routing objective, decision traces, and counterfactual records (owned by XAI).

Key separations enforced by these types:
- Predictions are made from TRAINING projects only. Every piece of evidence is a typed
  (project_id, run_id) reference that is validated against training_projects, and the
  held-out project may never appear (leave-one-project-out). The type check is a second line
  of defence: the loader must also physically exclude held-out records (XAI-owned).
- CounterfactualPrediction is frozen and carries a canonical content hash over an explicit,
  versioned field list. A record without a valid hash is rejected, so "reset the hash and
  re-validate" does not silently accept tampered content. Persist predictions in an
  append-only hash-chained log (chain_hash) committed BEFORE validation runs.
- Computational faithfulness (does the explanation match the router's recorded computation?)
  and empirical validity (did the predicted alternative outcome happen?) are separate records.

Quantity key convention (used in predicted/actual dicts):
  "<stage>.<metric>"  for stage quality, e.g. "analysis.numerical_accuracy"
  "feasible"          probability (predictions) / 0-1 outcome (actuals)
  "end_to_end_ms", "api_latency_ms", "cost_usd", "total_tokens", "n_switches" for efficiency

v1.1 (2026-11-17, review fixes M6, M7, M8, M10): typed evidence, canonical hashing,
richer counterfactual fields, selection steps and trace consistency validators.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .ids import parse_path_id
from .records import CONTRACT_VERSION


# ----------------------------------------------------------------------------- hashing
def canonical_json(data: Any) -> str:
    """Stable serialisation: sorted keys at every level, no whitespace, no NaN."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def chain_hash(prev_hash: str | None, content_hash: str) -> str:
    """Hash-chain link for append-only logs: H(prev || content)."""
    return sha256_hex(f"{prev_hash or 'GENESIS'}:{content_hash}")


def _norm_project(p: str) -> str:
    return p.strip().lower()


# ----------------------------------------------------------------------------- objective
class Strategy(str, Enum):
    S1_SINGLE_MODEL = "S1_single_model"
    S2_GREEDY_TASK_ONLY = "S2_greedy_task_only"          # ignores cross-stage interaction
    S3_WORKFLOW_AWARE = "S3_workflow_aware"              # path-level prediction incl. interaction terms
    S4_ORACLE = "S4_oracle"                              # retrospective reference ONLY


PROSPECTIVE = {Strategy.S1_SINGLE_MODEL, Strategy.S2_GREEDY_TASK_ONLY, Strategy.S3_WORKFLOW_AWARE}


class QualityConstraint(BaseModel):
    stage: str
    metric: str
    op: Literal[">=", "<="]
    threshold: float

    @property
    def key(self) -> str:
        return f"{self.stage}.{self.metric}"


PreferenceKey = Literal["cost_usd", "end_to_end_ms", "total_tokens", "n_switches"]


class RoutingObjective(BaseModel):
    """Predefined constraints + preference order. No weighted composite quality score."""

    objective_id: str
    min_feasibility_prob: float = 0.5
    quality_constraints: list[QualityConstraint] = Field(default_factory=list)
    # Lexicographic preference among feasible paths, e.g. ["cost_usd", "end_to_end_ms"].
    preference_order: list[PreferenceKey]
    tie_tolerance: float = 0.05          # relative difference treated as a tie
    description: str = ""


# ----------------------------------------------------------------------------- predictions
class EvidenceRef(BaseModel):
    project_id: str
    run_id: str
    experiment_id: str                   # e.g. "expA_stage" or "expB_paths"

    @field_validator("project_id")
    @classmethod
    def _norm(cls, v: str) -> str:
        return _norm_project(v)


class PathPrediction(BaseModel):
    path_id: str
    feasibility_prob: float | None
    quality: dict[str, float]                     # "<stage>.<metric>" -> predicted value
    end_to_end_ms: float | None
    cost_usd: float | None                        # None if pricing unavailable
    total_tokens: float | None
    n_switches: int
    interaction_terms: dict[str, float] = Field(default_factory=dict)   # S3 only; labelled, never "handoff cost"
    uncertainty: dict[str, tuple[float, float]] = Field(default_factory=dict)  # quantity -> (lo, hi) interval
    evidence: list[EvidenceRef] = Field(default_factory=list)
    satisfies_constraints: bool | None = None
    violated_constraints: list[str] = Field(default_factory=list)

    @field_validator("path_id")
    @classmethod
    def _valid_path(cls, v: str) -> str:
        parse_path_id(v)
        return v


class SelectionStep(BaseModel):
    """One step of the router's actual computation, recorded as it happened."""

    order: int
    rule: Literal["feasibility_threshold", "quality_constraint", "pareto_filter",
                  "lexicographic_preference", "tie_break", "no_feasible_path"]
    detail: str                                   # e.g. "analysis.numerical_accuracy >= 0.95"
    removed: dict[str, str] = Field(default_factory=dict)   # path_id -> reason
    remaining: list[str]
    inactive: bool = False                        # criterion skipped (e.g. cost_usd unavailable)
    inactive_reason: str | None = None


class DecisionTrace(BaseModel):
    contract_version: str = CONTRACT_VERSION
    trace_id: str
    created_at: str
    strategy: Strategy
    target_project: str                           # project the decision is about (all strategies)
    held_out_project: str | None                  # == target_project for prospective strategies
    training_projects: list[str]
    training_data_hash: str                       # sha256 over sorted (project_id, run_id) evidence
    objective: RoutingObjective
    candidates: list[PathPrediction]
    selection_steps: list[SelectionStep]
    feasible_path_ids: list[str]
    pareto_path_ids: list[str]
    selected_path_id: str | None                  # None => no feasible path
    no_feasible_path: bool
    inactive_criteria: list[str] = Field(default_factory=list)
    explanation_components: dict = Field(default_factory=dict)   # structured; text is rendered FROM this
    router_version: str
    config_hash: str

    @field_validator("target_project", "held_out_project")
    @classmethod
    def _norm_one(cls, v):
        return _norm_project(v) if v is not None else v

    @field_validator("training_projects")
    @classmethod
    def _norm_list(cls, v: list[str]) -> list[str]:
        return sorted({_norm_project(p) for p in v})

    @staticmethod
    def compute_training_data_hash(candidates: list[PathPrediction]) -> str:
        refs = sorted({(e.project_id, e.experiment_id, e.run_id) for c in candidates for e in c.evidence})
        return sha256_hex(canonical_json(refs))

    def trace_hash(self) -> str:
        return sha256_hex(canonical_json(self.model_dump(mode="json")))

    @model_validator(mode="after")
    def _checks(self):
        # Leave-one-project-out separation (prospective strategies).
        if self.strategy in PROSPECTIVE:
            if self.held_out_project is None:
                raise ValueError("Prospective strategies must declare a held-out project")
            if self.held_out_project != self.target_project:
                raise ValueError("held_out_project must equal target_project for prospective strategies")
        if self.held_out_project and self.held_out_project in self.training_projects:
            raise ValueError("Leakage: held-out project appears in training_projects")
        for c in self.candidates:
            for e in c.evidence:
                if self.strategy in PROSPECTIVE and e.project_id not in self.training_projects:
                    raise ValueError(f"Leakage: evidence {e.run_id} from project {e.project_id!r} "
                                     f"is not in training_projects")
        if self.training_data_hash != self.compute_training_data_hash(self.candidates):
            raise ValueError("training_data_hash does not match candidate evidence")
        # Set consistency.
        cand = {c.path_id for c in self.candidates}
        feas = set(self.feasible_path_ids)
        if not feas <= cand:
            raise ValueError("feasible_path_ids must be a subset of candidates")
        if not set(self.pareto_path_ids) <= feas:
            raise ValueError("pareto_path_ids must be a subset of feasible_path_ids")
        if self.no_feasible_path != (self.selected_path_id is None):
            raise ValueError("no_feasible_path must be True iff selected_path_id is None")
        if self.no_feasible_path != (len(feas) == 0):
            raise ValueError("no_feasible_path must be True iff feasible_path_ids is empty")
        if self.selected_path_id is not None and self.selected_path_id not in feas:
            raise ValueError("selected_path_id must be feasible")
        if [s.order for s in self.selection_steps] != list(range(len(self.selection_steps))):
            raise ValueError("selection_steps must be ordered 0..n-1")
        return self


# ----------------------------------------------------------------------------- counterfactuals
class CounterfactualPrediction(BaseModel):
    """Frozen, hashed prediction. Build with CounterfactualPrediction.create(...)."""

    model_config = ConfigDict(frozen=True)

    HASHED_FIELDS_V1: ClassVar[tuple[str, ...]] = (
        "hash_version", "prediction_id", "trace_id", "created_at", "strategy", "router_version",
        "config_hash", "objective_id", "held_out_project", "training_projects", "training_data_hash",
        "selected_path_id", "alternative_path_id", "predicted_selected", "predicted_alternative",
        "predicted_delta", "predicted_delta_interval",
    )

    contract_version: str = CONTRACT_VERSION
    hash_version: Literal[1] = 1
    prediction_id: str
    trace_id: str
    created_at: str
    strategy: Strategy
    router_version: str
    config_hash: str
    objective_id: str
    held_out_project: str
    training_projects: list[str]
    training_data_hash: str
    selected_path_id: str
    alternative_path_id: str
    predicted_selected: dict[str, float | None]         # absolute values, key convention above
    predicted_alternative: dict[str, float | None]
    predicted_delta: dict[str, float | None]            # alternative - selected
    predicted_delta_interval: dict[str, tuple[float, float] | None] = Field(default_factory=dict)
    content_hash: str

    @field_validator("held_out_project")
    @classmethod
    def _norm_one(cls, v: str) -> str:
        return _norm_project(v)

    @field_validator("training_projects")
    @classmethod
    def _norm_list(cls, v: list[str]) -> list[str]:
        return sorted({_norm_project(p) for p in v})

    @classmethod
    def _hash_of(cls, data: dict) -> str:
        return sha256_hex(canonical_json({k: data[k] for k in cls.HASHED_FIELDS_V1}))

    @classmethod
    def create(cls, **fields) -> "CounterfactualPrediction":
        # Validate/normalise first (hash check skipped), then hash the normalised JSON form.
        tmp = cls.model_validate({**fields, "content_hash": ""}, context={"skip_hash": True})
        h = cls._hash_of(tmp.model_dump(mode="json"))
        return cls.model_validate({**fields, "content_hash": h})

    def computed_hash(self) -> str:
        return self._hash_of(self.model_dump(mode="json"))

    @model_validator(mode="after")
    def _checks(self, info):
        if self.strategy not in PROSPECTIVE:
            raise ValueError("Counterfactual predictions must come from a prospective strategy (not the oracle)")
        if self.held_out_project in self.training_projects:
            raise ValueError("Leakage: held-out project appears in training_projects")
        parse_path_id(self.selected_path_id)
        parse_path_id(self.alternative_path_id)
        if info.context and info.context.get("skip_hash"):
            return self
        if self.content_hash != self.computed_hash():
            raise ValueError("CounterfactualPrediction content_hash mismatch (missing, modified, or not created via .create())")
        return self


class CounterfactualValidation(BaseModel):
    """Empirical validity: prediction vs. executed outcome. Written after; never edits the prediction."""

    prediction_id: str
    prediction_hash: str
    validated_at: str
    actual_selected: dict[str, float | None]            # mean over repeats where available
    actual_alternative: dict[str, float | None]
    actual_delta: dict[str, float | None]
    actual_delta_spread: dict[str, tuple[float, float] | None] = Field(default_factory=dict)  # min/max over repeats
    n_repeats: dict[str, int] = Field(default_factory=dict)   # {"selected": k, "alternative": k}
    abs_error: dict[str, float | None]
    direction_correct: dict[str, bool | None]
    interval_covers_actual: dict[str, bool | None] = Field(default_factory=dict)
    actual_outcome: dict[str, str]                       # {"selected": "feasible"|..., "alternative": ...}
    selected_run_ids: list[str]
    alternative_run_ids: list[str]
    notes: str = ""

    def check_against(self, prediction: CounterfactualPrediction) -> None:
        if prediction.prediction_id != self.prediction_id:
            raise ValueError("validation refers to a different prediction")
        if prediction.computed_hash() != self.prediction_hash or prediction.content_hash != self.prediction_hash:
            raise ValueError("prediction changed since it was validated (hash mismatch)")


class FaithfulnessCheck(BaseModel):
    """Computational faithfulness: does the explanation reflect the router's recorded computation?"""

    trace_id: str
    trace_hash: str
    explanation_hash: str
    checked_at: str
    explanation_kind: Literal["template", "llm_unconstrained", "llm_grounded"] = "template"
    checks: list[dict] = Field(default_factory=list)    # [{claim, source_field, consistent: bool, detail}]
    replay_matches_selection: bool | None = None         # re-running the router on trace inputs gives the same path
    claims_checked: int
    claims_consistent: int
    inconsistencies: list[str] = Field(default_factory=list)
