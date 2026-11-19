"""Regression tests for the locked first-pass A3 v2 human review."""

from __future__ import annotations

from pathlib import Path

from experiments.analyze_a3_v2_label_review import analyze


REPO = Path(__file__).resolve().parents[1]


def test_locked_review_validates_and_localizes_the_surface_defect():
    results, report = analyze(
        REPO / "results/review/a3_v2_query_review_completed.csv",
        REPO / "results/review/a3_v2_label_review_completed.csv",
    )
    assert results["grade_agreement"] == 167
    assert results["grade_disagreement"] == 13
    assert results["topic_match_disagreement"] == 13
    assert results["method_match_disagreement"] == 0
    assert results["affected_queries"] == ["A3Q-005", "A3Q-015", "A3Q-025"]
    assert results["query_rule_ambiguities"] == ["A3Q-005", "A3Q-015", "A3Q-025"]
    assert results["review_status"] == "locked_unblinded_requires_targeted_rereview"
    assert "167/180" in report
