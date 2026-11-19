"""Build the offline continuation-v1 paid-approval freeze manifest.

This script performs no model, AWS, Docker, or network operation.  It freezes the reviewed
inventory, budget, approval wording, code/data hashes, output contract, and empty separate-ledger
baseline.  Claude creates the required git tag only after committing and reviewing the manifest.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from experiments import run_continuations as runner


def _ledger_baseline() -> dict[str, Any]:
    if runner.MANIFEST.exists():
        previous = json.loads(runner.MANIFEST.read_text()).get("ledger_baseline")
        if previous and previous.get("calls") == 0 and previous.get("spent_usd_priced") == 0.0 and \
                previous.get("pending") == {}:
            return previous
    if not runner.LEDGER.exists():
        return {"path": str(runner.LEDGER.relative_to(runner.REPO)), "state": "not_created",
                "calls": 0, "spent_usd_priced": 0.0, "pending": {}}
    value = json.loads(runner.LEDGER.read_text())
    if value.get("calls", 0) != 0 or value.get("spent_usd_priced", 0.0) != 0.0 or value.get("pending", {}) != {}:
        raise ValueError("separate continuation ledger is not at an empty pre-execution baseline")
    return {"path": str(runner.LEDGER.relative_to(runner.REPO)), "state": "existing_empty",
            "calls": 0, "spent_usd_priced": 0.0, "pending": {}}


def _record_prefix_sha256(count: int) -> str:
    lines = runner.RECORDS.read_bytes().splitlines(keepends=True)
    if len(lines) < count:
        raise ValueError(f"continuation record file has {len(lines)} lines; expected at least {count}")
    return hashlib.sha256(b"".join(lines[:count])).hexdigest()


def _resume_amendment_evidence() -> dict[str, Any]:
    if not runner.RECORDS.exists() and runner.MANIFEST.exists():
        previous = json.loads(runner.MANIFEST.read_text())
        amendments = previous.get("amendments", [])
        if amendments and amendments[-1].get("id") == "unparseable-cleaning-summary-and-empty-directory-resume":
            return amendments[-1]["pre_resume_evidence"]
    records = runner.read_jsonl(runner.RECORDS)
    ledger = json.loads(runner.LEDGER.read_text())
    if len(records) != 30 or len({row["continued_from"] for row in records}) != 30:
        raise ValueError("execution amendment expects exactly 30 append-only completed records")
    if ledger["calls"] != 30 or ledger["failed_attempts"] != 0 or ledger["pending"] != {}:
        raise ValueError("execution amendment ledger does not match the 30-call pre-crash state")
    pending = runner.pending_cells(runner.eligible_cells(), records)
    if len(pending) != 10:
        raise ValueError("execution amendment expects exactly 10 pending cells")
    crashed = pending[0]
    crashed_run_id = runner.continuation_run_id(crashed)
    crashed_dir = runner.RUNS / crashed_run_id
    payload = [path for path in crashed_dir.rglob("*") if path.is_symlink() or not path.is_dir()]
    if not crashed_dir.is_dir() or payload:
        raise ValueError("crashed continuation directory is not empty scaffolding")
    invocation_run_ids = {row["context"]["run_id"] for row in runner.read_jsonl(runner.INVOCATIONS)}
    if crashed_run_id in invocation_run_ids:
        raise ValueError("crashed continuation unexpectedly has a model invocation")
    return {
        "completed_task_records": 30,
        "distinct_continued_from": 30,
        "remaining_logical_calls": 10,
        "first_30_record_prefix_sha256": _record_prefix_sha256(30),
        "ledger_calls": ledger["calls"],
        "ledger_spent_usd_priced": ledger["spent_usd_priced"],
        "ledger_failed_attempts": ledger["failed_attempts"],
        "ledger_pending": ledger["pending"],
        "crashed_run_id": crashed_run_id,
        "crash_before_model_call": True,
        "crashed_run_directory_empty": True,
    }


def _replay_evidence() -> list[dict[str, Any]]:
    rows = []
    for cell in runner.eligible_cells():
        replay = cell.replay
        rows.append({
            "group": cell.group,
            "continued_from": cell.original.run_id,
            "project_id": cell.original.project_id,
            "path_id": cell.original.path_id,
            "repeat_index": cell.original.repeat_index,
            "recovered_stage": replay["stage"],
            "recovered_model_alias": replay["model_alias"],
            "original_code_sha256": replay["original_code_sha256"],
            "patched_code_sha256": replay["patched_code_sha256"],
            "recovered_output_sha256": replay["output_sha256"],
            "sandbox_image": replay["execution"]["sandbox_image"],
            "frozen_validator_hard_pass": replay["frozen_validation"]["hard_pass"],
            "remaining": [{"stage": stage.value, "model_alias": alias}
                          for _, stage, alias in cell.remaining],
        })
    if len(rows) != 40 or any(not row["frozen_validator_hard_pass"] for row in rows):
        raise ValueError("eligible replay evidence differs from reviewed 40-cell inventory")
    return rows


def build_manifest() -> dict[str, Any]:
    plan = runner.build_plan()
    if plan["eligible_cells"] != 40 or plan["outputs"]["complete_record_lines"] != 40:
        raise ValueError("runner plan does not contain the approved 40-call inventory")
    budget = plan["budget"]
    if budget["proposed_hard_cap_usd"] != runner.HARD_CAP_USD or \
            budget["realistic_estimate"]["total"]["cost_usd"] != 1.4092798278317638:
        raise ValueError("runner budget differs from the amount presented to the user")
    approval = {"question": runner.APPROVAL_QUESTION, "wording": runner.APPROVAL_WORDING,
                "date": runner.APPROVAL_DATE}
    resume = _resume_amendment_evidence()
    return {
        "protocol": "continuation-v1-posthoc",
        "status": "continuation_frozen_paid_execution_approved",
        "date": runner.APPROVAL_DATE,
        "required_tag": runner.TAG,
        "previous_tag_retained": runner.PREVIOUS_TAG,
        "paid_execution_approved": True,
        "approval": approval,
        "scope": "40 reporting-stage continuations for reviewed int64-recovered Part B analysis cells only",
        "logical_call_ceiling": 40,
        "complete_record_lines": 40,
        "progress_field": "continued_from",
        "hard_budget_cap_usd": runner.HARD_CAP_USD,
        "budget_scope": "separate reserve-then-settle continuation ledger only",
        "ledger_path": str(runner.LEDGER.relative_to(runner.REPO)),
        "ledger_baseline": _ledger_baseline(),
        "invocation_log_path": str(runner.INVOCATIONS.relative_to(runner.REPO)),
        "task_records_path": str(runner.RECORDS.relative_to(runner.REPO)),
        "run_artifacts_path": str(runner.RUNS.relative_to(runner.REPO)),
        "execution_command": (
            ".venv/bin/python -m experiments.run_continuations "
            "--execute-approved-continuations"
        ),
        "completion_rule": (
            "exactly 40 JSONL task-record lines and 40 distinct continued_from values; "
            "invocation-log lines are not the progress denominator"
        ),
        "inventory_sha256": plan["inventory_sha256"],
        "eligible_cells": plan["eligible_cells"],
        "recovered_stage_counts": plan["recovered_stage_counts"],
        "remaining_call_counts": plan["remaining_call_counts"],
        "eligible_replay_evidence": _replay_evidence(),
        "budget": budget,
        "settings": plan["settings"],
        "compatibility_smoke_test": plan["compatibility_smoke_test"],
        "corrected_part_b_guard": {
            "compute_before_continuations_exist": False,
            "analysis_requires_task_record_lines": 40,
            "cleaning_recoveries_with_observed_downstream": 11,
            "cleaning_recovery_rule": (
                "use saved downstream outcomes without rerun; disclose that their handoffs saw "
                "upstream cleaning validation_status=failed"
            ),
        },
        "amendments": [{
            "date": "2026-11-19",
            "id": "unparseable-cleaning-summary-and-empty-directory-resume",
            "scope": "execution_bookkeeping_only",
            "scientific_protocol_changed": False,
            "approval_changed": False,
            "models_parameters_prompts_inventory_cap_and_ledger_changed": False,
            "crash": (
                "json.JSONDecodeError while reconstructing an original truncated cleaning_summary.json; "
                "the crash occurred before any model call for that cell"
            ),
            "handoff_fix": (
                "reuse the exact cleaning representation saved in the original analysis handoff: "
                "summary None, file retained, original limitation and failed status"
            ),
            "resume_fix": (
                "reuse an unrecorded run directory only when it contains no files and at most empty "
                "subdirectories; any payload still fails closed"
            ),
            "superseded_tag": runner.PREVIOUS_TAG,
            "replacement_tag": runner.TAG,
            "old_tag_deleted": False,
            "pre_resume_evidence": resume,
        }],
        "hashes": runner.protocol_hashes(),
        "network_or_model_calls_during_freeze_preparation": 0,
        "tag_created_by_builder": False,
    }


def main() -> int:
    manifest = build_manifest()
    runner.MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    runner.MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
