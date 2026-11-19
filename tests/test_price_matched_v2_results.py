"""Regression tests for the completed offline CP4 analysis."""

import json

import pytest

from experiments import analyze_price_matched_v2 as analysis


def test_task_loader_never_reads_colocated_invocation_log():
    records = analysis._load_records()
    assert len(records) == 810
    assert len({row["run_id"] for row in records}) == 810
    assert {row["task"] for row in records} == {"a1", "a2", "a3"}
    assert all("context" not in row for row in records)


def test_completed_run_integrity_and_cost_reconcile_exactly():
    result = analysis.build_full_analysis()
    audit = result["integrity_audit"]
    assert audit["status"] == "pass"
    assert audit["record_counts"]["status"] == {"failed": 10, "passed": 798, "void_infra": 2}
    assert audit["correspondence"]["primary_invocations"] == 810
    assert audit["retry_policy"]["automatic_failed_attempts"] == 13
    assert audit["retry_policy"]["logical_cells_rerun"] == 0
    assert audit["retry_policy"]["error_codes"] == ["EndpointConnectionError"]
    costs = audit["cost_reconciliation"]
    assert costs["known_response_cost_usd"] == pytest.approx(20.7583886)
    assert costs["failed_attempt_reservations_usd"] == pytest.approx(2.4794588)
    assert costs["main_experiment_ledger_cost_usd"] == pytest.approx(23.2378474)
    assert costs["shared_ledger_cost_usd"] == pytest.approx(23.9092314)
    assert all(costs["checks"].values())


def test_void_policy_denominators_and_failure_sensitivity():
    result = analysis.build_full_analysis()
    main = {(row["task"], row["model_alias"]): row for row in result["main_analysis_void_excluded"]["cells"]}
    sensitivity = {(row["task"], row["model_alias"]): row for row in result["sensitivity_void_as_failure"]["cells"]}
    assert main[("a1", "sonnet_4_6")]["analyzed_denominator"] == 89
    assert main[("a1", "glm_5")]["analyzed_denominator"] == 89
    assert main[("a1", "kimi_k3")]["analyzed_denominator"] == 90
    assert all(row["analyzed_denominator"] == 90 for row in sensitivity.values())
    assert sensitivity[("a1", "sonnet_4_6")]["primary_mean"] < main[("a1", "sonnet_4_6")]["primary_mean"]
    assert sensitivity[("a1", "glm_5")]["primary_mean"] < main[("a1", "glm_5")]["primary_mean"]


def test_a3_strict_primary_pareto_and_required_secondary_metrics():
    result = analysis.build_full_analysis()
    cells = [row for row in result["main_analysis_void_excluded"]["cells"] if row["task"] == "a3"]
    assert all(row["primary_metric"] == "ndcg_at_5" for row in cells)
    assert all(row["cost_per_valid_response_usd"] is not None for row in cells)
    assert all(row["cost_per_strict_ndcg_point_usd"] is not None for row in cells)
    for row in cells:
        assert {"deduplicated_ndcg_at_5", "grounding_r1_all_citations",
                "grounding_r2_any_citation", "citation_validity"} <= set(row["secondary_metrics"])
    assert result["main_analysis_void_excluded"]["pareto_frontier_by_task"]["a3"]["quality_axis"] == "ndcg_at_5"


def test_saved_analysis_is_reproducible_and_stat_families_are_holm_adjusted():
    result = analysis.build_full_analysis()
    assert result == json.loads(analysis.OUT.read_text())
    stats = result["main_analysis_void_excluded"]["paired_statistics"]
    assert stats["families_defined_before_testing"] == analysis.FAMILIES
    assert set(stats["families"]) == set(analysis.FAMILIES)
    assert all(len(rows) == 3 for rows in stats["families"].values())
    assert all("holm_adjusted_p_value" in row and row["paired_bootstrap"]["draws"] == 10_000
               for rows in stats["families"].values() for row in rows)


def test_kimi_returned_reasoning_explains_output_composition_with_labeled_approximation():
    result = analysis.build_full_analysis()
    composition = result["output_composition"]
    assert composition["char_to_token_approximation"] == 4.0
    assert "approximations" in composition["approximation_warning"]
    rows = {row["task"]: row for row in composition["kimi_vs_sonnet"]}
    assert {task: row["kimi_reasoning_chars_coverage"] for task, row in rows.items()} == {
        "a1": 90, "a2": 90, "a3": 90
    }
    assert [rows[t]["kimi_median_reasoning_chars"] for t in ("a1", "a2", "a3")] == [
        5583.5, 1108.5, 27467.0
    ]
    assert [rows[t]["kimi_median_final_answer_chars"] for t in ("a1", "a2", "a3")] == [
        1180.5, 209.0, 4385.0
    ]
    assert rows["a3"]["kimi_sum_of_component_medians_approx_tokens"] == pytest.approx(7963.0)
    assert rows["a3"]["kimi_median_billed_output_tokens"] == 7718.0
    assert all(0.9 < row["kimi_to_sonnet_final_answer_median_char_ratio"] < 1.2
               for row in rows.values())
