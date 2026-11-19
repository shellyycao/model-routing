"""Leakage-safe access to Experiment A / B records.

Two objects, deliberately separate:

* ``RecordStore`` holds EVERY loaded record. Prospective routing code never receives it.
  Its only outcome accessor, ``retrospective_outcomes(project)``, exists for counterfactual
  validation and the S4 oracle, which run AFTER predictions are logged.
* ``TrainingView`` is built for one held-out project. It is a new, frozen object holding
  only tuples of records from the other projects: the held-out project's records (Experiment
  A and B) are physically filtered out before any estimation, and the view keeps no reference
  back to the store. Estimators accept only a TrainingView.

Input format (what Workflow's saved records must look like): JSONL, one JSON object per line,
each either a ``WorkflowRunRecord`` (has ``path_id`` and ``stages``) or a
``StageBenchmarkRecord`` (has ``stage`` and ``record``), validated with the contract models.
A directory is scanned recursively for ``*.jsonl``. Blank lines are ignored.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Union

from src.contracts import CONTRACT_VERSION, EvidenceRef, StageBenchmarkRecord, WorkflowRunRecord

from .config import REPO_ROOT

Record = Union[StageBenchmarkRecord, WorkflowRunRecord]
SYNTHETIC_MARKER = "SYNTHETIC_FIXTURE"


def norm_project(p: str) -> str:
    """Same normalisation as the contracts (EvidenceRef / DecisionTrace)."""
    return p.strip().lower()


def parse_record(obj: dict | Record) -> Record:
    if isinstance(obj, (StageBenchmarkRecord, WorkflowRunRecord)):
        rec = obj
    elif isinstance(obj, dict) and "path_id" in obj and "stages" in obj:
        rec = WorkflowRunRecord.model_validate(obj)
    elif isinstance(obj, dict) and "stage" in obj and "record" in obj:
        rec = StageBenchmarkRecord.model_validate(obj)
    else:
        raise ValueError("record is neither a WorkflowRunRecord (path_id+stages) nor a "
                         "StageBenchmarkRecord (stage+record)")
    if rec.contract_version != CONTRACT_VERSION:
        raise ValueError(f"record {rec.run_id} has contract_version {rec.contract_version!r}, "
                         f"expected {CONTRACT_VERSION!r}")
    return rec


def read_jsonl(path: str | Path) -> list[Record]:
    out: list[Record] = []
    with open(path) as fh:
        for i, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                out.append(parse_record(json.loads(line)))
            except Exception as exc:  # noqa: BLE001 - re-raise with location
                raise ValueError(f"{path}:{i}: {exc}") from exc
    return out


def evidence_ref(rec: Record) -> EvidenceRef:
    return EvidenceRef(project_id=rec.project_id, run_id=rec.run_id, experiment_id=rec.experiment_id)


@dataclass(frozen=True)
class RecordStore:
    stage_records: tuple[StageBenchmarkRecord, ...]
    workflow_runs: tuple[WorkflowRunRecord, ...]

    def projects(self) -> list[str]:
        return sorted({norm_project(r.project_id) for r in (*self.stage_records, *self.workflow_runs)})

    @property
    def is_synthetic(self) -> bool:
        return any(SYNTHETIC_MARKER in r.run_id or SYNTHETIC_MARKER in r.experiment_id
                   for r in (*self.stage_records, *self.workflow_runs))

    def retrospective_outcomes(self, project: str) -> tuple[WorkflowRunRecord, ...]:
        """Experiment B runs of `project`. For validation and the S4 oracle ONLY (never prospective)."""
        p = norm_project(project)
        return tuple(r for r in self.workflow_runs if norm_project(r.project_id) == p)


def load_records(source: str | Path | Iterable[dict | Record]) -> RecordStore:
    """Load from a JSONL file, a directory of JSONL files, or an iterable of records/dicts."""
    if isinstance(source, (str, Path)):
        p = Path(source)
        files = sorted(p.rglob("*.jsonl")) if p.is_dir() else [p]
        recs: list[Record] = [r for f in files for r in read_jsonl(f)]
    else:
        recs = [parse_record(r) for r in source]
    seen: set[str] = set()
    for r in recs:
        if r.run_id in seen:
            raise ValueError(f"duplicate run_id {r.run_id}")
        seen.add(r.run_id)
    return RecordStore(
        stage_records=tuple(r for r in recs if isinstance(r, StageBenchmarkRecord)),
        workflow_runs=tuple(r for r in recs if isinstance(r, WorkflowRunRecord)),
    )


@dataclass(frozen=True)
class TrainingView:
    """Training data for one LOPO fold. Contains NO record of the held-out project."""

    held_out_project: str
    training_projects: tuple[str, ...]
    stage_records: tuple[StageBenchmarkRecord, ...]
    workflow_runs: tuple[WorkflowRunRecord, ...]

    def __post_init__(self):
        for r in (*self.stage_records, *self.workflow_runs):
            if norm_project(r.project_id) == self.held_out_project:
                raise ValueError(f"Leakage: record {r.run_id} of held-out project in TrainingView")

    def evidence_refs(self) -> list[EvidenceRef]:
        return [evidence_ref(r) for r in (*self.stage_records, *self.workflow_runs)]

    def model_aliases(self) -> list[str]:
        return sorted({r.model_alias for r in self.stage_records})


def build_training_view(store: RecordStore, held_out_project: str) -> TrainingView:
    ho = norm_project(held_out_project)
    if ho not in store.projects():
        raise ValueError(f"held-out project {ho!r} has no records")
    stage = tuple(r for r in store.stage_records if norm_project(r.project_id) != ho)
    runs = tuple(r for r in store.workflow_runs if norm_project(r.project_id) != ho)
    training = tuple(sorted({norm_project(r.project_id) for r in (*stage, *runs)}))
    if not training:
        raise ValueError("no training projects remain after excluding the held-out project")
    return TrainingView(held_out_project=ho, training_projects=training, stage_records=stage, workflow_runs=runs)


def ensure_output_allowed(out_dir: str | Path, store: RecordStore) -> None:
    """Synthetic fixture outputs must never be written to results/."""
    if not store.is_synthetic:
        return
    out = Path(out_dir).resolve()
    results = (REPO_ROOT / "results").resolve()
    if out == results or results in out.parents:
        raise ValueError(f"refusing to write SYNTHETIC_FIXTURE outputs under {results}")
