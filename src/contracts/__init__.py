"""Frozen shared contracts (see CONTRACT_VERSION; change log in docs/architecture.md). Owned by the Lead Architect.

Agents import from here but MUST NOT edit these files. Request changes through the lead;
any change bumps CONTRACT_VERSION and is recorded in docs/architecture.md.
"""

from .artifacts import AnalysisOutput, CleaningOutput, DerivedValue, HandoffPackage, KeyFinding, ReportOutput
from .execution import (
    CheckResult,
    ExecutionResult,
    ExecutionStatus,
    Executor,
    ResourceLimits,
    ValidationResult,
)
from .ids import STAGES, StageId, enumerate_paths, is_single_model, make_path_id, n_switches, parse_path_id
from .project import AnalysisQuestion, ColumnSpec, InputFile, ProjectSpec, ReportingRequirement
from .records import (
    CONTRACT_VERSION,
    QUALITY_METRICS,
    CostStatus,
    FailurePolicy,
    FailureType,
    Outcome,
    PropagationSummary,
    Feasibility,
    StageBenchmarkRecord,
    StageRunRecord,
    StageStatus,
    StageTimings,
    WorkflowEfficiency,
    WorkflowRunRecord,
)
from .routing import (
    CounterfactualPrediction,
    CounterfactualValidation,
    DecisionTrace,
    EvidenceRef,
    FaithfulnessCheck,
    SelectionStep,
    canonical_json,
    chain_hash,
    sha256_hex,
    PathPrediction,
    QualityConstraint,
    RoutingObjective,
    Strategy,
)
