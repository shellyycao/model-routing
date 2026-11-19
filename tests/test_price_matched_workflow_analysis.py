"""Offline CP7f integrity, analysis, and post-hoc Router regressions."""

from __future__ import annotations

import json

import pytest

from experiments import analyze_price_matched_workflow_v3 as analysis


def loaded():
    return analysis.load_effective_records()


def test_integrity_audit_reconciles_records_invocations_ledger_and_reruns():
    stage, raw, effective, reruns, _ = loaded()
    audit = analysis.integrity_audit(stage, raw, effective, reruns)
    assert audit["status"] == "pass" and audit["errors"] == []
    assert audit["records"] == {
        "part_a": 36, "part_b_raw": 161, "part_b_original": 156,
        "part_b_reruns": 5, "part_b_effective": 156,
    }
    assert audit["invocations"] == {
        "all_including_pilot": 479, "main_record_linked": 470, "unlinked": 0,
    }
    assert audit["ledger"]["record_recomputed"]["spent_usd_priced"] == \
        pytest.approx(audit["ledger"]["saved"]["spent_usd_priced"])
    assert len(audit["rerun_resolution"]["replacements"]) == 5
    assert len(audit["rerun_resolution"]["original_void_records_retained_in_raw"]) == 5
    assert audit["parameters"]["parameter_counts"]["kimi_temperature_omitted"] == 139


def test_part_summaries_and_primary_replication_numbers():
    stage, _, effective, _, store = loaded()
    secondary = analysis._v31_outcomes(store)
    part_a = analysis.summarize_part_a(stage)
    part_b = analysis.summarize_part_b(effective, secondary)
    routing = analysis.summarize_primary_routing()
    assert len(part_a["rows"]) == 9
    assert part_b["main_grid"] == {"n": 108, "v3_feasible": 41, "v31_feasible": 53}
    assert part_b["single_model_main_grid"]["v3_feasible"] == 3
    assert part_b["cross_model_main_grid"]["v3_feasible"] == 38
    assert part_b["repeat_variability"]["v3_consistent_cells"] == 20
    assert part_b["repeat_variability"]["v31_consistent_cells"] == 20
    assert routing["faithfulness"] == {
        "claims_checked": 451, "claims_consistent": 451,
        "replay_matches": 20, "n_traces": 20,
    }
    assert routing["feasibility_direction"] == {
        "matches": 31, "n": 64, "rate": 31 / 64,
    }
    assert routing["held_out_evidence_references"] == 0


def test_cost_summary_has_complete_runs_denominators_and_pareto():
    _, _, effective, _, store = loaded()
    secondary = analysis._v31_outcomes(store)
    costs = analysis.summarize_costs(effective, secondary, analysis.protocol.registry(16384))
    assert costs["all_effective"]["n_runs"] == 156
    assert costs["all_effective"]["total_cost_usd"] == pytest.approx(23.2234954)
    assert costs["all_effective"]["v3"]["n_feasible"] == 61
    assert costs["all_effective"]["v31"]["n_feasible"] == 77
    assert len(costs["run_costs"]) == 156
    assert all(row["complete"] for row in costs["run_costs"])
    assert set(costs["pareto_frontiers"]) == {
        "customer_churn", "energy_consumption", "retail_sales", "support_operations"}


def test_cost_aware_router_is_separate_faithful_and_hash_chained(tmp_path):
    raw_hash = analysis.sha256(analysis.WORKFLOW_RECORDS)
    _, _, _, _, store = loaded()
    result = analysis.build_cost_aware(
        store, analysis.protocol.registry(16384), tmp_path / "cost-routing")
    assert analysis.sha256(analysis.WORKFLOW_RECORDS) == raw_hash
    assert result["label"] == "post-hoc / exploratory"
    assert result["integrity_audit"]["held_out_leakage_refs"] == 0
    assert result["integrity_audit"]["prediction_chain"]["ok"] is True
    assert result["integrity_audit"]["validation_chain"]["ok"] is True
    assert result["faithfulness"]["claims_checked"] == result["faithfulness"]["claims_consistent"]
    assert result["faithfulness"]["replay_matches"] == 20
    assert result["selection_comparison"]["summary"]["n_selection_changes"] == 7
    assert result["counterfactual_validity"]["summary"]["cost_direction"] == {
        "n": 64, "matches": 64}


def test_checked_in_summary_and_report_carry_required_disclosures():
    result = json.loads(analysis.OUT.read_text())
    report = analysis.REPORT.read_text()
    assert result["integrity_audit"]["status"] == "pass"
    assert result["scope"] == "these three specific models under this account"
    for text in ("these three specific models under this account", "maxTokens=16384",
                 "Kimi omitted", "Docker", "post-hoc / exploratory", "31/64", "22/50",
                 "Sonnet 4.6", "Kimi K3", "GLM 5", "64/64", "56/64",
                 "single-model paths were **3/12**", "cross-model paths **38/96**"):
        assert text in report


def test_final_report_contains_second_group_conclusion_section_and_verification():
    report = (analysis.REPO / "docs/FINAL_REPORT.md").read_text()
    assert "9. **The workflow/XAI finding replicated descriptively with a second model group.**" in report
    assert "### Replication with a second model group" in report
    assert "| 9. Replication with a second model group |" in report
    assert "**Evidence: pre-registered protocol; exploratory strength.**" in report
