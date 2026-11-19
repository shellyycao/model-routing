"""Offline tests for the additive v2.2 scorer and tier-matched protocol."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from experiments import run_tier_matched_v2_2 as runner
from experiments.build_tier_matched_v2_2_protocol import OUT as MANIFEST_OUT
from experiments.select_tier_matched_models import OUT as SELECTION_OUT, build_selection
from src.independent.v2_2 import (
    LiteratureClaimV22,
    LiteratureResponseV22,
    score_debugging_v22,
    score_literature_v22,
)


def test_a3_attribute_is_an_enum_in_validation_and_json_schema():
    allowed = {"dataset", "first_author", "method", "metric", "topic", "value", "year"}
    schema = LiteratureClaimV22.model_json_schema()
    assert set(schema["properties"]["attribute"]["enum"]) == allowed
    with pytest.raises(ValidationError):
        LiteratureClaimV22(attribute="approach", value="x", cited_ids=["D0001"])


def test_v22_a1_uses_normalized_location_without_changing_functional_score():
    case = {
        "buggy": "def foo(x):\n    return x + 1\n",
        "bug_locations": ["foo return expression"],
        "difficulty": "easy",
    }
    from src.independent.v2 import DebugResponseV2

    response = DebugResponseV2(
        fixed_code=case["buggy"], bug_locations=["`foo` at line 2"], explanation="fixed"
    )
    harness = {"results": [{"passed": True}], "load_error": None}
    result = score_debugging_v22(case, response, harness)
    assert result["functional_correct"] is True
    assert result["frozen_v2_bug_location_recall"] == 0
    assert result["bug_location_recall"] == 1


def test_v22_a3_uses_strict_primary_and_keeps_deduplicated_and_r2_secondary():
    case = {
        "difficulty": "hard",
        "relevance": {"D0001": 2, "D0002": 1, "D0003": 0},
        "facts": {"D0001": {"method": "Graph Net"}, "D0002": {"method": "Other"}},
    }
    response = LiteratureResponseV22(
        ranked_ids=["D0001", "D0001", "D0002", "D0003", "Z9999"],
        summary="Result [D0001] [Z9999]",
        claims=[
            LiteratureClaimV22(
                attribute="method", value="Graph Net", cited_ids=["D0001", "D0002"]
            )
            for _ in range(3)
        ],
    )
    result = score_literature_v22(case, response)
    assert result["operational_success"] is False
    assert result["ranking_valid"] is False
    assert result["ndcg_at_5"] == 0
    assert 0 < result["deduplicated_ndcg_at_5"] <= 1
    assert result["evidence_grounding"] == 0
    assert result["evidence_grounding_any_citation"] == 1
    assert result["citation_validity"] < 1
    assert "citation_accuracy" not in result


def test_v22_a3_valid_response_uses_r1_primary_and_citation_validity_name():
    relevance = {f"D{i:04d}": 2 if i <= 2 else 1 for i in range(1, 6)}
    facts = {doc: {"method": "Interview"} for doc in relevance}
    case = {"difficulty": "easy", "relevance": relevance, "facts": facts}
    response = LiteratureResponseV22(
        ranked_ids=list(relevance),
        summary=" ".join(f"[{doc}]" for doc in relevance),
        claims=[
            LiteratureClaimV22(attribute="method", value="Interview", cited_ids=["D0001", "D0002"])
            for _ in range(3)
        ],
    )
    result = score_literature_v22(case, response)
    assert result["ranking_valid"] is True
    assert result["ndcg_at_5"] == result["deduplicated_ndcg_at_5"] == pytest.approx(1.0)
    assert result["citation_validity"] == 1
    assert result["evidence_grounding"] == 1
    assert result["evidence_grounding_any_citation"] == 1


def test_offline_selection_is_reproducible_and_leaves_amazon_high_empty():
    rebuilt = build_selection()
    assert rebuilt == json.loads(SELECTION_OUT.read_text())
    slots = {(row["provider"], row["band"]): row for row in rebuilt["selected_slots"]}
    assert slots[("Amazon", "high")]["status"] == "empty_no_offline_eligible_model"
    assert slots[("Anthropic", "high")]["base_model_id"] == "anthropic.claude-sonnet-5-5"
    assert slots[("OpenAI", "high")]["base_model_id"] == "openai.gpt-6.1-sol"
    assert all(len(source["sha256"]) == 64 for source in rebuilt["inputs"]["pricing_snapshots"])
    assert all("pricing.us-east-1.amazonaws.com" in source["source_url"] for source in rebuilt["inputs"]["pricing_snapshots"])


def test_runner_plan_is_offline_locked_and_budget_cut_fits():
    plan = runner.build_plan()
    assert len(plan["models"]) == 8
    assert plan["budget"]["evaluation_logical_calls"] == 8 * 90 * 3
    assert plan["budget"]["probe_logical_call_reservations"] == 8 * 2
    assert plan["budget"]["maximum_api_attempts"] == 8 * (90 * 3 + 2) * 5
    assert plan["budget"]["fits_hard_cap"] is False
    assert plan["proposed_cut"]["budget"]["fits_hard_cap"] is True
    assert all(probe["status"] == "not_run" for probe in plan["access_probes"])
    assert runner.main([]) == 0


def test_superseded_tier_manifest_remains_an_explicit_historical_record():
    historical = json.loads(MANIFEST_OUT.read_text())
    assert historical["status"] == "superseded_by_price_matched_v2_never_frozen"
    assert historical["superseded_by"] == "docs/PRICE_MATCHED_V2_PLAN.md"
    assert historical["freeze_tag_created"] is False
    assert historical["paid_calls_made"] == historical["access_probes_run"] == 0
    assert historical["budget_decision_required"] is False
    assert historical["empty_slots"] == [{"provider": "Amazon", "band": "high"}]
    for key, value in historical["hashes"].items():
        if key != "pricing_snapshot_sha256":
            assert len(value) == 64
