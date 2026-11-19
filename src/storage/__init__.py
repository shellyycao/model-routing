"""Append-only result storage (raw records + per-run artifact directories)."""

from .run_store import (
    DuplicateRunError,
    ExperimentModeError,
    RunStore,
    STAGE_BENCHMARK,
    WORKFLOW,
)

__all__ = ["RunStore", "DuplicateRunError", "ExperimentModeError", "WORKFLOW", "STAGE_BENCHMARK"]
