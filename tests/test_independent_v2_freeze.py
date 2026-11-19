"""Offline checks for the immutable Independent-v2 freeze manifest."""

import json

from experiments.freeze_independent_v2 import OUT


def test_freeze_manifest_covers_every_protocol_component_and_records_paid_approval():
    # After execution, runner.plan() correctly excludes completed cells. Validate the
    # pre-execution manifest itself instead of trying to regenerate it post hoc.
    manifest = json.loads(OUT.read_text())
    assert manifest["version"] == "independent-v2-1.1"
    assert manifest["case_counts"] == {"a1": 30, "a2": 30, "a3": 30}
    assert manifest["difficulty_counts"] == {
        "a1": {"easy": 10, "medium": 10, "hard": 10},
        "a2": {"easy": 10, "medium": 10, "hard": 10},
        "a3": {"easy": 10, "medium": 10, "hard": 10},
    }
    assert manifest["planned_logical_calls"] == 270
    assert manifest["worst_case_output_tokens"] == 1_474_560
    assert manifest["expected_git_tag"] == "independent-v2-frozen-v1.1"
    assert manifest["paid_execution_approved"] is True
    assert manifest["paid_execution_approval_budget_usd"] == 100.0
    assert manifest["paid_calls_made"] == 0
    for field in (
        "dataset_tree_sha256",
        "prompt_tree_sha256",
        "response_schema_and_scorer_sha256",
        "runner_sha256",
        "usage_guard_sha256",
        "model_behavior_sha256",
        "protocol_document_sha256",
    ):
        assert len(manifest[field]) == 64
    assert manifest["hard_guards"]["budget_usd"] == 100.0
    assert manifest["pricing_status_at_freeze"]["all_priced"] is True
