"""Offline checks for the completed Independent-v2 analysis."""

from experiments.analyze_independent_v2 import analyze


def test_completed_v2_analysis_audits_full_matrix_and_ledger():
    result = analyze()
    audit = result["audit"]
    assert audit["status"] == "pass"
    assert audit["totals"]["records"] == 270
    assert audit["unique_run_ids"] == audit["unique_invocation_ids"] == 270
    assert audit["failed_attempts"] == audit["unknown_usage_calls"] == audit["unpriced_calls"] == 0
    assert set(result["cells"]) == {f"{task}|{alias}" for task in ("a1", "a2", "a3") for alias in "ABC"}
    assert all(cell["n"] == 30 for cell in result["cells"].values())


def test_a3_sensitivity_views_are_bounded_and_preserve_frozen_audit():
    result = analyze()
    for alias in "ABC":
        primary = result["cells"][f"a3|{alias}"]["primary"]
        assert 0 <= primary["strict_invalid_as_zero"]["mean"] <= 1
        assert 0 <= primary["valid_ranking_only"]["mean"] <= 1
    assert sum(
        result["cells"][f"a3|{alias}"]["primary"]["frozen_values_over_one"] for alias in "ABC"
    ) > 0
