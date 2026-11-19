"""Offline tests for the locked CP4b workflow-cost analysis."""

import json

import pytest

from experiments import analyze_workflow_cost_posthoc as analysis


def test_verified_original_model_prices_are_exact():
    prices = analysis.load_prices()
    assert [(alias, row["input_per_mtok"], row["output_per_mtok"], row["retrieved"])
            for alias, row in prices.items()] == [
        ("A", 3.3, 16.5, "2026-11-18"),
        ("B", 0.8, 3.2, "2026-11-18"),
        ("C", 0.15, 0.6, "2026-11-18"),
    ]


def test_integrity_and_ledgers_reconcile_without_zero_imputation():
    result = analysis.build_analysis()
    audit = result["integrity_audit"]
    assert audit["status"] == "pass"
    assert audit["workflow_records"] == audit["unique_run_ids"] == 156
    assert audit["primary_invocations"] == 339
    assert audit["parse_children"] == 17
    assert audit["computed_totals"] == audit["ledger_totals"] == {
        "calls": 339, "failed_attempts": 0, "input_tokens": 828017,
        "output_tokens": 843303, "unknown_usage_calls": 0,
    }
    assert audit["cost_complete_runs"] == 156
    assert audit["known_usage_spend_usd"] == pytest.approx(7.6922558)
    assert audit["routing_artifacts"] == {
        "validated_traces": 20,
        "prediction_chain_ok": True,
        "prediction_chain_records": 50,
        "validation_chain_ok": True,
        "validation_chain_records": 50,
        "prediction_validation_links_checked": 50,
    }


def test_dual_validator_views_share_spend_but_not_feasibility_denominators():
    result = analysis.build_analysis()
    overall = result["overall"]
    assert overall["frozen_v3"]["n_feasible"] == 28
    assert overall["posthoc_v31"]["n_feasible"] == 38
    assert overall["frozen_v3"]["n_nonvoid"] == overall["posthoc_v31"]["n_nonvoid"] == 156
    assert overall["total_spend_usd"] == pytest.approx(7.6922558)
    for row in result["project_path_summaries"]:
        assert "frozen_v3" in row and "posthoc_v31" in row
        assert "total_spend_usd" in row and "mean_cost_per_run_usd" in row
    assert set(result["pareto_frontiers"]["pooled_posthoc_view"]) == {"frozen_v3", "posthoc_v31"}


def test_zero_success_and_single_run_labels_are_explicit():
    result = analysis.build_analysis()
    single = [row for row in result["project_path_summaries"] if row["n_runs"] == 1]
    assert single and all(row["evidence_label"] == "single-run evidence" for row in single)
    zero = [row for row in result["project_path_summaries"] if row["frozen_v3"]["n_feasible"] == 0]
    assert zero
    assert all(row["frozen_v3"]["cost_per_feasible_completion_usd"] is None and
               row["frozen_v3"]["not_estimable_reason"] == "zero_feasible_runs" for row in zero)


def test_pareto_retains_exact_ties_and_excludes_missing():
    base = {"n_runs": 1, "evidence_label": "single-run evidence"}
    rows = [
        {**base, "path_id": "A", "mean_cost_per_run_usd": 1.0,
         "frozen_v3": {"feasibility_rate": 0.5, "n_nonvoid": 1, "n_feasible": 1}},
        {**base, "path_id": "B", "mean_cost_per_run_usd": 1.0,
         "frozen_v3": {"feasibility_rate": 0.5, "n_nonvoid": 1, "n_feasible": 1}},
        {**base, "path_id": "C", "mean_cost_per_run_usd": 2.0,
         "frozen_v3": {"feasibility_rate": 0.4, "n_nonvoid": 1, "n_feasible": 0}},
        {**base, "path_id": "D", "mean_cost_per_run_usd": None,
         "frozen_v3": {"feasibility_rate": 1.0, "n_nonvoid": 1, "n_feasible": 1}},
    ]
    result = analysis.pareto(rows, "frozen_v3")
    assert [row["path_id"] for row in result["frontier"]] == ["A", "B"]
    assert result["excluded"] == [{"path_id": "D", "reason": "cost_not_estimable"}]


def test_counterfactual_direction_uses_frozen_five_percent_tolerance():
    assert analysis.direction(0.94, 1.0) == "alternative cheaper"
    assert analysis.direction(0.95, 1.0) == "tie"
    assert analysis.direction(1.05, 1.0) == "tie"
    assert analysis.direction(1.051, 1.0) == "alternative more expensive"
    assert analysis.direction(None, 1.0) is None


def test_naive_price_ordering_baseline_is_reported_on_same_counterfactual_pairs():
    result = analysis.build_analysis()
    summary = result["cost_counterfactual"]["summary"]
    naive = summary["naive_price_ordering_baseline"]
    assert summary["n_direction_matches"] == 29
    assert summary["n_direction_estimable"] == 32
    assert naive == {
        "n_direction_estimable": 50,
        "n_direction_matches": 42,
        "direction_match_rate": pytest.approx(0.84),
        "common_with_token_conversion_n": 32,
        "common_with_token_conversion_matches": 30,
    }
    assert result["cost_counterfactual"]["summary"]["frozen_router_feasibility_direction"] == {
        "n_estimable": 50, "n_matches": 22, "match_rate": pytest.approx(0.44)
    }
    assert analysis.naive_path_price_score("C-C-C", result["prices"]) < analysis.naive_path_price_score("A-A-A", result["prices"])


def test_router_conversion_and_counterfactual_labels_are_separate_from_actual_cost():
    result = analysis.build_analysis()
    sensitivity = result["router_cost_first_sensitivity"]
    counterfactual = result["cost_counterfactual"]
    assert "post-hoc conversion" in sensitivity["label"]
    assert "not a prospective" in sensitivity["label"]
    assert sensitivity["summary"]["n_traces"] == 20
    assert counterfactual["summary"]["n_pairs"] == 50
    assert "frozen Router never predicted dollars" in counterfactual["label"]
    assert all("candidate_conversions" in row for row in sensitivity["traces"])
    assert set(result["existing_router_sensitivity_posthoc"]["criteria"]) == {
        "frozen_v3", "feasibility_only", "strict_quality", "token_first", "maximum_reliability"
    }


def test_saved_outputs_are_reproducible_and_report_has_required_disclosures():
    result = analysis.build_analysis()
    assert result == json.loads(analysis.OUT.read_text())
    report = analysis.render_report(result)
    assert report == analysis.REPORT.read_text()
    assert report.startswith("# Workflow cost analysis — post-hoc / exploratory\n\n## Key findings")
    assert "retail_sales` is pilot-exposed" in report
    assert "single-run evidence" in report
    assert "Frozen v3 found 28/156" in report
    assert "post-hoc v3.1 found 38/156" in report
    assert "frozen Router never predicted dollars" in report
