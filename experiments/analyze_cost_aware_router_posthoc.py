"""CP6: offline post-hoc cost-aware S1--S3 routing and retrospective validation.

No Bedrock client is imported.  Frozen/raw inputs are read-only; every output is written to the
separate paths fixed in docs/COST_AWARE_ROUTER_RULES.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from src.bedrock.models import ModelRegistry, load_registry
from src.contracts import CounterfactualValidation, DecisionTrace, StageStatus, canonical_json
from src.explainability.explanations import render_explanation
from src.explainability.validation import check_faithfulness, summarise_validity, validate_prediction
from src.routing.config import load_routing_config
from src.routing.cost_posthoc import decide_cost_aware, record_cost_usd
from src.routing.counterfactual import HashChainLog, PredictionLog, generate_counterfactuals
from src.routing.data import build_training_view, load_records, read_jsonl

REPO = Path(__file__).resolve().parents[1]
STAGE_RECORDS = REPO / "results/raw/stage_benchmark/expA_stage_v3.jsonl"
WORKFLOW_RECORDS = REPO / "results/raw/workflow_runs/expB_paths_v3.jsonl"
V31 = REPO / "results/processed/v3_1_rescore/expB_paths_v3_reporting.json"
FROZEN_TRACES = REPO / "results/routing/v3_primary/traces.jsonl"
FROZEN_CONFIG = REPO / "configs/routing.yaml"
RULES = REPO / "docs/COST_AWARE_ROUTER_RULES.md"
CONFIG = REPO / "configs/routing_cost_posthoc.yaml"
MODELS = REPO / "configs/models.yaml"
OUT = REPO / "results/routing/v3_cost_posthoc"
PROCESSED = REPO / "results/processed/cost_aware_router_posthoc.json"
REPORT = REPO / "results/reports/cost_aware_router_posthoc.md"
SCRIPT = Path(__file__).resolve()
COST_MODULE = REPO / "src/routing/cost_posthoc.py"
PRED_LOG = "counterfactual_predictions.jsonl"
VAL_LOG = "counterfactual_validations.jsonl"
EPS = 1e-12
TOLERANCE = 0.05


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def source_hashes() -> dict[str, str]:
    paths = [STAGE_RECORDS, WORKFLOW_RECORDS, V31, FROZEN_TRACES, FROZEN_CONFIG,
             RULES, CONFIG, MODELS, SCRIPT, COST_MODULE]
    return {str(path.relative_to(REPO)): sha256(path) for path in paths}


def trace_key(trace: DecisionTrace | dict) -> tuple[str, str, str]:
    if isinstance(trace, DecisionTrace):
        return (trace.target_project, trace.strategy.value,
                str(trace.explanation_components.get("policy_path_id") or ""))
    return (trace["target_project"], trace["strategy"],
            str(trace.get("explanation_components", {}).get("policy_path_id") or ""))


def cost_direction(alternative: float | None, selected: float | None) -> str | None:
    if alternative is None or selected is None:
        return None
    delta = alternative - selected
    tolerance = TOLERANCE * abs(selected)
    if abs(delta) <= tolerance + EPS:
        return "tie"
    return "alternative cheaper" if delta < 0 else "alternative more expensive"


def naive_price_score(path_id: str, registry: ModelRegistry) -> float:
    return sum(
        registry.get(alias).pricing.input_per_mtok + registry.get(alias).pricing.output_per_mtok
        for alias in path_id.split("-")
    )


def _cost_step(trace: DecisionTrace):
    return next((step for step in trace.selection_steps
                 if step.rule == "lexicographic_preference" and step.detail.startswith("minimise cost_usd")), None)


def _pareto_step(trace: DecisionTrace):
    return next((step for step in trace.selection_steps if step.rule == "pareto_filter"), None)


def coverage_for(traces: list[DecisionTrace], cells: list[dict], scope: str) -> dict[str, Any]:
    scope_label = "passed_only_cost_sensitivity" if scope == "passed_only" else scope
    rows = []
    by_strategy: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for trace in traces:
        eligible = [candidate for candidate in trace.candidates if candidate.satisfies_constraints]
        cost_step = _cost_step(trace)
        pareto_step = _pareto_step(trace)
        row = {
            "trace_id": trace.trace_id,
            "target_project": trace.target_project,
            "strategy": trace.strategy.value,
            "scope": scope_label,
            "n_candidates": len(trace.candidates),
            "n_candidate_cost_estimable": sum(c.cost_usd is not None for c in trace.candidates),
            "n_constraint_eligible": len(eligible),
            "n_eligible_cost_estimable": sum(c.cost_usd is not None for c in eligible),
            "cost_pareto_dimension_active": bool(pareto_step and "cost_usd(min)" in pareto_step.detail),
            "cost_preference_step_present": cost_step is not None,
            "cost_preference_step_active": bool(cost_step and not cost_step.inactive),
            "has_selection": trace.selected_path_id is not None,
        }
        rows.append(row)
        bucket = by_strategy[trace.strategy.value]
        bucket["n_traces"] += 1
        bucket["n_candidates"] += row["n_candidates"]
        bucket["n_candidate_cost_estimable"] += row["n_candidate_cost_estimable"]
        bucket["n_constraint_eligible"] += row["n_constraint_eligible"]
        bucket["n_eligible_cost_estimable"] += row["n_eligible_cost_estimable"]
        bucket["n_cost_pareto_active"] += row["cost_pareto_dimension_active"]
        bucket["n_cost_preference_active"] += row["cost_preference_step_active"]
        bucket["n_with_selection"] += row["has_selection"]
    return {
        "scope": scope_label,
        "stage_cells": {
            "n_required": len(cells),
            "n_estimable": sum(cell["estimable"] for cell in cells),
            "rows": cells,
        },
        "trace_rows": rows,
        "by_strategy": {key: dict(value) for key, value in sorted(by_strategy.items())},
        "summary": {
            "n_traces": len(rows),
            "n_cost_pareto_active": sum(row["cost_pareto_dimension_active"] for row in rows),
            "n_cost_preference_active": sum(row["cost_preference_step_active"] for row in rows),
            "n_with_selection": sum(row["has_selection"] for row in rows),
            "n_no_feasible_path": sum(not row["has_selection"] for row in rows),
            "n_candidates": sum(row["n_candidates"] for row in rows),
            "n_candidate_cost_estimable": sum(row["n_candidate_cost_estimable"] for row in rows),
        },
    }


def actual_run_cost(run, registry: ModelRegistry) -> dict[str, Any]:
    if run.feasibility.outcome == "void_infra":
        return {"cost_usd": None, "complete": False, "reason": "void_infra", "stage_costs": []}
    total = 0.0
    stage_costs = []
    for stage in run.stages:
        if stage.status in (StageStatus.BLOCKED_BY_INVALID_ARTIFACT, StageStatus.NOT_RUN_UPSTREAM_FAILURE):
            stage_costs.append({"stage": stage.stage.value, "cost_usd": 0.0, "status": stage.status.value,
                                "basis": "not_incurred"})
            continue
        if stage.cache_hit:
            stage_costs.append({"stage": stage.stage.value, "cost_usd": 0.0, "status": stage.status.value,
                                "basis": "cache_hit_not_incurred"})
            continue
        cost = record_cost_usd(stage, stage.model_alias, registry)
        stage_costs.append({"stage": stage.stage.value, "cost_usd": cost, "status": stage.status.value,
                            "basis": "recorded_tokens" if cost is not None else "missing_usage_or_price"})
        if cost is None:
            return {"cost_usd": None, "complete": False, "reason": "executed_stage_cost_missing",
                    "stage_costs": stage_costs}
        total += cost
    return {"cost_usd": total, "complete": True, "reason": None, "stage_costs": stage_costs}


def v31_outcomes(store, v31: dict) -> dict[str, str]:
    rescored = {row["run_id"]: row for row in v31["records"]}
    outcomes = {}
    for run in store.workflow_runs:
        if run.feasibility.outcome == "void_infra":
            outcomes[run.run_id] = "void_infra"
            continue
        prior_pass = all(stage.status == StageStatus.PASSED for stage in run.stages[:2])
        report = rescored.get(run.run_id)
        report_pass = bool(report and report["v31_ground_truth"]["hard_pass"])
        outcomes[run.run_id] = "feasible" if prior_pass and report_pass else "infeasible"
    return outcomes


def actual_path_summary(store, project: str, path_id: str, registry: ModelRegistry,
                        secondary: dict[str, str]) -> dict[str, Any]:
    runs = sorted((run for run in store.workflow_runs
                   if run.project_id == project and run.path_id == path_id), key=lambda run: run.repeat_index)
    valid = [run for run in runs if run.feasibility.outcome != "void_infra"]
    cost_rows = {run.run_id: actual_run_cost(run, registry) for run in valid}
    complete = bool(valid) and all(row["complete"] for row in cost_rows.values())
    total = sum(row["cost_usd"] for row in cost_rows.values()) if complete else None
    v3_feasible = sum(run.feasibility.outcome == "feasible" for run in valid)
    v31_feasible = sum(secondary[run.run_id] == "feasible" for run in valid)
    return {
        "project_id": project,
        "path_id": path_id,
        "n_runs": len(runs),
        "n_nonvoid": len(valid),
        "n_void": len(runs) - len(valid),
        "n_cost_complete": sum(row["complete"] for row in cost_rows.values()),
        "total_cost_usd": total,
        "mean_cost_usd": total / len(valid) if total is not None and valid else None,
        "cost_per_feasible_v3_usd": total / v3_feasible if total is not None and v3_feasible else None,
        "cost_per_feasible_v31_usd": total / v31_feasible if total is not None and v31_feasible else None,
        "v3": {"n_feasible": v3_feasible, "n_nonvoid": len(valid),
               "feasibility_rate": v3_feasible / len(valid) if valid else None},
        "v31": {"n_feasible": v31_feasible, "n_nonvoid": len(valid),
                "feasibility_rate": v31_feasible / len(valid) if valid else None},
        "evidence_label": "single-run evidence" if len(valid) == 1 else "repeated evidence",
        "run_costs": [{"run_id": run.run_id, "repeat_index": run.repeat_index,
                       "v3_outcome": run.feasibility.outcome, "v31_outcome": secondary[run.run_id],
                       **cost_rows[run.run_id]} for run in valid],
    }


def validate_with_cost(pred, store, registry: ModelRegistry, validated_at: str) -> CounterfactualValidation:
    runs = store.retrospective_outcomes(pred.held_out_project)
    base = validate_prediction(pred, runs, validated_at)
    selected_runs = [run for run in runs if run.path_id == pred.selected_path_id
                     and run.feasibility.outcome != "void_infra"]
    alternative_runs = [run for run in runs if run.path_id == pred.alternative_path_id
                        and run.feasibility.outcome != "void_infra"]

    def costs(rows):
        values = [(run.repeat_index, actual_run_cost(run, registry)) for run in rows]
        complete = bool(values) and all(value["complete"] for _, value in values)
        return values, (mean(value["cost_usd"] for _, value in values) if complete else None)

    selected_values, selected_cost = costs(selected_runs)
    alternative_values, alternative_cost = costs(alternative_runs)
    actual_selected = {**base.actual_selected, "cost_usd": selected_cost}
    actual_alternative = {**base.actual_alternative, "cost_usd": alternative_cost}
    actual_delta = {**base.actual_delta, "cost_usd": (
        alternative_cost - selected_cost if alternative_cost is not None and selected_cost is not None else None)}
    predicted_delta = pred.predicted_delta.get("cost_usd")
    actual_cost_delta = actual_delta["cost_usd"]
    abs_error = {**base.abs_error, "cost_usd": (
        abs(predicted_delta - actual_cost_delta)
        if predicted_delta is not None and actual_cost_delta is not None else None)}
    predicted_direction = cost_direction(pred.predicted_alternative.get("cost_usd"),
                                         pred.predicted_selected.get("cost_usd"))
    actual_direction = cost_direction(alternative_cost, selected_cost)
    direction = {**base.direction_correct,
                 "cost_usd": (predicted_direction == actual_direction
                              if predicted_direction is not None and actual_direction is not None else None)}
    interval = pred.predicted_delta_interval.get("cost_usd")
    coverage = {**base.interval_covers_actual, "cost_usd": (
        interval[0] - EPS <= actual_cost_delta <= interval[1] + EPS
        if interval is not None and actual_cost_delta is not None else None)}
    selected_by_repeat = {repeat: row["cost_usd"] for repeat, row in selected_values if row["complete"]}
    alternative_by_repeat = {repeat: row["cost_usd"] for repeat, row in alternative_values if row["complete"]}
    common = sorted(set(selected_by_repeat) & set(alternative_by_repeat))
    deltas = [alternative_by_repeat[index] - selected_by_repeat[index] for index in common]
    spread = {**base.actual_delta_spread,
              "cost_usd": (min(deltas), max(deltas)) if len(deltas) >= 2 else None}
    result = CounterfactualValidation(
        **{
            **base.model_dump(mode="python"),
            "actual_selected": actual_selected,
            "actual_alternative": actual_alternative,
            "actual_delta": actual_delta,
            "actual_delta_spread": spread,
            "abs_error": abs_error,
            "direction_correct": direction,
            "interval_covers_actual": coverage,
            "notes": "; ".join(filter(None, [base.notes,
                "cost direction uses 5% relative tolerance; executed cost includes failed non-void stages"])),
        }
    )
    result.check_against(pred)
    return result


def classify_selection_changes(primary: list[DecisionTrace], frozen: list[DecisionTrace]) -> dict[str, Any]:
    frozen_by_key = {trace_key(trace): trace for trace in frozen}
    rows = []
    for trace in primary:
        old = frozen_by_key[trace_key(trace)]
        changed = old.selected_path_id != trace.selected_path_id
        cause = None
        if changed and old.selected_path_id is not None:
            pareto = _pareto_step(trace)
            cost = _cost_step(trace)
            if pareto and old.selected_path_id in pareto.removed:
                cause = "pareto_filter"
            elif cost and old.selected_path_id in cost.removed:
                cause = "cost_preference"
            else:
                cause = "downstream_or_tie_break"
        rows.append({
            "target_project": trace.target_project,
            "strategy": trace.strategy.value,
            "policy_path_id": trace.explanation_components.get("policy_path_id"),
            "frozen_trace_id": old.trace_id,
            "cost_trace_id": trace.trace_id,
            "frozen_selected_path_id": old.selected_path_id,
            "cost_selected_path_id": trace.selected_path_id,
            "could_change": old.selected_path_id is not None,
            "selection_changed": changed,
            "selection_change_cause": cause,
            "pareto_set_changed": set(old.pareto_path_ids) != set(trace.pareto_path_ids),
            "frozen_pareto_path_ids": old.pareto_path_ids,
            "cost_pareto_path_ids": trace.pareto_path_ids,
            "cost_preference_active": bool(_cost_step(trace) and not _cost_step(trace).inactive),
        })
    possible = [row for row in rows if row["could_change"]]
    changes = [row for row in rows if row["selection_changed"]]
    return {
        "rows": rows,
        "summary": {
            "n_traces": len(rows),
            "n_no_feasible_frozen": sum(not row["could_change"] for row in rows),
            "n_could_change": len(possible),
            "n_selection_changes": len(changes),
            "n_changes_among_could_change": len(changes),
            "n_pareto_sets_changed": sum(row["pareto_set_changed"] for row in rows),
            "change_causes": dict(sorted(Counter(row["selection_change_cause"] for row in changes).items())),
        },
    }


def counterfactual_summary(predictions, validations, registry: ModelRegistry) -> dict[str, Any]:
    rows = []
    for pred, validation in zip(predictions, validations):
        predicted_direction = cost_direction(pred.predicted_alternative.get("cost_usd"),
                                             pred.predicted_selected.get("cost_usd"))
        actual_direction = cost_direction(validation.actual_alternative.get("cost_usd"),
                                          validation.actual_selected.get("cost_usd"))
        naive_direction = cost_direction(naive_price_score(pred.alternative_path_id, registry),
                                         naive_price_score(pred.selected_path_id, registry))
        rows.append({
            "prediction_id": pred.prediction_id,
            "strategy": pred.strategy.value,
            "held_out_project": pred.held_out_project,
            "selected_path_id": pred.selected_path_id,
            "alternative_path_id": pred.alternative_path_id,
            "predicted_cost_direction": predicted_direction,
            "actual_cost_direction": actual_direction,
            "cost_direction_match": (predicted_direction == actual_direction
                                     if predicted_direction and actual_direction else None),
            "naive_price_direction": naive_direction,
            "naive_direction_match": (naive_direction == actual_direction if actual_direction else None),
            "feasibility_direction_match": validation.direction_correct.get("feasible"),
        })
    estimable = [row for row in rows if row["cost_direction_match"] is not None]
    naive = [row for row in rows if row["naive_direction_match"] is not None]
    feasibility = [row for row in rows if row["feasibility_direction_match"] is not None]
    by_strategy = {}
    for strategy in sorted({row["strategy"] for row in rows}):
        subset = [row for row in rows if row["strategy"] == strategy]
        cost_rows = [row for row in subset if row["cost_direction_match"] is not None]
        feas_rows = [row for row in subset if row["feasibility_direction_match"] is not None]
        by_strategy[strategy] = {
            "n_predictions": len(subset),
            "cost_direction": {"n": len(cost_rows), "matches": sum(r["cost_direction_match"] for r in cost_rows)},
            "feasibility_direction": {"n": len(feas_rows), "matches": sum(r["feasibility_direction_match"] for r in feas_rows)},
        }
    return {
        "rows": rows,
        "summary": {
            "n_predictions": len(rows),
            "cost_direction": {"n": len(estimable), "matches": sum(row["cost_direction_match"] for row in estimable)},
            "naive_price_ordering_same_subset": {"n": len(naive), "matches": sum(row["naive_direction_match"] for row in naive)},
            "feasibility_direction": {"n": len(feasibility), "matches": sum(row["feasibility_direction_match"] for row in feasibility)},
        },
        "by_strategy": by_strategy,
    }


def render_report(result: dict[str, Any]) -> str:
    selection = result["selection_comparison"]["summary"]
    coverage = result["coverage"]["primary"]["summary"]
    faith = result["faithfulness"]
    cf = result["counterfactual_validity"]["summary"]
    sensitivity = result["passed_only_sensitivity"]["summary"]
    sensitivity_coverage = result["coverage"]["passed_only_sensitivity"]
    sensitivity_cost = sensitivity_coverage["summary"]
    change_causes = selection["change_causes"]
    lines = [
        "# Cost-aware Router — post-hoc / exploratory", "", "## Key findings", "",
        f"- Frozen feasibility/quality constraints left {selection['n_could_change']}/{selection['n_traces']} traces with a selected path that could possibly change; {selection['n_no_feasible_frozen']}/{selection['n_traces']} no-feasible-path traces could not change.",
        f"- Activating direct cost changed {selection['n_selection_changes']}/{selection['n_could_change']} selectable traces ({selection['n_selection_changes']}/{selection['n_traces']} overall).",
        f"- Cost entered the Pareto filter in {coverage['n_cost_pareto_active']}/{coverage['n_traces']} traces and the cost preference was active in {coverage['n_cost_preference_active']}/{coverage['n_traces']}; {change_causes.get('cost_preference', 0)} selection change arose at the preference step and {change_causes.get('pareto_filter', 0)} at the Pareto filter.",
        f"- Template faithfulness was {faith['claims_consistent']}/{faith['claims_checked']} claims with {faith['replay_matches']}/{faith['n_traces']} replay matches.",
        f"- Counterfactual cost direction matched {cf['cost_direction']['matches']}/{cf['cost_direction']['n']} estimable pairs; the naive unit-price baseline matched {cf['naive_price_ordering_same_subset']['matches']}/{cf['naive_price_ordering_same_subset']['n']} on that subset. Feasibility direction matched {cf['feasibility_direction']['matches']}/{cf['feasibility_direction']['n']}.",
        "", "## Scope and method", "",
        "This is a **post-hoc / exploratory** rerun of S1–S3 over saved prospective-v3 records. It changes only the availability of `cost_usd`: constraints, LOPO folds, Pareto rules, preference order, tolerance, non-cost estimators and trace machinery remain fixed. Primary cost uses every fresh PASSED or FAILED non-void Experiment A record; PASSED-only is a sensitivity. S3 cost is additive and has no cost interaction term.",
        "", "## Coverage", "",
        f"Primary stage-cell coverage was {result['coverage']['primary']['stage_cells']['n_estimable']}/{result['coverage']['primary']['stage_cells']['n_required']}. Candidate cost coverage was {coverage['n_candidate_cost_estimable']}/{coverage['n_candidates']}. The cost preference was active in {coverage['n_cost_preference_active']}/{coverage['n_traces']} traces; {coverage['n_no_feasible_path']}/{coverage['n_traces']} stopped before any preference step because no candidate satisfied the frozen constraints.",
        "", "| Strategy | Traces | Candidate cost | Eligible cost | Cost Pareto active | Cost preference active | Selected |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for strategy, row in result["coverage"]["primary"]["by_strategy"].items():
        lines.append(f"| {strategy} | {row['n_traces']} | {row['n_candidate_cost_estimable']}/{row['n_candidates']} | {row['n_eligible_cost_estimable']}/{row['n_constraint_eligible']} | {row['n_cost_pareto_active']}/{row['n_traces']} | {row['n_cost_preference_active']}/{row['n_traces']} | {row['n_with_selection']}/{row['n_traces']} |")
    lines += ["", "The earlier CP4b 8/20 figure was selection estimability after frozen constraint gating plus a total-token conversion. This variant prices input/output tokens directly, but unchanged constraints still prevent no-feasible-path traces from reaching cost selection.",
              "", "## Selection comparison", "",
              "| Project | Strategy/policy | Frozen | Cost-aware | Changed | Cause |", "|---|---|---|---|---:|---|"]
    for row in result["selection_comparison"]["rows"]:
        label = row["strategy"] + (f" / {row['policy_path_id']}" if row["policy_path_id"] else "")
        lines.append(f"| {row['target_project']} | {label} | {row['frozen_selected_path_id'] or 'no feasible path'} | {row['cost_selected_path_id'] or 'no feasible path'} | {'yes' if row['selection_changed'] else 'no'} | {row['selection_change_cause'] or '—'} |")
    lines += ["", "## Pareto versus preference effects", "",
              f"Cost changed the Pareto set in {selection['n_pareto_sets_changed']}/{selection['n_traces']} traces. Among the {selection['n_selection_changes']} selection changes, {change_causes.get('pareto_filter', 0)} first removed the frozen selection at the Pareto filter and {change_causes.get('cost_preference', 0)} first removed it at the explicit cost preference. A `pareto_filter` cause means the cost dimension removed the old selection before lexicographic preferences; a `cost_preference` cause means it survived the Pareto set and was removed at the explicit cost step.",
              "", "## Executed outcomes and cost per feasible completion", "",
              "| Project | Strategy/policy | Selected path | Cost-complete | v3 feasible | v3.1 feasible | Mean actual cost | Cost/feasible v3 | Cost/feasible v3.1 | Evidence |",
              "|---|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for row in result["selected_path_outcomes"]:
        label = row["strategy"] + (f" / {row['policy_path_id']}" if row["policy_path_id"] else "")
        outcome = row.get("executed")
        if outcome is None:
            lines.append(f"| {row['target_project']} | {label} | no feasible path | — | — | — | — | not estimable | not estimable | no selection |")
            continue
        money = lambda value: "not estimable" if value is None else f"${value:.4f}"
        lines.append(f"| {row['target_project']} | {label} | {row['selected_path_id']} | {outcome['n_cost_complete']}/{outcome['n_nonvoid']} | {outcome['v3']['n_feasible']}/{outcome['v3']['n_nonvoid']} | {outcome['v31']['n_feasible']}/{outcome['v31']['n_nonvoid']} | {money(outcome['mean_cost_usd'])} | {money(outcome['cost_per_feasible_v3_usd'])} | {money(outcome['cost_per_feasible_v31_usd'])} | {outcome['evidence_label']} |")
    lines += ["", "Actual spend includes failed non-void stages and genuinely excludes blocked/not-run calls. A zero-success denominator is reported as `not estimable`.",
              "", "## Computational faithfulness", "",
              f"Observed template checks: **{faith['claims_consistent']}/{faith['claims_checked']}** claims consistent; replay reproduced **{faith['replay_matches']}/{faith['n_traces']}** selections. These are measurements of the new traces, not an assumption inherited from the frozen run.",
              "", "## Counterfactual validity", "",
              "| Strategy | Predictions | Cost direction | Feasibility direction |", "|---|---:|---:|---:|"]
    for strategy, row in result["counterfactual_validity"]["by_strategy"].items():
        lines.append(f"| {strategy} | {row['n_predictions']} | {row['cost_direction']['matches']}/{row['cost_direction']['n']} | {row['feasibility_direction']['matches']}/{row['feasibility_direction']['n']} |")
    lines += ["", f"Overall cost direction was {cf['cost_direction']['matches']}/{cf['cost_direction']['n']}; the naive unit-price ordering baseline was {cf['naive_price_ordering_same_subset']['matches']}/{cf['naive_price_ordering_same_subset']['n']} on the same executed-cost-comparable pairs. This baseline is essential because A/B/C unit prices differ greatly.",
              "", "## PASSED-only sensitivity", "",
              f"Changing only the cost record scope from all non-void executed records to PASSED-only changed {sensitivity['n_selection_changes_vs_primary']}/{sensitivity['n_primary_selected']} primary selections with a selected path. Only {sensitivity_coverage['stage_cells']['n_estimable']}/{sensitivity_coverage['stage_cells']['n_required']} stage/model/fold cells had PASSED records with complete usage. Under the pre-specified strict completeness rule this left {sensitivity_cost['n_candidate_cost_estimable']}/{sensitivity_cost['n_candidates']} complete candidate-path estimates and therefore {sensitivity['n_cost_preference_active']}/{sensitivity['n_traces']} active cost steps; the sensitivity falls back to the frozen non-cost logic when a candidate cost is incomplete.",
              "", "| Project | Strategy/policy | Primary | PASSED-only | Changed | First cause |",
              "|---|---|---|---|---:|---|"]
    for row in result["passed_only_sensitivity"]["rows"]:
        if not row["selection_changed"]:
            continue
        label = row["strategy"] + (f" / {row['policy_path_id']}" if row["policy_path_id"] else "")
        lines.append(f"| {row['target_project']} | {label} | {row['frozen_selected_path_id'] or 'no feasible path'} | {row['cost_selected_path_id'] or 'no feasible path'} | yes | {row['selection_change_cause'] or '—'} |")
    lines += ["", "## Limitations", "",
              "- All outcomes preceded this variant; the result is post-hoc and not prospective evidence.",
              "- Most selected path/project cells have one executed run and are labelled `single-run evidence`.",
              "- Additive cost intentionally does not model cross-stage token interactions and does not reward early blocking.",
              "- Selection and counterfactual claims apply only to these three models, four synthetic projects, verified prices, and this account's saved records.",
              "- A lower attempted-run cost must be read beside feasibility and cost per feasible completion.", ""]
    return "\n".join(lines)


def build_analysis(out: Path = OUT, processed: Path = PROCESSED, report: Path = REPORT) -> dict[str, Any]:
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty cost-aware output directory {out}")
    out.mkdir(parents=True, exist_ok=True)
    registry = load_registry(MODELS)
    cfg = load_routing_config(CONFIG)
    store = load_records([*read_jsonl(STAGE_RECORDS), *read_jsonl(WORKFLOW_RECORDS)])
    created_at = max(run.finished_at or run.started_at for run in store.workflow_runs)
    frozen = [DecisionTrace.model_validate(row) for row in read_jsonl(FROZEN_TRACES)]

    primary_traces: list[DecisionTrace] = []
    sensitivity_traces: list[DecisionTrace] = []
    primary_cells, sensitivity_cells = [], []
    fold_rows = []
    for project in store.projects():
        view = build_training_view(store, project)
        decisions, cells = decide_cost_aware(view, cfg, registry, created_at, "all_non_void_executed")
        sensitivity, sens_cells = decide_cost_aware(view, cfg, registry, created_at, "passed_only")
        fold_primary = [trace for traces in decisions.values() for trace in traces]
        fold_sensitivity = [trace for traces in sensitivity.values() for trace in traces]
        primary_traces.extend(fold_primary)
        sensitivity_traces.extend(fold_sensitivity)
        primary_cells.extend(cells)
        sensitivity_cells.extend(sens_cells)
        fold_rows.append({"held_out_project": project, "training_projects": list(view.training_projects),
                          "n_primary_traces": len(fold_primary), "n_sensitivity_traces": len(fold_sensitivity)})

    write_jsonl(out / "traces.jsonl", [trace.model_dump(mode="json") for trace in primary_traces])
    write_jsonl(out / "passed_only_traces.jsonl", [trace.model_dump(mode="json") for trace in sensitivity_traces])
    explanations, faithfulness = [], []
    prediction_log = PredictionLog(out / PRED_LOG)
    prediction_notes = []
    for trace in primary_traces:
        explanation = render_explanation(trace)
        check = check_faithfulness(trace, explanation, created_at)
        explanations.append(explanation.to_dict())
        faithfulness.append(check.model_dump(mode="json"))
        predictions, notes = generate_counterfactuals(trace, created_at)
        for prediction in predictions:
            prediction_log.append_prediction(prediction)
        prediction_notes.append({"trace_id": trace.trace_id, "notes": notes})
    write_jsonl(out / "explanations.jsonl", explanations)
    write_jsonl(out / "computational_faithfulness.jsonl", faithfulness)
    prediction_chain = prediction_log.verify()
    coverage = {
        "label": "post-hoc / exploratory",
        "primary": coverage_for(primary_traces, primary_cells, "all_non_void_executed"),
        "passed_only_sensitivity": coverage_for(sensitivity_traces, sensitivity_cells, "passed_only"),
    }
    (out / "cost_coverage.json").write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")
    hashes = source_hashes()
    predict_manifest = {
        "label": "post-hoc / exploratory",
        "rules_version": "cost-aware-router-posthoc-1.0",
        "router_version": cfg.router_version,
        "config_hash": cfg.config_hash,
        "created_at": created_at,
        "source_hashes": hashes,
        "folds": fold_rows,
        "n_traces": len(primary_traces),
        "n_explanations": len(explanations),
        "n_faithfulness_checks": len(faithfulness),
        "prediction_chain": {"ok": prediction_chain.ok, "n_lines": prediction_chain.n_lines,
                             "head": prediction_chain.head, "errors": prediction_chain.errors},
        "prediction_notes": prediction_notes,
    }
    (out / "predict_manifest.json").write_text(json.dumps(predict_manifest, indent=2, sort_keys=True) + "\n")

    # Retrospective phase starts only after the prediction log and manifest are durable and verified.
    if not prediction_chain.ok:
        raise ValueError(f"prediction chain failed before validation: {prediction_chain.errors}")
    predictions = prediction_log.predictions()
    validation_log = HashChainLog(out / VAL_LOG)
    validations = []
    for prediction in predictions:
        validation = validate_with_cost(prediction, store, registry, created_at)
        validation_log.append(validation.model_dump(mode="json"))
        validations.append(validation)
    validation_chain = validation_log.verify()
    if not validation_chain.ok:
        raise ValueError(f"validation chain failed: {validation_chain.errors}")
    validity_summary = summarise_validity(predictions, validations)
    validation_manifest = {
        "label": "post-hoc / exploratory",
        "validated_at": created_at,
        "source_hashes": hashes,
        "prediction_chain_head": prediction_chain.head,
        "n_validations": len(validations),
        "validation_chain": {"ok": validation_chain.ok, "n_lines": validation_chain.n_lines,
                             "head": validation_chain.head, "errors": validation_chain.errors},
        "by_strategy": validity_summary,
    }
    (out / "validation_manifest.json").write_text(json.dumps(validation_manifest, indent=2, sort_keys=True) + "\n")

    secondary = v31_outcomes(store, json.loads(V31.read_text()))
    selection = classify_selection_changes(primary_traces, frozen)
    sensitivity_selection = classify_selection_changes(sensitivity_traces, primary_traces)
    primary_by_key = {trace_key(trace): trace for trace in primary_traces}
    selected_outcomes = []
    for row in selection["rows"]:
        trace = primary_by_key[(row["target_project"], row["strategy"], str(row["policy_path_id"] or ""))]
        selected_outcomes.append({
            "target_project": trace.target_project,
            "strategy": trace.strategy.value,
            "policy_path_id": trace.explanation_components.get("policy_path_id"),
            "selected_path_id": trace.selected_path_id,
            "executed": (actual_path_summary(store, trace.target_project, trace.selected_path_id, registry, secondary)
                         if trace.selected_path_id else None),
        })
    counterfactual = counterfactual_summary(predictions, validations, registry)
    faith_summary = {
        "n_traces": len(faithfulness),
        "claims_checked": sum(row["claims_checked"] for row in faithfulness),
        "claims_consistent": sum(row["claims_consistent"] for row in faithfulness),
        "replay_matches": sum(row["replay_matches_selection"] is True for row in faithfulness),
        "n_inconsistent_checks": sum(len(row["inconsistencies"]) for row in faithfulness),
    }
    sens_rows = sensitivity_selection["rows"]
    passed_only = {
        "label": "passed_only_cost_sensitivity",
        "rows": sens_rows,
        "summary": {
            "n_traces": len(sens_rows),
            "n_primary_selected": sum(row["could_change"] for row in sens_rows),
            "n_selection_changes_vs_primary": sum(row["selection_changed"] for row in sens_rows),
            "n_cost_preference_active": coverage["passed_only_sensitivity"]["summary"]["n_cost_preference_active"],
        },
    }
    result = {
        "analysis_version": "cost-aware-router-posthoc-1.0",
        "analysis_date": "2026-11-19",
        "label": "post-hoc / exploratory",
        "rules_version": "cost-aware-router-posthoc-1.0",
        "router_version": cfg.router_version,
        "config_hash": cfg.config_hash,
        "source_hashes": hashes,
        "integrity_audit": {
            "status": "pass",
            "frozen_inputs_modified": False,
            "n_traces": len(primary_traces),
            "n_unique_trace_ids": len({trace.trace_id for trace in primary_traces}),
            "held_out_leakage_refs": sum(
                evidence.project_id == trace.held_out_project
                for trace in primary_traces for candidate in trace.candidates for evidence in candidate.evidence),
            "prediction_chain": predict_manifest["prediction_chain"],
            "validation_chain": validation_manifest["validation_chain"],
            "n_predictions": len(predictions),
            "n_validations": len(validations),
        },
        "coverage": coverage,
        "selection_comparison": selection,
        "selected_path_outcomes": selected_outcomes,
        "faithfulness": faith_summary,
        "counterfactual_validity": counterfactual,
        "empirical_validity_contract_summary": validity_summary,
        "passed_only_sensitivity": passed_only,
        "limitations": [
            "All outcomes preceded this post-hoc variant.",
            "Most path/project cells are single-run evidence.",
            "Cost is additive for S3 and does not model cross-stage token interactions.",
            "No provider-wide or deployability claim is supported.",
        ],
    }
    if result["integrity_audit"]["held_out_leakage_refs"] or not prediction_chain.ok or not validation_chain.ok:
        raise ValueError(f"integrity audit failed: {result['integrity_audit']}")
    processed.parent.mkdir(parents=True, exist_ok=True)
    processed.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(result))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--processed", default=str(PROCESSED))
    parser.add_argument("--report", default=str(REPORT))
    args = parser.parse_args(argv)
    result = build_analysis(Path(args.out), Path(args.processed), Path(args.report))
    print(json.dumps({
        "label": result["label"],
        "integrity": result["integrity_audit"]["status"],
        "traces": result["integrity_audit"]["n_traces"],
        "selection_changes": result["selection_comparison"]["summary"]["n_selection_changes"],
        "predictions": result["integrity_audit"]["n_predictions"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

