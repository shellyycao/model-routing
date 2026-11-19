"""Build the offline continuation-v1 paid-approval freeze manifest.

This script performs no model, AWS, Docker, or network operation.  It freezes the reviewed
inventory, budget, approval wording, code/data hashes, output contract, and empty separate-ledger
baseline.  Claude creates the required git tag only after committing and reviewing the manifest.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiments import run_continuations as runner


def _ledger_baseline() -> dict[str, Any]:
    if not runner.LEDGER.exists():
        return {"path": str(runner.LEDGER.relative_to(runner.REPO)), "state": "not_created",
                "calls": 0, "spent_usd_priced": 0.0, "pending": {}}
    value = json.loads(runner.LEDGER.read_text())
    if value.get("calls", 0) != 0 or value.get("spent_usd_priced", 0.0) != 0.0 or value.get("pending", {}) != {}:
        raise ValueError("separate continuation ledger is not at an empty pre-execution baseline")
    return {"path": str(runner.LEDGER.relative_to(runner.REPO)), "state": "existing_empty",
            "calls": 0, "spent_usd_priced": 0.0, "pending": {}}


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
    return {
        "protocol": "continuation-v1-posthoc",
        "status": "continuation_frozen_paid_execution_approved",
        "date": runner.APPROVAL_DATE,
        "required_tag": runner.TAG,
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
