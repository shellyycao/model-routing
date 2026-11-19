"""Regression tests for the locked targeted A3 v2 rereview."""

from __future__ import annotations

from pathlib import Path

from experiments.analyze_a3_v2_label_rereview import analyze


REPO = Path(__file__).resolve().parents[1]


def test_targeted_rereview_completes_adjudication_without_disagreement():
    results, report = analyze(
        REPO / "results/review/a3_v2_query_rereview_completed.csv",
        REPO / "results/review/a3_v2_label_rereview_completed.csv",
    )
    assert results["review_status"] == "complete_locked_unblinded"
    assert results["query_rule_ambiguities"] == []
    assert results["grade_agreement"] == 18
    assert results["grade_disagreement"] == 0
    assert results["human_grade_counts"] == {"0": 3, "1": 3, "2": 12}
    assert "adjudication is complete" in report
