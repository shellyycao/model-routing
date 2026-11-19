"""Structured outputs the MODELS must return, plus the stage handoff package.

Model outputs are parsed with src.bedrock.structured.parse_structured. Executed results
(cleaned CSV, findings.json) are produced by the sandbox, not trusted from model text.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .ids import StageId


class CleaningOutput(BaseModel):
    python_code: str = Field(description="Python script. Reads input from INPUT_DIR, writes the cleaned CSV and cleaning_summary.json to OUTPUT_DIR.")
    output_filename: str = Field(description="Filename of the cleaned CSV written to OUTPUT_DIR.")
    cleaning_logic: str = Field(description="Brief explanation of the cleaning steps.")


class AnalysisOutput(BaseModel):
    python_code: str = Field(description="Python script. Reads the cleaned CSV from INPUT_DIR, writes findings.json to OUTPUT_DIR.")
    expected_artifacts: list[str] = Field(description="Filenames the script writes to OUTPUT_DIR.")
    methods_description: str


class KeyFinding(BaseModel):
    finding_id: str = Field(description="The analysis question_id this finding addresses.")
    statement: str
    evidence_refs: list[str] = Field(description="metric_keys from findings.json supporting this statement.")
    reported_values: dict[str, float] = Field(default_factory=dict,
                                              description="metric_key -> number as stated in the report. "
                                                          "Required for EVERY metric_key of the finding.")
    # v1.2 structured claims, checked deterministically against verified findings.
    direction: Literal["increase", "decrease", "no_change", "not_applicable"] | None = Field(
        default=None, description="For change/trend findings: the direction you state in the text.")
    ranking: list[str] | None = Field(
        default=None, description="For group comparisons: group labels ordered from highest to lowest value.")
    derived_values: list["DerivedValue"] = Field(
        default_factory=list, description="Any number in the text computed from findings (share, difference, ...).")


class DerivedValue(BaseModel):
    """A number stated in the report that is computed from verified findings (v1.2)."""

    kind: Literal["difference", "ratio", "pct_change", "share"] = Field(
        description="difference = a-b; ratio = a/b; pct_change = (a-b)/b*100; share = a/b*100")
    operands: list[str] = Field(description="metric_keys [a, b] used in the formula, in order.")
    value: float = Field(description="The number as stated in the report.")


class ReportOutput(BaseModel):
    title: str
    executive_summary: str
    key_findings: list[KeyFinding]
    limitations: list[str]
    conclusion: str


class HandoffPackage(BaseModel):
    """Identical policy for same-model and cross-model transitions.

    Failed artifacts are passed as-is (with their validation status); they are never
    replaced by canonical ground truth during full-workflow evaluation.
    """

    project_id: str
    path_id: str
    original_objective: str
    current_stage: StageId
    completed_stages: list[StageId]
    stage_outputs: dict[str, dict]            # stage -> model structured output (as dict)
    source_files: list[str]                   # artifact paths visible to the next stage
    executed_code: dict[str, str]             # stage -> code that was executed
    verified_results: dict[str, dict]         # stage -> sandbox-produced results (e.g. findings)
    # v1.2: model-visible status ONLY. Never include validator details (they contain expected values).
    validation_status: dict[str, Literal["passed", "failed", "not_run", "blocked_by_invalid_artifact"]]
    known_limitations: list[str] = Field(default_factory=list)

    def size_bytes(self) -> int:
        return len(self.model_dump_json().encode())


KeyFinding.model_rebuild()
