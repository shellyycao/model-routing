"""Test-project specification (owned by Benchmark; consumed by Workflow and XAI).

A project lives at datasets/projects/<project_id>/project.json and validates against
ProjectSpec. Ground truth is computed by deterministic reference code, never by an
evaluated LLM.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field, model_validator


class ColumnSpec(BaseModel):
    name: str
    dtype: str                    # "int" | "float" | "str" | "date" | "category" | "bool"
    nullable: bool = False
    allowed_values: list[str] | None = None
    min_value: float | None = None
    max_value: float | None = None


class InputFile(BaseModel):
    """A file the MODEL's code may read (v1.2). Only files listed here are ever mounted."""

    name: str                     # filename inside INPUT_DIR
    path: str                     # relative to the project dir
    description: str = ""


class AnalysisQuestion(BaseModel):
    question_id: str              # e.g. "q1"
    question: str                 # model-visible; must not contain example answer values
    metric_keys: list[str]        # keys the analysis must write to findings.json
    abs_tolerance: float = 1e-6
    rel_tolerance: float = 1e-4
    # v1.2 metadata for structured report checks (validator-only; not rendered to models)
    direction_key: str | None = None             # metric whose sign defines increase/decrease
    ranking_labels: dict[str, str] | None = None  # metric_key -> group label, for ranking checks


class ReportingRequirement(BaseModel):
    required_finding_ids: list[str]   # question_ids whose results the report must cover
    max_words: int | None = None
    audience: str = "business stakeholders"


class ProjectSpec(BaseModel):
    project_id: str
    domain: str
    seed: int
    objective: str                        # original user objective (carried in every handoff)
    raw_data_file: str                    # relative to project dir (primary input)
    input_files: list[InputFile] = Field(default_factory=list)   # v1.2: ALL model-readable inputs; default = [raw_data_file]
    cleaning_requirements: list[str]      # natural-language rules given to the model
    cleaned_schema: list[ColumnSpec]      # schema the cleaned CSV must satisfy
    cleaned_data_filename: str = "cleaned.csv"
    analysis_questions: list[AnalysisQuestion]
    findings_filename: str = "findings.json"
    reporting: ReportingRequirement
    # Canonical artifacts for Experiment A (independent stage evaluation):
    canonical_cleaned_file: str           # reference-cleaned CSV
    canonical_findings_file: str          # reference findings.json (verified)
    ground_truth_file: str                # machine-readable expected outputs
    notes: str = Field(default="", description="Known data imperfections. HIDDEN: never rendered to models.")

    # v1.2: fields that may be rendered into model prompts. Everything else (notes, canonical/
    # ground-truth paths, tolerances metadata) is hidden from models.
    MODEL_VISIBLE_FIELDS: ClassVar[tuple[str, ...]] = (
        "project_id", "domain", "objective", "cleaning_requirements", "cleaned_schema",
        "cleaned_data_filename", "findings_filename", "reporting",
    )

    def model_input_files(self) -> list[InputFile]:
        if self.input_files:
            return self.input_files
        name = self.raw_data_file.rsplit("/", 1)[-1]
        return [InputFile(name=name, path=self.raw_data_file, description="raw data")]

    def model_view(self) -> dict:
        """The ONLY project information that may be shown to a model."""
        view = {k: getattr(self, k) for k in self.MODEL_VISIBLE_FIELDS}
        view = {k: (v.model_dump(mode="json") if hasattr(v, "model_dump") else
                    [x.model_dump(mode="json") if hasattr(x, "model_dump") else x for x in v] if isinstance(v, list) else v)
                for k, v in view.items()}
        view["analysis_questions"] = [{"question_id": q.question_id, "question": q.question,
                                       "metric_keys": q.metric_keys} for q in self.analysis_questions]
        view["input_files"] = [{"name": f.name, "description": f.description} for f in self.model_input_files()]
        return view

    @model_validator(mode="after")
    def _hidden_paths_not_inputs(self):
        hidden = {self.canonical_cleaned_file, self.canonical_findings_file, self.ground_truth_file}
        for f in self.model_input_files():
            if f.path in hidden or "canonical" in f.path or "ground_truth" in f.path:
                raise ValueError(f"input file {f.path!r} would expose canonical/ground-truth data to the model")
        return self
