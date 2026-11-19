from __future__ import annotations

import json

from experiments import analyze_cost_aware_router_posthoc as analysis
from src.bedrock.models import load_registry
from src.routing.config import load_routing_config
from src.routing.cost_posthoc import decide_cost_aware, estimate_stage_models_with_cost
from src.routing.data import build_training_view, load_records


def _store():
    return load_records([
        *analysis.read_jsonl(analysis.STAGE_RECORDS),
        *analysis.read_jsonl(analysis.WORKFLOW_RECORDS),
    ])


def test_cost_config_changes_only_identity_and_cost_metadata():
    frozen = load_routing_config(analysis.REPO / "configs/routing.yaml")
    cost = load_routing_config(analysis.CONFIG)
    assert cost.router_version != frozen.router_version
    assert cost.objective.objective_id != frozen.objective.objective_id
    assert cost.objective.min_feasibility_prob == frozen.objective.min_feasibility_prob
    assert [(q.stage, q.metric, q.op, q.threshold) for q in cost.objective.quality_constraints] == [
        (q.stage, q.metric, q.op, q.threshold) for q in frozen.objective.quality_constraints
    ]
    assert cost.objective.preference_order == frozen.objective.preference_order
    assert cost.objective.tie_tolerance == frozen.objective.tie_tolerance
    assert cost.settings == frozen.settings
    assert cost.interaction_shrinkage_k == frozen.interaction_shrinkage_k


def test_all_nonvoid_scope_includes_failed_records_and_strict_cost_is_estimable():
    store, registry = _store(), load_registry(analysis.MODELS)
    view = build_training_view(store, store.projects()[0])
    _, primary = estimate_stage_models_with_cost(view, registry, "all_non_void_executed")
    _, passed = estimate_stage_models_with_cost(view, registry, "passed_only")
    assert all(row["estimable"] for row in primary)
    assert any(p["n_eligible_records"] > s["n_eligible_records"] for p, s in zip(primary, passed))
    assert all(row["n_complete_usage_records"] == row["n_eligible_records"] for row in primary)


def test_s3_cost_is_additive_and_never_an_interaction():
    store, registry = _store(), load_registry(analysis.MODELS)
    view = build_training_view(store, store.projects()[0])
    cfg = load_routing_config(analysis.CONFIG)
    decisions, _ = decide_cost_aware(view, cfg, registry, "2026-11-19T00:00:00+00:00")
    s2, s3 = decisions["S2"][0], decisions["S3"][0]
    s2_by_path = {candidate.path_id: candidate for candidate in s2.candidates}
    assert all(candidate.cost_usd is not None for candidate in s3.candidates)
    for candidate in s3.candidates:
        assert "cost_usd" not in candidate.interaction_terms
        assert candidate.cost_usd == s2_by_path[candidate.path_id].cost_usd
        assert candidate.uncertainty["cost_usd"] == s2_by_path[candidate.path_id].uncertainty["cost_usd"]


def test_full_offline_driver_writes_separate_chains_and_audited_report(tmp_path):
    out = tmp_path / "routing"
    processed = tmp_path / "analysis.json"
    report = tmp_path / "report.md"
    result = analysis.build_analysis(out, processed, report)
    assert result["label"] == "post-hoc / exploratory"
    assert result["integrity_audit"]["status"] == "pass"
    assert result["integrity_audit"]["n_traces"] == 20
    assert result["integrity_audit"]["held_out_leakage_refs"] == 0
    assert result["integrity_audit"]["prediction_chain"]["ok"]
    assert result["integrity_audit"]["validation_chain"]["ok"]
    assert result["integrity_audit"]["n_predictions"] == result["integrity_audit"]["n_validations"]
    assert result["selection_comparison"]["summary"]["n_could_change"] + \
        result["selection_comparison"]["summary"]["n_no_feasible_frozen"] == 20
    assert set(result["selection_comparison"]["summary"]["change_causes"]) <= {
        "pareto_filter", "cost_preference", "downstream_or_tie_break"
    }
    assert result["faithfulness"]["claims_checked"] == result["faithfulness"]["claims_consistent"]
    assert result["faithfulness"]["replay_matches"] == 20
    assert result["coverage"]["primary"]["stage_cells"]["n_estimable"] == 108
    assert result["coverage"]["primary"]["stage_cells"]["n_required"] == 108
    assert result["coverage"]["primary"]["summary"]["n_candidate_cost_estimable"] == 228
    assert result["coverage"]["primary"]["summary"]["n_cost_preference_active"] == 8
    assert result["selection_comparison"]["summary"]["n_could_change"] == 8
    assert result["selection_comparison"]["summary"]["n_selection_changes"] == 1
    assert result["selection_comparison"]["summary"]["n_pareto_sets_changed"] == 1
    assert result["selection_comparison"]["summary"]["change_causes"] == {"cost_preference": 1}
    assert result["faithfulness"]["claims_checked"] == 421
    assert result["counterfactual_validity"]["summary"]["cost_direction"] == {"n": 50, "matches": 41}
    assert result["counterfactual_validity"]["summary"]["naive_price_ordering_same_subset"] == {
        "n": 50, "matches": 41
    }
    assert result["counterfactual_validity"]["summary"]["feasibility_direction"] == {
        "n": 50, "matches": 23
    }
    assert result["coverage"]["passed_only_sensitivity"]["stage_cells"]["n_estimable"] == 60
    assert result["coverage"]["passed_only_sensitivity"]["summary"]["n_candidate_cost_estimable"] == 0
    assert result["passed_only_sensitivity"]["summary"]["n_selection_changes_vs_primary"] == 1
    assert result["passed_only_sensitivity"]["label"] == "passed_only_cost_sensitivity"
    assert result["coverage"]["passed_only_sensitivity"]["scope"] == "passed_only_cost_sensitivity"
    assert (out / "counterfactual_predictions.jsonl.head").exists()
    assert (out / "counterfactual_validations.jsonl.head").exists()
    assert json.loads(processed.read_text())["integrity_audit"]["status"] == "pass"
    text = report.read_text()
    assert text.startswith("# Cost-aware Router — post-hoc / exploratory")
    assert "## Pareto versus preference effects" in text
    assert "60/108" in text
    assert "0/228" in text
    assert "Cost-complete" in text
    assert "single-run evidence" in text

