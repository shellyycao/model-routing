"""Append-only storage of run records, one JSONL file per (record kind, experiment_id).

Layout under `root` (default results/raw/):
    workflow_runs/<experiment_id>.jsonl          one WorkflowRunRecord per line (Experiment B)
    workflow_runs/<experiment_id>.meta.json      experiment mode ("fresh" | "shared_prefix"), fixed at creation
    stage_benchmark/<experiment_id>.jsonl        one StageBenchmarkRecord per line (Experiment A)
    stage_benchmark/<experiment_id>.meta.json
    runs/<run_id>/                               every artifact of one run (prompts, responses, code,
                                                 sandbox outputs, handoff packages, validations,
                                                 run_record.json)

Rules
- Append-only: records are never edited or deleted. A run_id can be appended at most once
  (DuplicateRunError), so a completed run is never silently repeated. Failed and void_infra runs
  are complete records and are kept.
- One experiment_id = one mode. The meta file pins the mode; appending from a different mode raises
  ExperimentModeError, so shared-prefix results can never be mixed into the primary
  (fresh-call) experiment's file.
- A run directory that exists without a record is an interrupted run: before re-running, it is
  moved aside to runs/<run_id>.incomplete-<UTC timestamp> (kept, not deleted).
- Writes take a thread lock plus an fcntl lock on a sibling .lock file (multi-process safe on POSIX).
"""

from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from src.bedrock.models import REPO_ROOT
from src.contracts import StageBenchmarkRecord, WorkflowRunRecord

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

WORKFLOW = "workflow_runs"
STAGE_BENCHMARK = "stage_benchmark"
_MODELS = {WORKFLOW: WorkflowRunRecord, STAGE_BENCHMARK: StageBenchmarkRecord}
DEFAULT_ROOT = REPO_ROOT / "results" / "raw"


class DuplicateRunError(RuntimeError):
    pass


class ExperimentModeError(RuntimeError):
    pass


class RunStore:
    def __init__(self, experiment_id: str, *, root: str | Path = DEFAULT_ROOT, kind: str = WORKFLOW,
                 mode: str | None = None):
        if kind not in _MODELS:
            raise ValueError(f"kind must be one of {sorted(_MODELS)}")
        if not experiment_id or any(c in experiment_id for c in "/\\ "):
            raise ValueError("experiment_id must be non-empty without slashes/spaces")
        self.experiment_id = experiment_id
        self.kind = kind
        self.root = Path(root)
        self.records_path = self.root / kind / f"{experiment_id}.jsonl"
        self.meta_path = self.root / kind / f"{experiment_id}.meta.json"
        self.runs_dir = self.root / "runs"
        self._lock = threading.Lock()
        self.mode = mode
        if mode is not None:
            self._pin_mode(mode)

    # ---------------------------------------------------------------- mode
    def _pin_mode(self, mode: str) -> None:
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        with self._locked():
            if self.meta_path.exists():
                meta = json.loads(self.meta_path.read_text())
                if meta.get("mode") != mode:
                    raise ExperimentModeError(
                        f"experiment {self.experiment_id!r} was created in mode {meta.get('mode')!r}; "
                        f"refusing to write mode {mode!r} results into it")
            else:
                self.meta_path.write_text(json.dumps({"experiment_id": self.experiment_id, "kind": self.kind,
                                                      "mode": mode, "created_at": _now()}, indent=2))

    # ---------------------------------------------------------------- locking
    @contextmanager
    def _locked(self) -> Iterator[None]:
        lock_path = self.records_path.with_name(self.records_path.name + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, open(lock_path, "a") as fh:
            if fcntl:
                fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl:
                    fcntl.flock(fh, fcntl.LOCK_UN)

    # ---------------------------------------------------------------- read
    def _lines(self) -> list[str]:
        if not self.records_path.exists():
            return []
        return [l for l in self.records_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def load_records(self) -> list:
        model = _MODELS[self.kind]
        return [model.model_validate_json(l) for l in self._lines()]

    def completed_run_ids(self) -> set[str]:
        return {json.loads(l)["run_id"] for l in self._lines()}

    def is_completed(self, run_id: str) -> bool:
        return run_id in self.completed_run_ids()

    # ---------------------------------------------------------------- write
    def append(self, record) -> None:
        model = _MODELS[self.kind]
        if not isinstance(record, model):
            raise TypeError(f"{self.kind} store accepts {model.__name__} only")
        if record.experiment_id != self.experiment_id:
            raise ValueError(f"record experiment_id {record.experiment_id!r} != store {self.experiment_id!r}")
        line = record.model_dump_json()
        self.records_path.parent.mkdir(parents=True, exist_ok=True)
        with self._locked():
            if record.run_id in self.completed_run_ids():
                raise DuplicateRunError(f"run {record.run_id} already recorded; records are append-only")
            with self.records_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        rd = self.run_dir(record.run_id)
        rd.mkdir(parents=True, exist_ok=True)
        (rd / "run_record.json").write_text(json.dumps(json.loads(line), indent=2), encoding="utf-8")

    # ---------------------------------------------------------------- run dirs
    def run_dir(self, run_id: str) -> Path:
        return self.runs_dir / run_id

    def prepare_run_dir(self, run_id: str) -> Path:
        """Fresh, empty artifact directory for a run that has no record yet."""
        if self.is_completed(run_id):
            raise DuplicateRunError(f"run {run_id} is already completed")
        d = self.run_dir(run_id)
        if d.exists():
            d.rename(d.with_name(f"{run_id}.incomplete-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"))
        d.mkdir(parents=True)
        return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
