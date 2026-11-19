"""Build the frozen, paid-execution-approved price-matched-v2 manifest."""

from __future__ import annotations

import json
from pathlib import Path

from experiments import run_price_matched_v2 as runner
from experiments.verify_price_matched_models import MODEL_PROBE, OUT as VERIFICATION


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results/processed/independent_v2/price_matched_v2_protocol_manifest.json"


def build_manifest() -> dict:
    verification = json.loads(VERIFICATION.read_text())
    saved_plan = json.loads(runner.PLAN_OUT.read_text())
    previous_manifest = json.loads(OUT.read_text())
    # The saved plan is a frozen scientific artifact. After repeat 1, rebuilding it
    # from the live ledger would mix execution state into protocol definition.
    if saved_plan.get("status") != "protocol_frozen_paid_execution_approved":
        raise ValueError("saved price-matched plan is not frozen and approved")
    if len(verification["models"]) != 3 or not all(row["verified"] for row in verification["models"]):
        raise ValueError("the three final models are not all verified")
    if saved_plan["evaluation"]["logical_calls"] != 810:
        raise ValueError("unexpected evaluation call count")
    if not saved_plan["compatibility_pilot"]["executed"]:
        raise ValueError("CP3d must retain the completed initial compatibility pilot")
    if not saved_plan["compatibility_repilot"]["executed"]:
        raise ValueError("freeze requires the completed re-pilot")
    pilot_summary = json.loads(runner.PILOT_SUMMARY.read_text())
    repilot_summary = json.loads(runner.REPILOT_SUMMARY.read_text())
    if repilot_summary.get("successes") != 6 or repilot_summary.get("parse_errors") != 0:
        raise ValueError("freeze requires 6/6 successful parsed re-pilot calls")
    model_probe = json.loads(MODEL_PROBE.read_text())
    probe_calls = len(model_probe["results"])
    checkpoint = json.loads(runner.CHECKPOINT.read_text())
    if checkpoint.get("summary") != {"executed": 270, "skipped_completed": 0, "void_infra": 0}:
        raise ValueError("repeat-1 checkpoint does not show the expected clean 270-call completion")
    return {
        "protocol": "Price-Matched Independent Benchmark v2",
        "version": "price-matched-v2-frozen-v1.1",
        "status": "protocol_frozen_paid_execution_approved",
        "date": "2026-11-18",
        "user_approval": {
            "wording": "Approve main run",
            "date": "2026-11-18",
            "scope": "810-call main experiment under the shared $100 hard cap with mandatory stop after repeat 1",
        },
        "required_tag": runner.FUTURE_TAG,
        "previous_tag_retained": "price-matched-v2-frozen-v1",
        "freeze_tag_created": False,
        "freeze_tag_creation_delegated_to": "Claude manager after review",
        "paid_calls_made_before_main": (
            pilot_summary["total_attempted_records"]
            + probe_calls
            + repilot_summary["total_attempted_records"]
        ),
        "network_requests_made_by_freeze_build": 0,
        "compatibility_pilot_executed": True,
        "compatibility_pilot_approved": True,
        "compatibility_pilot_hard_cap_usd": 15.0,
        "compatibility_pilot_uses_shared_100_usd_ledger": True,
        "model_count": 3,
        "evaluation_logical_calls": 810,
        "compatibility_pilot_max_calls": 9,
        "compatibility_pilot_actual_api_attempts": pilot_summary["total_attempted_records"],
        "compatibility_repilot_approved": True,
        "compatibility_repilot_executed": True,
        "compatibility_repilot_max_calls": 6,
        "compatibility_repilot_successes": repilot_summary["successes"],
        "compatibility_repilot_schema_parses": 6 - repilot_summary["parse_errors"],
        "hard_cap_usd": runner.HARD_CAP_USD,
        "static_worst_case_usd": saved_plan["budget"]["static_worst_case"]["total_usd"],
        "realistic_estimate_usd": saved_plan["budget"]["realistic_estimate"]["total_usd"],
        "cost_checkpoint_after_repeat": 1,
        "pre_main_ledger_state": previous_manifest["pre_main_ledger_state"],
        "repeat1_execution_state": {
            "logical_calls": checkpoint["summary"]["executed"],
            "void_infra": checkpoint["summary"]["void_infra"],
            "evaluation_actual_usd": checkpoint["repeat1_evaluation_actual_usd"],
            "projected_total_usd": checkpoint["projected_total_usd"],
            "projection_within_cap": checkpoint["projection_within_cap"],
            "resume_crash_ledger_calls": 283,
            "resume_crash_occurred_before_any_new_call": True,
        },
        "amendments": [{
            "id": "resume-completed-record-scan-v1.1",
            "date": "2026-11-18",
            "classification": "execution_bookkeeping_bugfix",
            "failure": "resume raised KeyError 'run_id' while reading invocations.jsonl",
            "timing": "before any repeat-2/3 model call or ledger reservation",
            "fix": "_completed reads only price_matched_v2_a1/a2/a3 task record JSONL files",
            "scientific_protocol_changed": False,
            "unchanged": [
                "data", "prompts", "scorer", "models", "parameters",
                "repeat-major order", "810-call scope", "$100 hard cap",
                "mandatory repeat-1 cost checkpoint",
            ],
            "supersedes_execution_tag": "price-matched-v2-frozen-v1",
            "required_execution_tag": runner.FUTURE_TAG,
        }],
        "execution": {
            "initial_command": ".venv/bin/python -m experiments.run_price_matched_v2 --execute",
            "resume_after_repeat_1_command": ".venv/bin/python -m experiments.run_price_matched_v2 --execute --continue-after-repeat-1",
            "mandatory_stop_after_repeat": 1,
            "records_dir": "results/raw/price_matched_v2/",
            "run_artifacts_dir": "results/raw/runs/<run_id>/",
            "invocation_log": "results/raw/price_matched_v2/invocations.jsonl",
            "ledger": "results/raw/ledgers/price_matched_v2.json",
            "checkpoint": "results/raw/price_matched_v2/repeat1_cost_checkpoint.json",
        },
        "hashes": runner.protocol_hashes(),
    }


def main() -> int:
    manifest = build_manifest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
