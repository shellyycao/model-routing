"""Outcome-blind resolution of approved workflow reruns for analysis.

Raw records remain append-only. A non-void rerun replaces its referenced infrastructure-void cell
in the effective analysis set; a rerun that is itself void does not replace the original void.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from src.contracts import WorkflowRunRecord

SUCCESSFUL_RERUN_REPLACES_VOID = "successful_rerun_replaces_void"


def resolve_workflow_reruns(records: Iterable[WorkflowRunRecord]) -> tuple[list[WorkflowRunRecord], dict]:
    rows = list(records)
    by_id = {row.run_id: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("duplicate workflow run_id while resolving reruns")
    reruns = [row for row in rows if row.rerun_of is not None]
    counts = Counter(row.rerun_of for row in reruns)
    duplicates = sorted(run_id for run_id, count in counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"more than one rerun record references original(s) {duplicates}")

    replacements: dict[str, WorkflowRunRecord] = {}
    retained_rerun_voids: list[str] = []
    for rerun in reruns:
        original = by_id.get(rerun.rerun_of)
        if original is None or original.rerun_of is not None:
            raise ValueError(f"rerun {rerun.run_id} references a missing or non-original run")
        if original.feasibility.outcome != "void_infra":
            raise ValueError(f"rerun {rerun.run_id} does not reference a void_infra original")
        original_key = (original.experiment_id, original.project_id, original.path_id, original.repeat_index)
        rerun_key = (rerun.experiment_id, rerun.project_id, rerun.path_id, rerun.repeat_index)
        if rerun_key != original_key:
            raise ValueError(f"rerun {rerun.run_id} does not match its original cell")
        if rerun.feasibility.outcome == "void_infra":
            retained_rerun_voids.append(rerun.run_id)
        else:
            replacements[original.run_id] = rerun

    effective = [replacements.get(row.run_id, row) for row in rows if row.rerun_of is None]
    audit = {
        "rule": SUCCESSFUL_RERUN_REPLACES_VOID,
        "raw_records": len(rows),
        "original_records": sum(row.rerun_of is None for row in rows),
        "rerun_records": len(reruns),
        "effective_records": len(effective),
        "replacements": [
            {"original_run_id": original_id, "effective_run_id": rerun.run_id,
             "project_id": rerun.project_id, "path_id": rerun.path_id,
             "repeat_index": rerun.repeat_index, "rerun_outcome": rerun.feasibility.outcome}
            for original_id, rerun in sorted(replacements.items())
        ],
        "rerun_voids_not_used_as_replacements": sorted(retained_rerun_voids),
        "original_void_records_retained_in_raw": sorted(row.rerun_of for row in reruns),
    }
    return effective, audit
