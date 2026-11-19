"""Offline post-hoc workflow cost analysis under locked CP4b rules."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

from src.contracts import CounterfactualPrediction, CounterfactualValidation, DecisionTrace
from src.contracts.records import WorkflowRunRecord
from src.routing.counterfactual import HashChainLog, PredictionLog

REPO = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO / "results/raw/workflow_runs/expB_paths_v3.jsonl"
INVOCATIONS = REPO / "results/raw/invocations.jsonl"
STAGE_RECORDS = REPO / "results/raw/stage_benchmark/expA_stage_v3.jsonl"
V31 = REPO / "results/processed/v3_1_rescore/expB_paths_v3_reporting.json"
TRACES = REPO / "results/routing/v3_primary/traces.jsonl"
PREDICTIONS = REPO / "results/routing/v3_primary/counterfactual_predictions.jsonl"
VALIDATIONS = REPO / "results/routing/v3_primary/counterfactual_validations.jsonl"
MODELS = REPO / "configs/models.yaml"
RULES = REPO / "docs/POSTHOC_WORKFLOW_COST_RULES.md"
EXISTING_ROUTER_SENSITIVITY = REPO / "results/processed/router_sensitivity_posthoc.json"
LEDGERS = (
    REPO / "results/raw/ledgers/expB_paths_v3_20261118T050708Z.json",
    REPO / "results/raw/ledgers/expB_paths_v3_20261118T063523Z.json",
)
OUT = REPO / "results/processed/workflow_cost_posthoc.json"
REPORT = REPO / "results/reports/workflow_cost_posthoc.md"
STAGES = ("cleaning", "analysis", "reporting")
TIE_TOLERANCE = 0.05


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_prices() -> dict[str, dict[str, Any]]:
    config = yaml.safe_load(MODELS.read_text())
    prices = {}
    for alias in ("A", "B", "C"):
        row = config["models"][alias]
        pricing = row["pricing"]
        if pricing["retrieved"] != "2026-11-18" or pricing["input_per_mtok"] is None or pricing["output_per_mtok"] is None:
            raise ValueError(f"unverified frozen price for {alias}")
        prices[alias] = {
            "name": row["name"], "model_id": row["model_id"],
            "input_per_mtok": float(pricing["input_per_mtok"]),
            "output_per_mtok": float(pricing["output_per_mtok"]),
            "source": pricing["source"], "retrieved": pricing["retrieved"],
        }
    return prices


def token_cost(alias: str, input_tokens: float, output_tokens: float, prices: dict[str, dict]) -> float:
    p = prices[alias]
    return (input_tokens * p["input_per_mtok"] + output_tokens * p["output_per_mtok"]) / 1_000_000


def _primary_id(invocation_ids: list[str]) -> list[str]:
    return [invocation_id for invocation_id in invocation_ids if not invocation_id.endswith(":parse")]


def build_run_costs(
    workflow_rows: list[dict[str, Any]], invocation_rows: list[dict[str, Any]], prices: dict[str, dict]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    inv_by_id = {row["invocation_id"]: row for row in invocation_rows}
    used_primary: set[str] = set()
    errors: list[str] = []
    run_costs = []
    for run in workflow_rows:
        known_cost = 0.0
        known_input = known_output = attempts = failed_attempts = missing_attempts = 0
        stage_rows = []
        for stage in run["stages"]:
            primary_ids = _primary_id(stage["invocation_ids"])
            if stage["status"] in {"blocked_by_invalid_artifact", "not_run_upstream_failure"}:
                if primary_ids:
                    errors.append(f"{run['run_id']}:{stage['stage']} blocked/not-run but has invocation")
                stage_rows.append({"stage": stage["stage"], "model_alias": stage["model_alias"],
                                   "status": stage["status"], "attempts": 0, "cost_usd": 0.0,
                                   "cost_status": "not_incurred"})
                continue
            if stage["cache_hit"]:
                stage_rows.append({"stage": stage["stage"], "model_alias": stage["model_alias"],
                                   "status": stage["status"], "attempts": 0, "cost_usd": 0.0,
                                   "cost_status": "not_incurred_cache_hit"})
                continue
            if len(primary_ids) != 1 or primary_ids[0] not in inv_by_id:
                errors.append(f"{run['run_id']}:{stage['stage']} primary invocation unresolved")
                missing_attempts += 1
                stage_rows.append({"stage": stage["stage"], "model_alias": stage["model_alias"],
                                   "status": stage["status"], "attempts": None, "cost_usd": None,
                                   "cost_status": "missing_invocation"})
                continue
            inv = inv_by_id[primary_ids[0]]
            used_primary.add(inv["invocation_id"])
            context = inv["context"]
            if (context["experiment_id"], context["run_id"], context["project_id"], context["path_id"],
                context["stage_id"], context["repeat_index"], inv["model_alias"], inv["model_id"]) != (
                "expB_paths_v3", run["run_id"], run["project_id"], run["path_id"], stage["stage"],
                run["repeat_index"], stage["model_alias"], stage["model_id"]):
                errors.append(f"{run['run_id']}:{stage['stage']} invocation context mismatch")
            if (stage["input_tokens"], stage["output_tokens"]) != (inv["input_tokens"], inv["output_tokens"]):
                errors.append(f"{run['run_id']}:{stage['stage']} token mismatch")
            retry_count = len(inv.get("attempts") or [])
            # No v3 retry has unknown usage. If one appears, refuse to invent per-run usage;
            # the rules require an exact reservation reconstruction before results can be released.
            if retry_count:
                missing_attempts += retry_count
            final_known = inv.get("input_tokens") is not None and inv.get("output_tokens") is not None
            if not final_known:
                missing_attempts += 1
                stage_cost = None
            else:
                stage_cost = token_cost(inv["model_alias"], inv["input_tokens"], inv["output_tokens"], prices)
                known_cost += stage_cost
                known_input += inv["input_tokens"]
                known_output += inv["output_tokens"]
            attempts += 1 + retry_count
            failed_attempts += retry_count + (0 if inv["status"] == "success" else 1)
            stage_rows.append({"stage": stage["stage"], "model_alias": stage["model_alias"],
                               "status": stage["status"], "attempts": 1 + retry_count,
                               "failed_attempts": retry_count, "input_tokens": inv["input_tokens"],
                               "output_tokens": inv["output_tokens"], "cost_usd": stage_cost,
                               "cost_status": "complete_known_usage" if stage_cost is not None else "incomplete"})
        complete = missing_attempts == 0
        run_costs.append({
            "run_id": run["run_id"], "project_id": run["project_id"], "path_id": run["path_id"],
            "repeat_index": run["repeat_index"], "frozen_v3_outcome": run["feasibility"]["outcome"],
            "cost_usd": known_cost if complete else None, "known_partial_spend_usd": known_cost,
            "cost_complete": complete, "input_tokens_known": known_input, "output_tokens_known": known_output,
            "api_attempts": attempts, "failed_attempts": failed_attempts,
            "missing_usage_attempts": missing_attempts, "stages": stage_rows,
        })
    primary_v3 = {row["invocation_id"] for row in invocation_rows
                  if row.get("context", {}).get("experiment_id") == "expB_paths_v3"
                  and row.get("parent_invocation_id") is None}
    parse_v3 = [row for row in invocation_rows
                if row.get("context", {}).get("experiment_id") == "expB_paths_v3"
                and row.get("parent_invocation_id") is not None]
    if used_primary != primary_v3:
        errors.append(f"stage/primary invocation set mismatch missing={len(primary_v3-used_primary)} extra={len(used_primary-primary_v3)}")
    for parse in parse_v3:
        if parse["parent_invocation_id"] not in primary_v3 or parse["incurred_cost_usd"] != 0.0:
            errors.append(f"invalid parse child {parse['invocation_id']}")
    ledger = [json.loads(path.read_text()) for path in LEDGERS]
    ledger_totals = {key: sum(int(row[key]) for row in ledger) for key in
                     ("calls", "input_tokens", "output_tokens", "failed_attempts", "unknown_usage_calls")}
    computed = {
        "calls": sum(row["api_attempts"] for row in run_costs),
        "input_tokens": sum(row["input_tokens_known"] for row in run_costs),
        "output_tokens": sum(row["output_tokens_known"] for row in run_costs),
        "failed_attempts": sum(row["failed_attempts"] for row in run_costs),
        "unknown_usage_calls": sum(row["missing_usage_attempts"] for row in run_costs),
    }
    if ledger_totals != computed:
        errors.append(f"ledger mismatch ledger={ledger_totals} computed={computed}")
    audit = {
        "status": "pass" if not errors else "fail", "errors": errors,
        "workflow_records": len(workflow_rows), "unique_run_ids": len({r["run_id"] for r in workflow_rows}),
        "primary_invocations": len(primary_v3), "parse_children": len(parse_v3),
        "ledger_totals": ledger_totals, "computed_totals": computed,
        "cost_complete_runs": sum(row["cost_complete"] for row in run_costs),
        "known_usage_spend_usd": sum(row["known_partial_spend_usd"] for row in run_costs),
    }
    return run_costs, audit


def add_v31_labels(run_costs: list[dict[str, Any]], workflows: dict[str, dict], v31: dict[str, Any]) -> None:
    rescored = {row["run_id"]: row for row in v31["records"]}
    for cost in run_costs:
        run = workflows[cost["run_id"]]
        prior_pass = all(stage["status"] == "passed" for stage in run["stages"][:2])
        report = rescored.get(cost["run_id"])
        report_pass = bool(report and report["v31_ground_truth"]["hard_pass"])
        cost["posthoc_v31_outcome"] = (
            "void_infra" if run["feasibility"]["outcome"] == "void_infra"
            else ("feasible" if prior_pass and report_pass else "infeasible")
        )


def summarize_group(rows: list[dict[str, Any]], *, project_id: str | None, path_id: str) -> dict[str, Any]:
    spend_complete = all(row["cost_complete"] for row in rows)
    spend = sum(row["cost_usd"] for row in rows) if spend_complete else None
    result: dict[str, Any] = {
        "project_id": project_id, "path_id": path_id, "n_runs": len(rows),
        "n_cost_complete": sum(row["cost_complete"] for row in rows),
        "evidence_label": "single-run evidence" if len(rows) == 1 else "repeated evidence",
        "total_spend_usd": spend, "known_partial_spend_usd": sum(row["known_partial_spend_usd"] for row in rows),
        "mean_cost_per_run_usd": spend / len(rows) if spend is not None else None,
        "cost_not_estimable_reason": None if spend_complete else "incomplete_run_cost",
    }
    for view, field in (("frozen_v3", "frozen_v3_outcome"), ("posthoc_v31", "posthoc_v31_outcome")):
        nonvoid = [row for row in rows if row[field] != "void_infra"]
        feasible = sum(row[field] == "feasible" for row in rows)
        result[view] = {
            "n_nonvoid": len(nonvoid), "n_void": len(rows) - len(nonvoid), "n_feasible": feasible,
            "feasibility_rate": feasible / len(nonvoid) if nonvoid else None,
            "cost_per_feasible_completion_usd": spend / feasible if spend is not None and feasible else None,
            "not_estimable_reason": ("no_nonvoid_runs" if not nonvoid else
                ("zero_feasible_runs" if feasible == 0 else (None if spend is not None else "incomplete_run_cost"))),
        }
    return result


def build_summaries(run_costs: list[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
    project_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    pooled_groups: dict[str, list[dict]] = defaultdict(list)
    for row in run_costs:
        project_groups[row["project_id"], row["path_id"]].append(row)
        pooled_groups[row["path_id"]].append(row)
    project = [summarize_group(rows, project_id=key[0], path_id=key[1])
               for key, rows in sorted(project_groups.items())]
    pooled = [summarize_group(rows, project_id=None, path_id=path)
              for path, rows in sorted(pooled_groups.items())]
    return project, pooled


def pareto(rows: list[dict[str, Any]], view: str) -> dict[str, Any]:
    eligible, excluded = [], []
    for row in rows:
        cost, feas = row["mean_cost_per_run_usd"], row[view]["feasibility_rate"]
        if cost is None or feas is None:
            excluded.append({"path_id": row["path_id"], "reason": "cost_not_estimable" if cost is None else "feasibility_not_estimable"})
        else:
            eligible.append(row)
    frontier = []
    for row in eligible:
        dominated = any(
            other["mean_cost_per_run_usd"] <= row["mean_cost_per_run_usd"]
            and other[view]["feasibility_rate"] >= row[view]["feasibility_rate"]
            and (other["mean_cost_per_run_usd"] < row["mean_cost_per_run_usd"]
                 or other[view]["feasibility_rate"] > row[view]["feasibility_rate"])
            for other in eligible
        )
        if not dominated:
            frontier.append({"path_id": row["path_id"], "mean_cost_per_run_usd": row["mean_cost_per_run_usd"],
                             "feasibility_rate": row[view]["feasibility_rate"],
                             "n_runs": row["n_runs"], "n_nonvoid": row[view]["n_nonvoid"],
                             "n_feasible": row[view]["n_feasible"], "evidence_label": row["evidence_label"]})
    frontier.sort(key=lambda x: (x["mean_cost_per_run_usd"], -x["feasibility_rate"], x["path_id"]))
    return {"view": view, "eligible_paths": len(eligible), "excluded": excluded, "frontier": frontier}


def build_frontiers(project: list[dict], pooled: list[dict]) -> dict[str, Any]:
    by_project = defaultdict(list)
    for row in project:
        by_project[row["project_id"]].append(row)
    return {
        "per_project": {project_id: {view: pareto(rows, view) for view in ("frozen_v3", "posthoc_v31")}
                        for project_id, rows in sorted(by_project.items())},
        "pooled_posthoc_view": {view: pareto(pooled, view) for view in ("frozen_v3", "posthoc_v31")},
    }


def _evidence_record(envelope: dict[str, Any]) -> dict[str, Any]:
    return envelope["record"]


def candidate_token_cost(candidate: dict[str, Any], stage_by_id: dict[str, dict], prices: dict[str, dict]) -> dict[str, Any]:
    total_tokens = candidate.get("total_tokens")
    if total_tokens is None:
        return {"cost_usd": None, "reason": "frozen_total_tokens_missing"}
    evidence_ids = {e["run_id"] for e in candidate["evidence"] if e["experiment_id"] == "expA_stage_v3"}
    evidence = [stage_by_id[run_id] for run_id in sorted(evidence_ids) if run_id in stage_by_id]
    models = candidate["path_id"].split("-")
    additive_tokens = additive_cost = 0.0
    stage_components = []
    for stage_name, alias in zip(STAGES, models):
        relevant = [row for row in evidence if row["stage"] == stage_name and row["model_alias"] == alias]
        per_project: dict[str, list[dict]] = defaultdict(list)
        for row in relevant:
            rec = row["record"]
            if rec["status"] == "passed" and not rec["cache_hit"] and rec["input_tokens"] is not None and rec["output_tokens"] is not None:
                per_project[row["project_id"]].append(rec)
        project_means = []
        for records in per_project.values():
            project_means.append((statistics.fmean(r["input_tokens"] for r in records),
                                  statistics.fmean(r["output_tokens"] for r in records)))
        if not project_means:
            return {"cost_usd": None, "reason": f"stage_evidence_missing:{stage_name}:{alias}"}
        inp = statistics.fmean(x[0] for x in project_means)
        out = statistics.fmean(x[1] for x in project_means)
        tokens = inp + out
        cost = token_cost(alias, inp, out, prices)
        additive_tokens += tokens
        additive_cost += cost
        stage_components.append({"stage": stage_name, "model_alias": alias,
                                 "additive_input_tokens": inp, "additive_output_tokens": out,
                                 "additive_cost_usd": cost})
    if additive_tokens <= 0:
        return {"cost_usd": None, "reason": "additive_total_tokens_nonpositive"}
    effective_rate = additive_cost / additive_tokens
    return {"cost_usd": total_tokens * effective_rate, "reason": None,
            "frozen_total_tokens": total_tokens, "additive_total_tokens": additive_tokens,
            "additive_cost_usd": additive_cost, "effective_usd_per_token": effective_rate,
            "stage_components": stage_components}


def eligible(candidate: dict[str, Any], objective: dict[str, Any]) -> bool:
    feasibility = candidate.get("feasibility_prob")
    if feasibility is None or feasibility < objective["min_feasibility_prob"]:
        return False
    for constraint in objective["quality_constraints"]:
        value = candidate.get("quality", {}).get(f"{constraint['stage']}.{constraint['metric']}")
        if value is None or (constraint["op"] == ">=" and value < constraint["threshold"]) or (constraint["op"] == "<=" and value > constraint["threshold"]):
            return False
    return True


def _retain_ties(candidates: list[dict], values: dict[str, float | None]) -> list[dict]:
    if any(values[c["path_id"]] is None for c in candidates):
        return candidates
    best = min(values[c["path_id"]] for c in candidates)
    limit = best + TIE_TOLERANCE * abs(best)
    return [c for c in candidates if values[c["path_id"]] <= limit]


def cost_first_sensitivity(traces: list[dict], stage_by_id: dict[str, dict], prices: dict[str, dict]) -> dict[str, Any]:
    rows = []
    for trace in traces:
        conversions = {c["path_id"]: candidate_token_cost(c, stage_by_id, prices) for c in trace["candidates"]}
        eligible_rows = [c for c in trace["candidates"] if eligible(c, trace["objective"])]
        comparable = [c for c in eligible_rows if conversions[c["path_id"]]["cost_usd"] is not None]
        remaining = _retain_ties(comparable, {c["path_id"]: conversions[c["path_id"]]["cost_usd"] for c in comparable}) if comparable else []
        if remaining:
            remaining = _retain_ties(remaining, {c["path_id"]: c.get("end_to_end_ms") for c in remaining})
            remaining = _retain_ties(remaining, {c["path_id"]: c.get("total_tokens") for c in remaining})
            selected = sorted(remaining, key=lambda c: (-c["feasibility_prob"], c["path_id"]))[0]["path_id"]
        else:
            selected = None
        rows.append({
            "trace_id": trace["trace_id"], "strategy": trace["strategy"], "target_project": trace["target_project"],
            "frozen_selected_path_id": trace["selected_path_id"], "cost_first_selected_path_id": selected,
            "changed_vs_frozen": selected != trace["selected_path_id"], "eligible_count": len(eligible_rows),
            "cost_comparable_count": len(comparable), "selection_estimable": selected is not None,
            "missing_converted_cost": {path: row["reason"] for path, row in conversions.items() if row["cost_usd"] is None},
            "candidate_conversions": conversions,
        })
    return {
        "label": "post-hoc conversion of the Router's token predictions; not a prospective dollar prediction",
        "traces": rows, "summary": {"n_traces": len(rows),
            "n_selection_estimable": sum(row["selection_estimable"] for row in rows),
            "n_changed_vs_frozen": sum(row["changed_vs_frozen"] for row in rows),
            "n_not_estimable": sum(not row["selection_estimable"] for row in rows)},
    }


def direction(alternative: float | None, selected: float | None) -> str | None:
    if alternative is None or selected is None:
        return None
    delta = alternative - selected
    tolerance = TIE_TOLERANCE * abs(selected)
    if abs(delta) <= tolerance + 1e-12:
        return "tie"
    if delta < -tolerance:
        return "alternative cheaper"
    return "alternative more expensive"


def naive_path_price_score(path_id: str, prices: dict[str, dict]) -> float:
    """Token-agnostic baseline: sum each stage model's input+output unit prices."""
    return sum(prices[alias]["input_per_mtok"] + prices[alias]["output_per_mtok"]
               for alias in path_id.split("-"))


def counterfactual_cost_check(
    predictions: list[dict], validations: dict[str, dict], traces: dict[str, dict],
    stage_by_id: dict[str, dict], run_by_id: dict[str, dict], prices: dict[str, dict]
) -> dict[str, Any]:
    rows = []
    for envelope in predictions:
        prediction = envelope["record"]
        validation = validations[prediction["prediction_id"]]
        trace = traces[prediction["trace_id"]]
        candidates = {c["path_id"]: c for c in trace["candidates"]}
        selected_conv = candidate_token_cost(candidates[prediction["selected_path_id"]], stage_by_id, prices)
        alternative_conv = candidate_token_cost(candidates[prediction["alternative_path_id"]], stage_by_id, prices)
        def executed(run_ids: list[str]) -> dict[str, Any]:
            values = [run_by_id[run_id] for run_id in run_ids]
            complete = all(row["cost_complete"] for row in values)
            return {"n_runs": len(values), "n_cost_complete": sum(row["cost_complete"] for row in values),
                    "mean_cost_usd": statistics.fmean(row["cost_usd"] for row in values) if complete and values else None,
                    "reason": None if complete and values else "incomplete_or_missing_executed_cost"}
        selected_exec = executed(validation["selected_run_ids"])
        alternative_exec = executed(validation["alternative_run_ids"])
        predicted_direction = direction(alternative_conv["cost_usd"], selected_conv["cost_usd"])
        executed_direction = direction(alternative_exec["mean_cost_usd"], selected_exec["mean_cost_usd"])
        naive_selected = naive_path_price_score(prediction["selected_path_id"], prices)
        naive_alternative = naive_path_price_score(prediction["alternative_path_id"], prices)
        naive_direction = direction(naive_alternative, naive_selected)
        rows.append({
            "prediction_id": prediction["prediction_id"], "strategy": prediction["strategy"],
            "held_out_project": prediction["held_out_project"], "selected_path_id": prediction["selected_path_id"],
            "alternative_path_id": prediction["alternative_path_id"], "predicted_selected_conversion": selected_conv,
            "predicted_alternative_conversion": alternative_conv,
            "predicted_delta_usd": (alternative_conv["cost_usd"] - selected_conv["cost_usd"]
                                    if alternative_conv["cost_usd"] is not None and selected_conv["cost_usd"] is not None else None),
            "executed_selected": selected_exec, "executed_alternative": alternative_exec,
            "executed_delta_usd": (alternative_exec["mean_cost_usd"] - selected_exec["mean_cost_usd"]
                                   if alternative_exec["mean_cost_usd"] is not None and selected_exec["mean_cost_usd"] is not None else None),
            "predicted_direction": predicted_direction, "executed_direction": executed_direction,
            "direction_match": predicted_direction == executed_direction if predicted_direction and executed_direction else None,
            "naive_price_ordering_baseline": {
                "definition": "sum of stage-model (input_per_mtok + output_per_mtok); ignores token volume",
                "selected_unit_price_score": naive_selected,
                "alternative_unit_price_score": naive_alternative,
                "predicted_direction": naive_direction,
                "direction_match": naive_direction == executed_direction if executed_direction else None,
            },
            "frozen_router_feasibility_direction_match": validation["direction_correct"].get("feasible"),
        })
    estimable = [row for row in rows if row["direction_match"] is not None]
    naive_estimable = [row for row in rows if row["naive_price_ordering_baseline"]["direction_match"] is not None]
    common = [row for row in estimable if row["naive_price_ordering_baseline"]["direction_match"] is not None]
    feasibility_estimable = [row for row in rows if row["frozen_router_feasibility_direction_match"] is not None]
    return {"label": "post-hoc conversion of token predictions; frozen Router never predicted dollars",
            "rows": rows, "summary": {"n_pairs": len(rows), "n_direction_estimable": len(estimable),
                "n_direction_matches": sum(row["direction_match"] for row in estimable),
                "direction_match_rate": statistics.fmean(row["direction_match"] for row in estimable) if estimable else None,
                "naive_price_ordering_baseline": {
                    "n_direction_estimable": len(naive_estimable),
                    "n_direction_matches": sum(row["naive_price_ordering_baseline"]["direction_match"] for row in naive_estimable),
                    "direction_match_rate": statistics.fmean(row["naive_price_ordering_baseline"]["direction_match"] for row in naive_estimable) if naive_estimable else None,
                    "common_with_token_conversion_n": len(common),
                    "common_with_token_conversion_matches": sum(row["naive_price_ordering_baseline"]["direction_match"] for row in common),
                },
                "frozen_router_feasibility_direction": {
                    "n_estimable": len(feasibility_estimable),
                    "n_matches": sum(row["frozen_router_feasibility_direction_match"] for row in feasibility_estimable),
                    "match_rate": statistics.fmean(row["frozen_router_feasibility_direction_match"] for row in feasibility_estimable) if feasibility_estimable else None,
                }}}


def build_analysis() -> dict[str, Any]:
    prices = load_prices()
    workflows = read_jsonl(WORKFLOWS)
    validated = [WorkflowRunRecord.model_validate(row).model_dump(mode="json") for row in workflows]
    if len({row["run_id"] for row in validated}) != len(validated):
        raise ValueError("duplicate workflow run ID")
    invocations = read_jsonl(INVOCATIONS)
    run_costs, audit = build_run_costs(validated, invocations, prices)
    if audit["status"] != "pass":
        raise ValueError(f"integrity audit failed: {audit['errors']}")
    v31 = json.loads(V31.read_text())
    if v31["source_records_sha256"] != sha256(WORKFLOWS):
        raise ValueError("v3.1 labels do not match frozen workflow source")
    workflow_by_id = {row["run_id"]: row for row in validated}
    add_v31_labels(run_costs, workflow_by_id, v31)
    project, pooled = build_summaries(run_costs)
    stage_envelopes = read_jsonl(STAGE_RECORDS)
    stage_by_id = {row["run_id"]: row for row in stage_envelopes}
    traces = read_jsonl(TRACES)
    validated_traces = [DecisionTrace.model_validate(row).model_dump(mode="json") for row in traces]
    if validated_traces != traces:
        raise ValueError("trace contract normalization changed saved trace content")
    prediction_chain = PredictionLog(PREDICTIONS).verify()
    validation_chain = HashChainLog(VALIDATIONS).verify()
    if not prediction_chain.ok or not validation_chain.ok:
        raise ValueError(f"routing hash chain failure: predictions={prediction_chain.errors}, validations={validation_chain.errors}")
    trace_by_id = {row["trace_id"]: row for row in traces}
    sensitivity = cost_first_sensitivity(traces, stage_by_id, prices)
    prediction_envelopes = read_jsonl(PREDICTIONS)
    validation_envelopes = read_jsonl(VALIDATIONS)
    prediction_models = {row["record"]["prediction_id"]: CounterfactualPrediction.model_validate(row["record"])
                         for row in prediction_envelopes}
    validation_models = {row["record"]["prediction_id"]: CounterfactualValidation.model_validate(row["record"])
                         for row in validation_envelopes}
    for prediction_id, validation_model in validation_models.items():
        validation_model.check_against(prediction_models[prediction_id])
    validation_by_id = {row["record"]["prediction_id"]: row["record"] for row in validation_envelopes}
    run_by_id = {row["run_id"]: row for row in run_costs}
    counterfactual = counterfactual_cost_check(prediction_envelopes, validation_by_id, trace_by_id,
                                               stage_by_id, run_by_id, prices)
    totals = {}
    for view, field in (("frozen_v3", "frozen_v3_outcome"), ("posthoc_v31", "posthoc_v31_outcome")):
        nonvoid = [row for row in run_costs if row[field] != "void_infra"]
        feasible = sum(row[field] == "feasible" for row in run_costs)
        totals[view] = {"n_runs": len(run_costs), "n_nonvoid": len(nonvoid), "n_feasible": feasible,
                        "feasibility_rate": feasible / len(nonvoid) if nonvoid else None,
                        "cost_per_feasible_completion_usd": audit["known_usage_spend_usd"] / feasible if feasible else None}
    existing_sensitivity = json.loads(EXISTING_ROUTER_SENSITIVITY.read_text())
    source_paths = [WORKFLOWS, INVOCATIONS, STAGE_RECORDS, V31, TRACES, PREDICTIONS, VALIDATIONS,
                    MODELS, RULES, EXISTING_ROUTER_SENSITIVITY, *LEDGERS]
    return {
        "analysis_version": "workflow-cost-posthoc-1.0", "analysis_date": "2026-11-19",
        "mode": "post-hoc / exploratory; offline only", "retail_sales_pilot_exposed": True,
        "sources": {str(path.relative_to(REPO)): sha256(path) for path in source_paths},
        "prices": prices, "integrity_audit": {**audit, "routing_artifacts": {
            "validated_traces": len(validated_traces), "prediction_chain_ok": prediction_chain.ok,
            "prediction_chain_records": prediction_chain.n_lines, "validation_chain_ok": validation_chain.ok,
            "validation_chain_records": validation_chain.n_lines,
            "prediction_validation_links_checked": len(validation_models)}}, "overall": {
            "n_runs": len(run_costs), "total_spend_usd": audit["known_usage_spend_usd"],
            "mean_cost_per_run_usd": audit["known_usage_spend_usd"] / len(run_costs), **totals},
        "run_costs": run_costs, "project_path_summaries": project,
        "pooled_path_summaries": pooled, "pareto_frontiers": build_frontiers(project, pooled),
        "existing_router_sensitivity_posthoc": existing_sensitivity,
        "router_cost_first_sensitivity": sensitivity, "cost_counterfactual": counterfactual,
        "limitations": ["Most project/path cells are single-run evidence.",
                        "The pooled view includes retail_sales, which is pilot-exposed.",
                        "v3.1 is a post-hoc secondary label view; frozen v3 remains primary.",
                        "Router dollar quantities are post-hoc conversions of frozen token predictions, not prospective dollar predictions."],
    }


def _money(value: float | None) -> str:
    return "not estimable" if value is None else f"${value:.4f}"


def _rate(value: float | None) -> str:
    return "not estimable" if value is None else f"{100*value:.1f}%"


def render_report(result: dict[str, Any]) -> str:
    overall = result["overall"]
    frozen, v31 = overall["frozen_v3"], overall["posthoc_v31"]
    sens = result["router_cost_first_sensitivity"]["summary"]
    cf = result["cost_counterfactual"]["summary"]
    naive = cf["naive_price_ordering_baseline"]
    feasibility_direction = cf["frozen_router_feasibility_direction"]
    lines = [
        "# Workflow cost analysis — post-hoc / exploratory", "", "## Key findings", "",
        f"- Across {overall['n_runs']} saved runs, executed spend was {_money(overall['total_spend_usd'])}; every run had complete recorded usage (**not single-run evidence overall**).",
        f"- Frozen v3 found {frozen['n_feasible']}/{frozen['n_nonvoid']} feasible runs ({_rate(frozen['feasibility_rate'])}); post-hoc v3.1 found {v31['n_feasible']}/{v31['n_nonvoid']} ({_rate(v31['feasibility_rate'])}). Spend is identical; only feasibility denominators change.",
        f"- Cost per feasible completion was {_money(frozen['cost_per_feasible_completion_usd'])} under v3 and {_money(v31['cost_per_feasible_completion_usd'])} under v3.1 (pooled exploratory evidence).",
        f"- The cost-first token-conversion view was estimable for {sens['n_selection_estimable']}/{sens['n_traces']} frozen traces and changed {sens['n_changed_vs_frozen']}/{sens['n_traces']} selections; it is not a prospective dollar prediction.",
        f"- Cost-counterfactual direction matched in {cf['n_direction_matches']}/{cf['n_direction_estimable']} estimable pairs; a token-agnostic unit-price baseline matched {naive['common_with_token_conversion_matches']}/{naive['common_with_token_conversion_n']} on the same pairs, so cost direction is largely price-ordered.",
        "", "## Scope and provenance", "",
        "This offline analysis prices the saved Experiment B v3 calls with the verified A/B/C prices in `configs/models.yaml`. Frozen v3 feasibility is primary; existing post-hoc v3.1 labels are secondary. `retail_sales` is pilot-exposed, so the pooled view contains one pilot-exposed project. No Router trace, prediction, validation, or raw record was changed.",
        "", "## Integrity and cost reconciliation", "",
        f"Audit: **{result['integrity_audit']['status'].upper()}**. {result['integrity_audit']['workflow_records']} unique workflow records map to {result['integrity_audit']['primary_invocations']} primary API calls and {result['integrity_audit']['parse_children']} non-billable parse children. Ledger calls and tokens reconcile exactly. Missing-usage calls: {result['integrity_audit']['computed_totals']['unknown_usage_calls']}; failed attempts: {result['integrity_audit']['computed_totals']['failed_attempts']}.",
        "", "## Project-level path costs", "",
        "`single-run evidence` means the project/path cell has n=1. Cost is unchanged across validator views.", "",
        "| Project | Path | Evidence | Spend | Mean/run | v3 feasible | v3 cost/feasible | v3.1 feasible | v3.1 cost/feasible |", "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["project_path_summaries"]:
        a, b = row["frozen_v3"], row["posthoc_v31"]
        lines.append(f"| {row['project_id']} | {row['path_id']} | {row['evidence_label']} (n={row['n_runs']}) | {_money(row['total_spend_usd'])} | {_money(row['mean_cost_per_run_usd'])} | {a['n_feasible']}/{a['n_nonvoid']} | {_money(a['cost_per_feasible_completion_usd'])} | {b['n_feasible']}/{b['n_nonvoid']} | {_money(b['cost_per_feasible_completion_usd'])} |")
    lines += ["", "## Pooled path costs", "",
              "This is a **pooled post-hoc view**, not an equal-weighted project comparison. It includes pilot-exposed `retail_sales`.", "",
              "| Path | Evidence | Spend | Mean/run | v3 feasible | v3 cost/feasible | v3.1 feasible | v3.1 cost/feasible |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in result["pooled_path_summaries"]:
        a, b = row["frozen_v3"], row["posthoc_v31"]
        lines.append(f"| {row['path_id']} | {row['evidence_label']} (n={row['n_runs']}) | {_money(row['total_spend_usd'])} | {_money(row['mean_cost_per_run_usd'])} | {a['n_feasible']}/{a['n_nonvoid']} | {_money(a['cost_per_feasible_completion_usd'])} | {b['n_feasible']}/{b['n_nonvoid']} | {_money(b['cost_per_feasible_completion_usd'])} |")
    lines += ["", "## Quality–cost Pareto frontiers", "",
              "Axes are mean executed cost per saved run (lower) and feasibility among non-void runs (higher). Frontiers retain ties and are listed separately by validator.", ""]
    for project, views in result["pareto_frontiers"]["per_project"].items():
        for view, body in views.items():
            text = ", ".join(f"{x['path_id']} ({_money(x['mean_cost_per_run_usd'])}, {x['n_feasible']}/{x['n_nonvoid']}, {x['evidence_label']})" for x in body["frontier"])
            lines.append(f"- **{project}, {view}:** {text or 'not estimable'}")
    for view, body in result["pareto_frontiers"]["pooled_posthoc_view"].items():
        text = ", ".join(f"{x['path_id']} ({_money(x['mean_cost_per_run_usd'])}, {x['n_feasible']}/{x['n_nonvoid']}, n={x['n_runs']})" for x in body["frontier"])
        lines.append(f"- **Pooled post-hoc, {view}:** {text or 'not estimable'}")
    lines += ["", "## Router cost-first sensitivity", "",
              "This is a **post-hoc conversion of the Router's token predictions**. The frozen Router never predicted dollars. Candidate estimates, evidence, constraints, and traces remain frozen.", "",
              "The previously reported sensitivity views remain alongside this addition: `frozen_v3`, `feasibility_only`, `strict_quality`, `token_first`, and `maximum_reliability`.", "",
              "| Trace | Strategy | Project | Frozen selection | Cost-first conversion | Comparable/eligible | Changed |", "|---|---|---|---|---|---:|---:|"]
    for row in result["router_cost_first_sensitivity"]["traces"]:
        lines.append(f"| {row['trace_id']} | {row['strategy']} | {row['target_project']} | {row['frozen_selected_path_id'] or 'none'} | {row['cost_first_selected_path_id'] or 'not estimable'} | {row['cost_comparable_count']}/{row['eligible_count']} | {'yes' if row['changed_vs_frozen'] else 'no'} |")
    lines += ["", "## Cost counterfactual: post-hoc conversion of token predictions", "",
              "Predicted direction uses the post-hoc token conversion; executed direction uses recorded tokens × verified prices. This does not retroactively validate a prospective dollar forecast.", "",
              f"On the common estimable subset, token conversion matched {cf['n_direction_matches']}/{cf['n_direction_estimable']} and the naive unit-price ordering baseline matched {naive['common_with_token_conversion_matches']}/{naive['common_with_token_conversion_n']}. Across all executed-cost pairs the naive baseline matched {naive['n_direction_matches']}/{naive['n_direction_estimable']}. By contrast, the frozen Router's feasibility direction matched only {feasibility_direction['n_matches']}/{feasibility_direction['n_estimable']} ({100*feasibility_direction['match_rate']:.1f}%): feasibility, not cost ordering, was the difficult decision-relevant quantity.", "",
              "| Strategy/project | Selected → alternative | Predicted Δ | Executed Δ | Runs selected/alternative | Direction match |", "|---|---|---:|---:|---:|---:|"]
    for row in result["cost_counterfactual"]["rows"]:
        lines.append(f"| {row['strategy']} / {row['held_out_project']} | {row['selected_path_id']} → {row['alternative_path_id']} | {_money(row['predicted_delta_usd'])} | {_money(row['executed_delta_usd'])} | {row['executed_selected']['n_runs']}/{row['executed_alternative']['n_runs']} | {'yes' if row['direction_match'] is True else ('no' if row['direction_match'] is False else 'not estimable')} |")
    lines += ["", "## Limitations", ""] + [f"- {item}" for item in result["limitations"]]
    lines += ["- No path should be called the cheapest combination without its feasibility denominator, evidence count, and cost-completeness status.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    result = build_analysis()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    REPORT.write_text(render_report(result))
    print(json.dumps({"analysis": str(OUT.relative_to(REPO)), "report": str(REPORT.relative_to(REPO)),
                      "audit": result["integrity_audit"]["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
