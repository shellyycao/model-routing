"""Build the offline CP7e Docker-void rerun freeze/approval manifest."""

from __future__ import annotations

import json

from experiments import run_price_matched_workflow as runner


APPROVAL_WORDING = "Approve the main run (504 calls, about $43 expected, $100 cap)"
APPROVAL_DATE = "2026-11-19"
IMAGE_AMENDMENT_DATE = "2026-11-19"
RERUN_AMENDMENT_DATE = "2026-11-19"
RERUN_AUTHORIZATION = "\u53ef\u4ee5\u4e0d\u7528\u6211\u6279\u51c6\uff0c\u5982\u679c\u662fdocker\u7684\u95ee\u9898\u4f60\u4e4b\u95f4\u91cd\u8dd1\u5c31\u884c"


def _verified_pilot_outcome() -> dict:
    summary = json.loads(runner.PILOT_SUMMARY.read_text())
    records = summary["records"]
    checks = {
        "planned_logical_calls": summary["planned_logical_calls"] == 9,
        "records": len(records) == 9,
        "api_success": all(row["call_status"] == "success" for row in records),
        "parsed": all(row["parse_ok"] is True for row in records),
        "stop_reason": all(row["stopReason"] == "end_turn" for row in records),
        "parameter_failures": not any(row["parameter_failure"] for row in records),
        "no_parameter_changes": summary["automatic_parameter_changes"] == 0,
        "quality_not_analyzed": summary["quality_analyzed"] is False,
        "ledger_calls": summary["ledger_state"]["calls"] == 9,
        "ledger_spend": summary["ledger_state"]["spent_usd_priced"] == 0.449949,
        "no_pending_reservations": summary["ledger_state"]["pending"] == {},
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"pilot evidence failed main-freeze checks: {failed}")
    return {
        "logical_calls": 9,
        "api_success": 9,
        "parsed": 9,
        "stopReason_end_turn": 9,
        "parameter_failures": 0,
        "input_tokens": summary["ledger_state"]["input_tokens"],
        "output_tokens": summary["ledger_state"]["output_tokens"],
        "actual_cost_usd": summary["ledger_state"]["spent_usd_priced"],
        "quality_inspected": False,
        "summary_path": str(runner.PILOT_SUMMARY.relative_to(runner.REPO)),
        "task_records_path": str(runner.PILOT_RECORDS.relative_to(runner.REPO)),
    }


def _verify_active_image() -> dict:
    verification_path = runner.REPO / "results/verification/sandbox_verification.json"
    verification = json.loads(verification_path.read_text())
    if verification.get("all_controls_verified") is not True or \
            verification.get("image_id") != runner.SANDBOX_IMAGE_ID:
        raise ValueError("immutable sandbox image does not match the active verified image")
    return {"active_verification_record": str(verification_path.relative_to(runner.REPO)),
            "verified_image_id": verification["image_id"]}


def _verify_completed_main_and_docker_voids() -> dict:
    from src.contracts import WorkflowRunRecord

    part_a = runner._read_task_records(runner.STAGE_RECORDS)
    workflow = [WorkflowRunRecord.model_validate(row)
                for row in runner._read_task_records(runner.WORKFLOW_RECORDS)]
    originals = [row for row in workflow if row.rerun_of is None]
    ledger = json.loads(runner.MAIN_SUMMARY.read_text())["ledger_state"]
    checkpoint = json.loads(runner.MAIN_GRID_CHECKPOINT.read_text())
    if len(part_a) != 36 or len(originals) != 156 or not 156 <= len(workflow) <= 161:
        raise ValueError("main task files do not preserve 36 Part A and 156 original Part B records")
    if ledger["failed_attempts"] != 0 or ledger["pending"] != {} or \
            ledger["spent_usd_priced"] != 25.480151299999978:
        raise ValueError("completed main ledger does not match the committed pre-rerun state")
    if checkpoint["projection_within_cap"] is not True or \
            checkpoint["projected_total_usd"] != 24.365198586451662:
        raise ValueError("main-grid cost checkpoint does not match the committed state")
    rerun_plan = runner.plan_docker_void_reruns(workflow)
    cells = [(row.project_id, row.path_id, row.repeat_index) for row in rerun_plan.eligible]
    if set(cells) != set(runner.APPROVED_DOCKER_VOID_CELLS) or len(cells) != 5:
        raise ValueError(f"Docker void selection differs from the approved five cells: {cells}")
    if len(rerun_plan.pending) + len(rerun_plan.completed_reruns) != 5:
        raise ValueError("Docker void rerun coverage is inconsistent with the five-cell freeze")
    return {
        "part_a_records": 36,
        "part_b_original_records": 156,
        "ledger_calls": ledger["calls"],
        "ledger_cost_usd": ledger["spent_usd_priced"],
        "failed_api_attempts": ledger["failed_attempts"],
        "pending_reservations": len(ledger["pending"]),
        "main_grid_projected_total_usd": checkpoint["projected_total_usd"],
        "approved_original_run_ids": [row.run_id for row in rerun_plan.eligible],
        "cells": [{"project_id": row.project_id, "path_id": row.path_id,
                   "repeat_index": row.repeat_index} for row in rerun_plan.eligible],
        "original_156_record_prefix_sha256": runner.workflow_record_prefix_sha256(),
    }


def build_manifest() -> dict:
    plan = runner.build_plan()
    approval = plan["main_approval"]
    if approval != {
        "wording": APPROVAL_WORDING,
        "date": APPROVAL_DATE,
        "logical_call_ceiling": 504,
        "realistic_estimate_usd_rounded": 43,
        "hard_budget_cap_usd": 100.0,
    }:
        raise ValueError("runner does not reflect the user's exact main approval")
    pilot = _verified_pilot_outcome()
    image_evidence = _verify_active_image()
    rerun_evidence = _verify_completed_main_and_docker_voids()
    selected = plan["selected_budget"]
    return {
        "protocol": "Price-Matched Workflow + Routing Replication",
        "version": runner.MAIN_TAG,
        "status": "main_frozen_paid_execution_approved",
        "date": APPROVAL_DATE,
        "user_main_approval": approval,
        "selected_max_tokens": runner.SELECTED_MAX_TOKENS,
        "comparability_disclosure": "maxTokens 16384 differs from the original Parts A/B setting of 4096",
        "hard_budget_cap_usd": runner.HARD_CAP_USD,
        "budget_scope": "completed compatibility pilot plus main run, on one shared reserve-then-settle ledger",
        "pilot_actual_plus_main_realistic_estimate_usd": (
            pilot["actual_cost_usd"] + selected["main"]["realistic_estimate"]["total"]["cost_usd"]
        ),
        "combined_pre_pilot_realistic_estimate_usd": selected["combined"]["realistic_estimate"]["total"]["cost_usd"],
        "combined_static_worst_case_usd": selected["combined"]["static_worst_case"]["total"]["cost_usd"],
        "below_static_worst_case_intentionally_accepted": True,
        "pilot_approved": True,
        "pilot_outcome": pilot,
        "main_approved": True,
        "main_required_tag": runner.MAIN_TAG,
        "previous_main_tag_retained": runner.PREVIOUS_MAIN_TAG,
        "previous_main_tags_retained": [runner.MAIN_TAG_V1, runner.MAIN_TAG_V1_1],
        "main_logical_call_ceiling": plan["call_counts"]["main"],
        "sandbox_execution": {
            "immutable_image_id": runner.SANDBOX_IMAGE_ID,
            "availability_run_and_lease_reference": runner.SANDBOX_IMAGE_ID,
            "short_name_fallback": False,
            "verification_record": "results/verification/sandbox_verification.json",
            "shared_default_image_constant_changed": False,
        },
        "amendments": [
            {
                "date": IMAGE_AMENDMENT_DATE,
                "id": "immutable-sandbox-image-pin",
                "scope": "execution_only",
                "scientific_protocol_changed": False,
                "main_calls_before_amendment": 0,
                "root_cause": (
                    "Docker Desktop containerd intermittently failed to resolve the short image name "
                    "while the fully qualified name and immutable image ID remained available"
                ),
                "change": (
                    f"price-matched workflow availability, run, and lease now use {runner.SANDBOX_IMAGE_ID}; "
                    "missing ID fails closed without short-name fallback"
                ),
                "superseded_execution_tag": runner.MAIN_TAG_V1,
                "replacement_execution_tag": runner.MAIN_TAG_V1_1,
                "old_tag_deleted": False,
                "no_main_execution_evidence": {
                    **image_evidence, "part_a_task_records": 0, "part_b_task_records": 0,
                    "main_invocations": 0,
                },
            },
            {
                "date": RERUN_AMENDMENT_DATE,
                "id": "outcome-blind-docker-void-rerun",
                "scope": "execution_and_analysis_handling_only",
                "scientific_protocol_changed": False,
                "user_authorization": {"date": RERUN_AMENDMENT_DATE,
                                       "wording": RERUN_AUTHORIZATION},
                "root_cause": "approximately two-minute Docker daemon outage; docker info timed out",
                "approved_cells": rerun_evidence["cells"],
                "rerun_count_ceiling": 5,
                "each_cell_reruns_exactly_once": True,
                "selection_is_outcome_blind": True,
                "original_records_deleted_or_overwritten": False,
                "analysis_rule": "a non-void rerun replaces its original void for the effective cell; raw original remains reported",
                "superseded_execution_tag": runner.MAIN_TAG_V1_1,
                "replacement_execution_tag": runner.MAIN_TAG,
                "old_tag_deleted": False,
            },
        ],
        "docker_void_rerun": {
            "approved": True,
            "authorization_wording": RERUN_AUTHORIZATION,
            "authorization_date": RERUN_AMENDMENT_DATE,
            "approved_original_run_ids": rerun_evidence["approved_original_run_ids"],
            "approved_cells": rerun_evidence["cells"],
            "logical_cell_ceiling": 5,
            "infra_attempt": 1,
            "repeat_index_unchanged": True,
            "same_models_parameters_prompts_and_image": True,
            "shared_ledger_hard_cap_usd": runner.HARD_CAP_USD,
            "original_156_record_prefix_sha256": rerun_evidence["original_156_record_prefix_sha256"],
            "pre_rerun_evidence": rerun_evidence,
            "analysis_resolution": "successful_rerun_replaces_void",
        },
        "model_parameters": [
            {"alias": row["alias"], "source_alias": row["source_alias"],
             "temperature": row["temperature"],
             "temperature_field": row["temperature_field"],
             "maxTokens": runner.SELECTED_MAX_TOKENS}
            for row in plan["models"]
        ],
        "experiment_ids": {
            "part_a": runner.STAGE_EXPERIMENT,
            "part_b": runner.WORKFLOW_EXPERIMENT,
        },
        "main_plan": {
            "part_a_task_records": 36,
            "part_b_main_task_records": 108,
            "part_b_repeat_task_records": 48,
            "part_b_total_task_records": 156,
            "part_a_model_call_ceiling": plan["call_counts"]["part_a"],
            "part_b_main_model_call_ceiling": plan["call_counts"]["part_b_main"],
            "part_b_repeat_model_call_ceiling": plan["call_counts"]["part_b_repeats"],
            "repeat_paths": list(runner.REPEAT_PATHS),
            "order": "Part A; mandatory stop; 27-path main grid; mandatory stop; repeats 1-2",
        },
        "commands": {
            "part_a": ".venv/bin/python -m experiments.run_price_matched_workflow --execute-approved-main",
            "main_grid": ".venv/bin/python -m experiments.run_price_matched_workflow --execute-approved-main --continue-after-part-a",
            "resume_repeats": ".venv/bin/python -m experiments.run_price_matched_workflow --execute-approved-main --continue-after-part-a --continue-after-main-grid",
            "rerun_docker_voids": ".venv/bin/python -m experiments.run_price_matched_workflow --rerun-docker-voids",
        },
        "outputs": {
            "part_a": {"path": str(runner.STAGE_RECORDS.relative_to(runner.REPO)),
                       "complete_lines": 36,
                       "group_fields": ["project_id", "stage", "model_alias"]},
            "part_b": {"path": str(runner.WORKFLOW_RECORDS.relative_to(runner.REPO)),
                       "original_lines": 156, "expected_lines_after_rerun": 161,
                       "group_fields": ["project_id", "path_id", "repeat_index"],
                       "main_grid_repeat_index": 0, "repeat_indices": [1, 2]},
            "invocations": {"path": str(runner.INVOCATIONS.relative_to(runner.REPO)),
                            "completion_source": False,
                            "group_field": "context.experiment_id"},
            "ledger": str(runner.LEDGER.relative_to(runner.REPO)),
        },
        "checkpoints": {
            "part_a": str(runner.PART_A_CHECKPOINT.relative_to(runner.REPO)),
            "main_grid": str(runner.MAIN_GRID_CHECKPOINT.relative_to(runner.REPO)),
            "main_grid_projection_must_be_within_cap": True,
        },
        "resume_completion_sources": [
            str(runner.STAGE_RECORDS.relative_to(runner.REPO)),
            str(runner.WORKFLOW_RECORDS.relative_to(runner.REPO)),
        ],
        "retry_policy": {"maximum_api_attempts_per_logical_call": runner.RETRY_ATTEMPTS,
                         "selective_retries": False,
                         "docker_void_rerun_has_standing_user_authorization": True,
                         "non_docker_void_rerun_requires_amendment_and_user_decision": True},
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
