"""Build the offline CP7b compatibility-pilot freeze/approval manifest."""

from __future__ import annotations

import json

from experiments import run_price_matched_workflow as runner


def build_manifest() -> dict:
    plan = runner.build_plan()
    if plan["user_decision"] != {
        "wording": "16384, $100 cap",
        "date": "2026-11-19",
        "selected_maxTokens": 16384,
        "hard_budget_cap_usd": 100.0,
        "pilot_approved": True,
        "main_approved": False,
        "pilot_requires_separate_explicit_approval": True,
        "main_requires_separate_explicit_approval": True,
    }:
        raise ValueError("runner does not reflect the user's frozen pilot-stage decision")
    selected = plan["selected_budget"]
    return {
        "protocol": "Price-Matched Workflow + Routing Replication",
        "version": "price-matched-workflow-pilot-v1",
        "status": "pilot_frozen_paid_execution_approved",
        "date": "2026-11-19",
        "user_decision": {
            "wording": "16384, $100 cap",
            "date": "2026-11-19",
            "comparability_disclosure": "maxTokens 16384 differs from the original Parts A/B setting of 4096",
        },
        "selected_max_tokens": runner.SELECTED_MAX_TOKENS,
        "hard_budget_cap_usd": runner.HARD_CAP_USD,
        "budget_scope": "compatibility pilot plus any later separately approved main run",
        "below_static_worst_case_intentionally_accepted": True,
        "combined_realistic_estimate_usd": selected["combined"]["realistic_estimate"]["total"]["cost_usd"],
        "combined_static_worst_case_usd": selected["combined"]["static_worst_case"]["total"]["cost_usd"],
        "pilot_realistic_estimate_usd": selected["pilot"]["realistic_estimate"]["total"]["cost_usd"],
        "pilot_static_worst_case_usd": selected["pilot"]["static_worst_case"]["total"]["cost_usd"],
        "pilot_approved": True,
        "pilot_approval_scope": "exactly 9 structural compatibility calls in the frozen order",
        "pilot_required_tag": runner.PILOT_TAG,
        "pilot_command": ".venv/bin/python -m experiments.run_price_matched_workflow --execute-approved-pilot",
        "pilot_logical_calls": 9,
        "pilot_order": [
            {"stage": row["stage"], "model_alias": row["model_alias"], "project": row["project"]}
            for row in runner.call_inventory() if row["phase"] == "pilot"
        ],
        "model_parameters": [
            {"alias": row["alias"], "source_alias": row["source_alias"],
             "temperature": row["temperature"],
             "temperature_field": row["temperature_field"],
             "maxTokens": runner.SELECTED_MAX_TOKENS}
            for row in plan["models"]
        ],
        "experiment_ids": {
            "pilot": runner.PILOT_EXPERIMENT,
            "part_a": runner.STAGE_EXPERIMENT,
            "part_b": runner.WORKFLOW_EXPERIMENT,
        },
        "retry_policy": {"maximum_api_attempts_per_logical_call": runner.RETRY_ATTEMPTS,
                         "unchanged_from_shared_bedrock_client": True},
        "shared_ledger": str(runner.LEDGER.relative_to(runner.REPO)),
        "pilot_summary": str(runner.PILOT_SUMMARY.relative_to(runner.REPO)),
        "pilot_rules": {
            "parameter_failure": "stop remaining slots for that model",
            "automatic_parameter_changes": 0,
            "record_fields": ["call_status", "error", "input_tokens", "output_tokens",
                              "reasoning_chars", "effective_parameters", "stopReason",
                              "parse_ok", "structural_ok", "latency_ms", "cost_usd"],
            "quality_inspection": "forbidden",
            "main_training_eligible": False,
        },
        "main_approved": False,
        "main_required_tag": runner.MAIN_TAG,
        "main_execution_must_refuse": True,
        "main_plan": {
            "logical_call_ceiling": plan["call_counts"]["main"],
            "part_a": plan["call_counts"]["part_a"],
            "part_b_main": plan["call_counts"]["part_b_main"],
            "part_b_repeats": plan["call_counts"]["part_b_repeats"],
            "repeat_paths": list(runner.REPEAT_PATHS),
            "execution_order": "Part A; mandatory stop; Part B main grid; mandatory stop; repeats",
        },
        "main_checkpoints_prepared": [
            "results/raw/price_matched_workflow/part_a_cost_checkpoint.json",
            "results/raw/price_matched_workflow/main_grid_cost_checkpoint.json",
        ],
        "freeze_tag_created": False,
        "freeze_tag_creation_delegated_to": "Claude manager after review",
        "network_or_model_calls_made_by_manifest_build": 0,
        "hashes": runner.protocol_hashes(),
    }


def main() -> int:
    manifest = build_manifest()
    runner.APPROVAL_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    runner.APPROVAL_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
