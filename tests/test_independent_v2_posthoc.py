"""Tests for model-agnostic Independent-v2 post-hoc rules."""

import json

import pytest

from experiments.analyze_independent_v2_posthoc import analyze
from src.independent.v2_posthoc import (
    bootstrap_paired_difference,
    canonical_attribute,
    claim_supported_r1,
    claim_supported_r2,
    classify_a2_error,
    exact_mcnemar,
    frozen_claim_reason,
    holm_adjust,
    score_a1_locations,
    score_a3_deduplicated,
    score_a3_grounding,
    wilcoxon_approx,
)


def test_a1_function_and_line_overlap_normalization():
    case = {"buggy": "def foo(x):\n    y = x + 1\n    return y\n", "bug_locations": ["foo return"]}
    by_name = score_a1_locations(case, {"fixed_code": case["buggy"], "bug_locations": ["`foo`: return"]})
    by_line = score_a1_locations(case, {"fixed_code": case["buggy"], "bug_locations": ["lines 2-3"]})
    wrong = score_a1_locations(case, {"fixed_code": case["buggy"], "bug_locations": ["line 9"]})
    mismatch = score_a1_locations(case, {"fixed_code": case["buggy"], "bug_locations": ["changed return"]})
    assert by_name["normalized_location_recall"] == by_line["normalized_location_recall"] == 1
    assert wrong["wrong_location"] == 1
    assert mismatch["format_mismatch"] == 1


def test_a1_anchor_disclosures_distinguish_bare_and_fixed_only():
    case = {"buggy": "\n\n\ndef foo(x):\n    return x\n", "bug_locations": ["foo return"]}
    bare = score_a1_locations(case, {"fixed_code": case["buggy"], "bug_locations": ["4-5"]})
    fixed = score_a1_locations(case, {
        "fixed_code": "def foo(x):\n    return x\n", "bug_locations": ["line 1"]
    })
    assert bare["bare_range_only_match"] == 1
    assert fixed["fixed_span_only_match"] == 1


@pytest.mark.parametrize("claim,facts,reason", [
    ({"attribute": "method", "value": "x", "cited_ids": []}, {"D": {"method": "x"}}, "no_citation"),
    ({"attribute": "method", "value": "x", "cited_ids": ["X"]}, {"D": {"method": "x"}}, "unknown_doc"),
    ({"attribute": "approach", "value": "x", "cited_ids": ["D"]}, {"D": {"method": "x"}}, "attribute_key_mismatch"),
    ({"attribute": "method", "value": "y", "cited_ids": ["D"]}, {"D": {"method": "x"}}, "value_mismatch"),
    ({"attribute": "method", "value": "x", "cited_ids": ["D"]}, {"D": {"method": ["x"]}}, "supported"),
])
def test_frozen_grounding_failure_reason_precedence(claim, facts, reason):
    assert frozen_claim_reason(claim, facts) == reason


def test_grounding_relaxations_are_nested_and_model_agnostic():
    facts = {"D1": {"method": ["Graph Net"]}, "D2": {"method": ["Other"]}}
    claim = {"attribute": "Approach", "value": "Graph Net", "cited_ids": ["D1", "D2"]}
    assert canonical_attribute("Approach") == "method"
    assert claim_supported_r1(claim, facts) is False
    assert claim_supported_r2(claim, facts) is True
    scored = score_a3_grounding({"facts": facts}, {"claims": [claim]})
    assert scored["attribute_key_coverage"] == 1


def test_deduplicated_ranking_keeps_first_top5_and_pads_zero():
    case = {"relevance": {"D1": 2, "D2": 1, "D3": 0}}
    result = score_a3_deduplicated(case, {"ranked_ids": ["D1", "D1", "D2", "D2", "X", "D3"]})
    assert result["kept_ids"] == ["D1", "D2", "X"]
    assert result["gains"] == [2, 1, 0, 0, 0]
    assert 0 <= result["ndcg_at_5"] <= 1
    assert 0 <= result["grade2_recall_at_5"] <= 1


def test_a2_taxonomy_priority_and_residual():
    assert classify_a2_error({"document_family": "invoice"}, "total_due_usd") == "unit_scale_conversion"
    assert classify_a2_error({"document_family": "invoice"}, "invoice_id") == "conflict_resolution"
    assert classify_a2_error({"document_family": "invoice"}, "vendor") == "field_omission"


def test_exact_mcnemar_and_bootstrap_are_deterministic():
    first = [True, True, False, False]
    second = [False, True, True, False]
    result = exact_mcnemar(first, second)
    assert result == {"first_only": 1, "second_only": 1, "p_value": 1.0}
    one = bootstrap_paired_difference([1, 1, 0, 0], [0, 1, 1, 0], seed=7)
    two = bootstrap_paired_difference([1, 1, 0, 0], [0, 1, 1, 0], seed=7)
    assert one == two and one["difference"] == 0


def test_wilcoxon_zero_and_tie_handling():
    assert wilcoxon_approx([1, 2], [1, 2]) == {
        "statistic": 0.0, "p_value": 1.0, "n_nonzero": 0, "z": 0.0
    }
    tied = wilcoxon_approx([2, 3, 4, 5], [1, 2, 3, 4])
    assert tied["n_nonzero"] == 4
    assert tied["statistic"] == 0
    # Four equal positive differences: average ranks are 2.5, W+=10,
    # tie-corrected variance is 6.25, z=2, two-sided p=erfc(sqrt(2)).
    assert tied["z"] == pytest.approx(2.0)
    assert tied["p_value"] == pytest.approx(0.04550026389635844)


def test_holm_mapping_is_monotone_in_sorted_p_values():
    adjusted = holm_adjust([("x", 0.01), ("y", 0.04), ("z", 0.03)])
    assert adjusted["x"] == pytest.approx(0.03)
    assert adjusted["z"] == pytest.approx(0.06)
    assert adjusted["y"] == pytest.approx(0.06)


def test_integrated_posthoc_output_is_blinded_and_complete():
    result = analyze()
    assert result["label"] == "post-hoc / exploratory"
    assert sum(len(rows) for rows in result["record_views"].values()) == 270
    assert set(result["cells"]) == {f"{task}|{alias}" for task in ("a1", "a2", "a3") for alias in "ABC"}
    serialized = json.dumps(result)
    assert "Claude" not in serialized and "Nova Pro" not in serialized and "gpt-oss" not in serialized
