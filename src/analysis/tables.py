"""Processed-table builders. Every number is derived from saved records/files only.

Aggregation reuses the existing rules instead of duplicating them:
  * ``src.evaluation.workflow_metrics.summarize_runs``  counts, quality (ground truth and
    conditional, side by side), efficiency, cost status (missing price -> None, never 0);
  * ``src.routing.outcomes.aggregate_runs``             outcome label and feasible-run means used for
    the Pareto table (same rule as S3 training / S4 oracle);
  * ``src.routing.scoring.pareto_front``                Pareto dominance.
No composite score and no significance test is computed anywhere.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from src.contracts import (
    QUALITY_METRICS,
    STAGES,
    CounterfactualValidation,
    PathPrediction,
    StageBenchmarkRecord,
    StageStatus,
    WorkflowRunRecord,
    is_single_model,
    n_switches,
    parse_path_id,
)
from src.evaluation.workflow_metrics import summarize_runs
from src.routing.counterfactual import HashChainLog, PredictionLog
from src.routing.outcomes import aggregate_runs
from src.routing.scoring import LOWER_IS_BETTER_QUALITY, pareto_front

from .io import Table

PREFIX = ["experiment_id", "benchmark_version", "prompt_version", "validator_version",
          "project_id", "n_runs", "n_void_infra"]
PROPAGATION_LABEL = "descriptive_decomposition_not_causal_switching_cost"
ORACLE_LABEL = "S4_retrospective_reference_not_deployable"
METRIC_KEYS = [(s.value, m) for s in STAGES for m in QUALITY_METRICS[s]]


@dataclass
class Context:
    runs_by_exp: dict[str, list[WorkflowRunRecord]]
    stage_by_exp: dict[str, list[StageBenchmarkRecord]]
    benchmark_versions: dict[str, str] = field(default_factory=dict)
    matched_pairs: dict[str, str] = field(default_factory=dict)   # expB id -> expA id
    status_override: str | None = None
    routing_dir: Path | None = None
    rescores: list[dict] = field(default_factory=list)
    source_hashes: dict[str, str] = field(default_factory=dict)

    def status(self, evidence: str) -> str:
        return self.status_override or evidence


# --------------------------------------------------------------------------- helpers

def _valid(runs):
    return [r for r in runs if r.feasibility.outcome != "void_infra"]


def _versions(runs) -> tuple[str, str]:
    prompts = sorted({s.prompt_version for r in runs for s in r.stages})
    vv: dict[str, set] = defaultdict(set)
    for r in runs:
        for s in r.stages:
            for v in (s.validation, s.conditional_validation):
                if v is not None:
                    vv[s.stage.value].add(v.validator_version)
    validators = ";".join(f"{st.value}={'|'.join(sorted(vv[st.value]))}" for st in STAGES if vv[st.value])
    return "|".join(prompts) or None, validators or None


def _prefix(ctx: Context, exp: str, project: str, runs) -> dict:
    pv, vv = _versions(runs)
    return {"experiment_id": exp, "benchmark_version": ctx.benchmark_versions.get(exp, "unrecorded"),
            "prompt_version": pv, "validator_version": vv, "project_id": project,
            "n_runs": len(runs), "n_void_infra": sum(r.feasibility.outcome == "void_infra" for r in runs)}


def _by_project(runs) -> dict[str, list]:
    g: dict[str, list] = defaultdict(list)
    for r in runs:
        g[r.project_id].append(r)
    return dict(sorted(g.items()))


def _by_path(runs) -> dict[str, list]:
    g: dict[str, list] = defaultdict(list)
    for r in runs:
        g[r.path_id].append(r)
    return dict(sorted(g.items(), key=lambda kv: (len(parse_path_id(kv[0])), kv[0])))


def _stats(xs) -> dict:
    xs = [float(x) for x in xs if x is not None]
    if not xs:
        return {"mean": None, "min": None, "max": None, "n": 0}
    return {"mean": sum(xs) / len(xs), "min": min(xs), "max": max(xs), "n": len(xs)}


def _insufficient(ctx, exp, project, runs, detail, columns) -> dict:
    row = {c: None for c in columns}
    row.update(_prefix(ctx, exp, project, runs) if exp else {})
    row["status_detail"] = "insufficient_evidence: " + detail
    return row


def _grid_complete(runs) -> bool:
    """Every (project, n_stages) group has all |models|^n paths and no void run."""
    if any(r.feasibility.outcome == "void_infra" for r in runs):
        return False
    aliases = {m for r in runs for m in r.models}
    groups: dict[tuple, set] = defaultdict(set)
    for r in runs:
        groups[(r.project_id, len(r.models))].add(r.path_id)
    return all(len(p) == len(aliases) ** n for (_, n), p in groups.items())


def _iter_groups(ctx: Context):
    for exp, runs in sorted(ctx.runs_by_exp.items()):
        for project, pruns in _by_project(runs).items():
            yield exp, project, pruns


# --------------------------------------------------------------------------- 1. path_summary

EFF_COLS = ["end_to_end_ms_mean", "api_latency_ms_mean", "execution_ms_mean", "input_tokens_mean",
            "output_tokens_mean", "n_calls_mean", "n_cache_hits", "cost_usd_mean", "cost_status"]
PATH_SUMMARY_COLS = PREFIX + [
    "path_id", "n_stages", "same_model", "n_switches", "n_feasible", "n_infeasible", "n_valid",
    "feasibility_rate", "outcome_label", "first_failure_stage", "failure_type",
] + [f"{b}.{s}.{m}" for s, m in METRIC_KEYS for b in ("gt", "cond")] \
  + [f"n_gt.{s.value}" for s in STAGES] + EFF_COLS + ["status_detail"]


def path_summary(ctx: Context) -> Table:
    rows, all_runs = [], []
    for exp, project, pruns in _iter_groups(ctx):
        all_runs += pruns
        for path, runs in _by_path(pruns).items():
            counts = summarize_runs(runs)
            valid = _valid(runs)
            sv = summarize_runs(valid) if valid else None
            row = _prefix(ctx, exp, project, runs) | {
                "path_id": path, "n_stages": len(parse_path_id(path)), "same_model": is_single_model(path),
                "n_switches": n_switches(path), "n_feasible": counts["n_feasible"],
                "n_infeasible": counts["n_infeasible"], "n_valid": len(valid),
                "feasibility_rate": counts["feasibility_rate"],
                "outcome_label": aggregate_runs(path, runs).outcome_label,
                "first_failure_stage": dict(sorted(counts["first_failure_stage"].items())),
                "failure_type": dict(sorted(counts["failure_type"].items())),
                "cost_status": "unavailable",
            }
            if sv:
                for s, m in METRIC_KEYS:
                    gt = sv["quality"].get(s, {}).get(m)
                    cd = sv["conditional_quality"].get(s, {}).get(m)
                    row[f"gt.{s}.{m}"] = gt["mean"] if gt else None
                    row[f"cond.{s}.{m}"] = cd["mean"] if cd else None
                for st in STAGES:
                    ns = [v["n"] for v in sv["quality"].get(st.value, {}).values() if v]
                    row[f"n_gt.{st.value}"] = max(ns) if ns else 0
                e = sv["efficiency"]
                mean = lambda k: e[k]["mean"] if e[k] else None  # noqa: E731
                row |= {"end_to_end_ms_mean": mean("end_to_end_ms"),
                        "api_latency_ms_mean": mean("total_api_latency_ms"),
                        "execution_ms_mean": mean("total_execution_ms"),
                        "input_tokens_mean": mean("input_tokens"), "output_tokens_mean": mean("output_tokens"),
                        "n_calls_mean": mean("n_calls"), "n_cache_hits": e["n_cache_hits"],
                        "cost_usd_mean": e["cost_usd"]["mean"] if e["cost_usd"] else None,
                        "cost_status": e["cost_status"]}
            else:
                row["status_detail"] = "all runs void_infra: no feasibility rate, quality or efficiency"
            rows.append(row)
    ev = "insufficient_evidence" if not rows else ("complete" if _grid_complete(all_runs) else "partial")
    return Table("path_summary", PATH_SUMMARY_COLS, rows, ctx.status(ev), ev, notes=[
        "feasibility_rate is STRICT (all stages passed) over non-void runs; void_infra runs are counted "
        "in n_void_infra and excluded from the rate, quality and efficiency.",
        "gt.* = ground-truth quality, cond.* = conditional-reference quality; means over non-void runs in "
        "which the stage was validated (failed stages included). Not a composite score.",
        "end_to_end_ms and API latency are separate quantities. cost_usd_mean is null when any price is "
        "unverified (cost_status unavailable/partial); it is never 0 by default.",
    ])


# --------------------------------------------------------------------------- 2. propagation

PROP_COLS = PREFIX + ["path_id", "stage", "quantity", "metric", "mean", "min", "max", "n",
                      "interpretation", "status_detail"]


def propagation(ctx: Context) -> Table:
    rows = []
    for exp, project, pruns in _iter_groups(ctx):
        for path, runs in _by_path(pruns).items():
            props = [r.propagation for r in _valid(runs) if r.propagation is not None]
            pre = _prefix(ctx, exp, project, runs)
            if not props:
                rows.append(_insufficient(ctx, exp, project, runs, "no PropagationSummary on non-void runs",
                                          PROP_COLS) | {"path_id": path})
                continue
            stages = [st.value for st in STAGES[:len(parse_path_id(path))]]
            def add(stage, qty, metric, xs):
                rows.append(pre | {"path_id": path, "stage": stage, "quantity": qty, "metric": metric,
                                   **_stats(xs), "interpretation": PROPAGATION_LABEL})
            for st in stages:
                add(st, "downstream_executable", "",
                    [float(p.downstream_executable[st]) for p in props if st in p.downstream_executable])
                add(st, "blocked", "", [float(st in p.blocked_stages) for p in props])
                for qty in ("upstream_error_severity", "propagation_impact"):
                    metrics = sorted({m for p in props for m in getattr(p, qty).get(st, {})})
                    for m in metrics:
                        add(st, qty, m, [getattr(p, qty)[st].get(m) for p in props if st in getattr(p, qty)])
            last = stages[-1]
            for m in sorted({m for p in props for m in p.end_to_end_accuracy}):
                add(last, "end_to_end_accuracy", m, [p.end_to_end_accuracy.get(m) for p in props])
    has = any(r["quantity"] for r in rows)
    ev = "insufficient_evidence" if not has else (
        "complete" if _grid_complete([r for _, rs in ctx.runs_by_exp.items() for r in rs]) else "partial")
    return Table("propagation", PROP_COLS, rows, ctx.status(ev), ev, notes=[
        "Descriptive decomposition of observed outcomes under continue_with_actual_artifact. "
        "propagation_impact = conditional - ground-truth quality; it is NOT a causal model-switching or "
        "handoff cost (upstream data errors, formatting and stochasticity all contribute).",
        "Statistics over non-void runs; downstream_executable and blocked are fractions of those runs.",
    ])


# --------------------------------------------------------------------------- 3. matched_baseline

MATCHED_COLS = PREFIX + ["n_stages", "canonical_experiment_id", "canonical_prompt_version", "analysis_model",
                         "upstream_cleaning_model", "metric", "canonical_mean", "canonical_n",
                         "actual_upstream_mean", "actual_upstream_n", "difference_actual_minus_canonical",
                         "interpretation", "status_detail"]


def matched_baseline(ctx: Context) -> Table:
    rows = []
    for exp, project, pruns in _iter_groups(ctx):
        exp_a = ctx.matched_pairs.get(exp)
        if exp_a is None and len(ctx.stage_by_exp) == 1:
            exp_a = next(iter(ctx.stage_by_exp))
        srecs = [s for s in ctx.stage_by_exp.get(exp_a, []) if s.project_id == project
                 and s.stage.value == "analysis" and s.record.status != StageStatus.INFRA_ERROR
                 and s.record.validation is not None]
        if not srecs:
            rows.append(_insufficient(ctx, exp, project, pruns,
                                      "no Experiment A (canonical-input) analysis records for this project",
                                      MATCHED_COLS))
            continue
        b_obs: dict[tuple[str, str], list] = defaultdict(list)   # (analysis model, cleaning model) -> runs
        for r in _valid(pruns):
            if len(r.stages) > 1 and r.stages[1].validation is not None:
                b_obs[(r.models[1], r.models[0], len(r.models))].append(r)
        a_by_model: dict[str, list] = defaultdict(list)
        for s in srecs:
            a_by_model[s.model_alias].append(s)
        for (am, cm, nst), runs in sorted(b_obs.items()):
            arecs = a_by_model.get(am, [])
            pre = _prefix(ctx, exp, project, runs) | {"n_stages": nst, "analysis_model": am,
                                                      "upstream_cleaning_model": cm,
                                                      "canonical_experiment_id": exp_a}
            if not arecs:
                rows.append(pre | {"status_detail": f"insufficient_evidence: no Experiment A analysis record "
                                                    f"for model {am}"})
                continue
            for m in QUALITY_METRICS[STAGES[1]]:
                a = _stats(s.record.validation.quality.get(m) for s in arecs)
                b = _stats(r.stages[1].validation.quality.get(m) for r in runs)
                diff = b["mean"] - a["mean"] if a["mean"] is not None and b["mean"] is not None else None
                rows.append(pre | {"canonical_prompt_version": "|".join(sorted({s.record.prompt_version
                                                                              for s in arecs})),
                                   "metric": m, "canonical_mean": a["mean"], "canonical_n": a["n"],
                                   "actual_upstream_mean": b["mean"], "actual_upstream_n": b["n"],
                                   "difference_actual_minus_canonical": diff,
                                   "interpretation": PROPAGATION_LABEL})
    has = any(r.get("metric") for r in rows)
    ev = "insufficient_evidence" if not has else (
        "complete" if not any(r.get("status_detail") for r in rows) else "partial")
    return Table("matched_baseline", MATCHED_COLS, rows, ctx.status(ev), ev, notes=[
        "Analysis-stage ground-truth quality on canonical input (Experiment A) vs on the actual upstream "
        "artifact (Experiment B), same model and project. The difference is descriptive, not a pure "
        "switching cost. Experiment A handoffs label inputs 'Canonical reference', a documented wording "
        "difference (rule 5).",
    ])


# --------------------------------------------------------------------------- 4. pareto

PARETO_COLS = PREFIX + ["n_stages", "row_type", "path_id", "n_feasible", "feasibility_rate", "pareto_optimal",
                        "dominated_by", "objectives", "quality_feasible_mean", "end_to_end_ms",
                        "total_tokens", "cost_usd", "status_detail"]


def pareto(ctx: Context) -> Table:
    rows = []
    for exp, project, pruns in _iter_groups(ctx):
        by_len: dict[int, list] = defaultdict(list)
        for r in pruns:
            by_len[len(r.models)].append(r)
        for nst, runs in sorted(by_len.items()):
            pre = _prefix(ctx, exp, project, runs) | {"n_stages": nst}
            outs = {p: aggregate_runs(p, rs) for p, rs in _by_path(runs).items()}
            cands = []
            for p, o in outs.items():
                if o.n_feasible == 0:
                    continue
                v = o.values
                cands.append(PathPrediction(
                    path_id=p, feasibility_prob=v["feasible"],
                    quality={k: x for k, x in v.items() if "." in k and x is not None},
                    end_to_end_ms=v["end_to_end_ms"], cost_usd=v["cost_usd"],
                    total_tokens=v["total_tokens"], n_switches=n_switches(p)))
            if not cands:
                rows.append(pre | {"row_type": "no_feasible_path",
                                   "status_detail": "no path has a feasible non-void run"})
                continue
            qkeys = sorted(set.intersection(*(set(c.quality) for c in cands)))
            dims = [(k, "min" if k in LOWER_IS_BETTER_QUALITY else "max") for k in qkeys]
            for k in ("end_to_end_ms", "total_tokens", "cost_usd"):     # cost only when verified for all
                if all(getattr(c, k) is not None for c in cands):
                    dims.append((k, "min"))
            front, removed = pareto_front(cands, dims)
            for c in sorted(cands, key=lambda c: c.path_id):
                o = outs[c.path_id]
                rows.append(pre | {"row_type": "candidate", "path_id": c.path_id, "n_feasible": o.n_feasible,
                                   "feasibility_rate": o.values["feasible"],
                                   "pareto_optimal": c.path_id in front,
                                   "dominated_by": removed.get(c.path_id, "").removeprefix("dominated by ")
                                   or None,
                                   "objectives": [f"{k}:{s}" for k, s in dims],
                                   "quality_feasible_mean": dict(sorted(c.quality.items())),
                                   "end_to_end_ms": c.end_to_end_ms, "total_tokens": c.total_tokens,
                                   "cost_usd": c.cost_usd})
    has = any(r["row_type"] == "candidate" for r in rows)
    ev = "insufficient_evidence" if not rows else (
        "complete" if has and _grid_complete([r for rs in ctx.runs_by_exp.values() for r in rs]) else "partial")
    return Table("pareto", PARETO_COLS, rows, ctx.status(ev), ev, notes=[
        "Candidates: paths with >=1 feasible non-void run, grouped by project and number of stages. "
        "Objective values are means over FEASIBLE runs (src.routing.outcomes.aggregate_runs). Quality metrics "
        "are maximised except unsupported_claim_count (minimised); end_to_end_ms and total_tokens minimised; "
        "cost only when verified for every candidate. No composite score. 'no_feasible_path' rows are kept.",
    ])


# --------------------------------------------------------------------------- 5-6. routing outputs

def _read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _routing_prefix(ctx: Context, project: str) -> dict:
    runs = [r for rs in ctx.runs_by_exp.values() for r in rs if r.project_id == project]
    exps = sorted({r.experiment_id for r in runs})
    return _prefix(ctx, "|".join(exps) or None, project, runs) if exps else {"project_id": project}


STRATEGY_COLS = PREFIX + ["strategy", "trace_id", "selected_path_id", "no_feasible_path", "policy_path_id",
                          "executed_outcome_label", "executed_n_runs", "executed_n_void", "executed_values",
                          "oracle_selected_path_id", "oracle_role", "matches_oracle_selection",
                          "in_oracle_feasible_set", "in_oracle_pareto_set", "status_detail"]


def strategies(ctx: Context) -> Table:
    p = ctx.routing_dir / "oracle_comparison.json" if ctx.routing_dir else None
    if p is None or not p.exists():
        row = _insufficient(ctx, None, None, [], "no evaluate_routing/validate_counterfactuals output "
                            "(oracle_comparison.json)", STRATEGY_COLS)
        return Table("strategies", STRATEGY_COLS, [row], ctx.status("insufficient_evidence"),
                     "insufficient_evidence", notes=[f"S4 is {ORACLE_LABEL}."])
    rows = []
    for c in json.loads(p.read_text())["rows"]:
        ex = c.get("executed_outcome") or {}
        rows.append(_routing_prefix(ctx, c["held_out_project"]) | {
            "strategy": c["strategy"], "trace_id": c["trace_id"], "selected_path_id": c["selected_path_id"],
            "no_feasible_path": c["no_feasible_path"], "policy_path_id": c.get("policy_path_id"),
            "executed_outcome_label": ex.get("label"), "executed_n_runs": ex.get("n_runs"),
            "executed_n_void": ex.get("n_void"), "executed_values": ex.get("values"),
            "oracle_selected_path_id": c["oracle_selected_path_id"], "oracle_role": ORACLE_LABEL,
            "matches_oracle_selection": c["matches_oracle_selection"],
            "in_oracle_feasible_set": c["in_oracle_feasible_set"],
            "in_oracle_pareto_set": c["in_oracle_pareto_set"]})
    rows.sort(key=lambda r: (r["project_id"], r["strategy"], r["trace_id"]))
    ev = "complete" if rows else "insufficient_evidence"
    return Table("strategies", STRATEGY_COLS, rows, ctx.status(ev), ev, notes=[
        "S1/S2/S3 are prospective (LOPO) decisions; S4 is the retrospective oracle built from the held-out "
        "project's outcomes AFTER predictions were logged. S4 is a reference only and is NOT deployable.",
    ])


CF_COLS = PREFIX + ["prediction_id", "strategy", "selected_path_id", "alternative_path_id", "quantity",
                    "predicted_delta", "predicted_delta_interval", "actual_delta", "actual_delta_spread",
                    "abs_error", "direction_correct", "interval_covers_actual", "actual_outcome_selected",
                    "actual_outcome_alternative", "status_detail"]


def counterfactual_validity(ctx: Context) -> Table:
    d = ctx.routing_dir
    if d is None or not (d / "counterfactual_validations.jsonl").exists() \
            or not (d / "counterfactual_predictions.jsonl").exists():
        row = _insufficient(ctx, None, None, [], "no counterfactual prediction + validation logs", CF_COLS)
        return Table("counterfactual_validity", CF_COLS, [row], ctx.status("insufficient_evidence"),
                     "insufficient_evidence", notes=["EMPIRICAL VALIDITY only; faithfulness is a separate table."])
    plog, vlog = PredictionLog(d / "counterfactual_predictions.jsonl"), HashChainLog(d / "counterfactual_validations.jsonl")
    for name, log in (("prediction", plog), ("validation", vlog)):
        rep = log.verify()
        if not rep.ok:
            raise ValueError(f"refusing to analyse: {name} log hash chain is broken: {rep.errors}")
    preds = {p.prediction_id: p for p in plog.predictions()}
    rows = []
    for o in vlog.records():
        v = CounterfactualValidation.model_validate(o)
        p = preds[v.prediction_id]
        v.check_against(p)                    # refuses a prediction that changed after validation
        for q in sorted(set(p.predicted_delta) | set(v.actual_delta)):
            iv, sp = p.predicted_delta_interval.get(q), v.actual_delta_spread.get(q)
            rows.append(_routing_prefix(ctx, p.held_out_project) | {
                "prediction_id": p.prediction_id, "strategy": p.strategy.value,
                "selected_path_id": p.selected_path_id, "alternative_path_id": p.alternative_path_id,
                "quantity": q, "predicted_delta": p.predicted_delta.get(q),
                "predicted_delta_interval": list(iv) if iv else None, "actual_delta": v.actual_delta.get(q),
                "actual_delta_spread": list(sp) if sp else None, "abs_error": v.abs_error.get(q),
                "direction_correct": v.direction_correct.get(q),
                "interval_covers_actual": v.interval_covers_actual.get(q),
                "actual_outcome_selected": v.actual_outcome.get("selected"),
                "actual_outcome_alternative": v.actual_outcome.get("alternative")})
    rows.sort(key=lambda r: (r["project_id"], r["prediction_id"], r["quantity"]))
    ev = "complete" if rows else "insufficient_evidence"
    return Table("counterfactual_validity", CF_COLS, rows, ctx.status(ev), ev, notes=[
        "EMPIRICAL VALIDITY: logged (hashed) predictions vs executed held-out outcomes. Descriptive only; no "
        "significance claims. Computational faithfulness is reported in a separate table.",
    ])


FAITH_COLS = PREFIX + ["trace_id", "strategy", "explanation_kind", "claims_checked", "claims_consistent",
                       "replay_matches_selection", "n_inconsistencies", "trace_hash", "explanation_hash",
                       "status_detail"]


def faithfulness(ctx: Context) -> Table:
    d = ctx.routing_dir
    if d is None or not (d / "computational_faithfulness.jsonl").exists():
        row = _insufficient(ctx, None, None, [], "no computational_faithfulness.jsonl", FAITH_COLS)
        return Table("faithfulness", FAITH_COLS, [row], ctx.status("insufficient_evidence"),
                     "insufficient_evidence", notes=["COMPUTATIONAL FAITHFULNESS only; separate from validity."])
    traces = {t["trace_id"]: t for t in _read_jsonl(d / "traces.jsonl")} if (d / "traces.jsonl").exists() else {}
    rows = []
    for fc in _read_jsonl(d / "computational_faithfulness.jsonl"):
        t = traces.get(fc["trace_id"], {})
        rows.append(_routing_prefix(ctx, t.get("target_project")) | {
            "trace_id": fc["trace_id"], "strategy": t.get("strategy"),
            "explanation_kind": fc.get("explanation_kind"), "claims_checked": fc["claims_checked"],
            "claims_consistent": fc["claims_consistent"],
            "replay_matches_selection": fc.get("replay_matches_selection"),
            "n_inconsistencies": len(fc.get("inconsistencies", [])), "trace_hash": fc["trace_hash"],
            "explanation_hash": fc["explanation_hash"]})
    rows.sort(key=lambda r: (str(r["project_id"]), str(r["strategy"]), r["trace_id"]))
    ev = "complete" if rows else "insufficient_evidence"
    return Table("faithfulness", FAITH_COLS, rows, ctx.status(ev), ev, notes=[
        "COMPUTATIONAL FAITHFULNESS: do explanation claims match the recorded decision trace, and does a "
        "router replay give the same selection. Says nothing about empirical validity.",
    ])


# --------------------------------------------------------------------------- 7. reporting_scores

REPORT_METRICS = QUALITY_METRICS[STAGES[2]]
REPORT_COLS = PREFIX + ["row_type", "run_id", "path_id", "quality_basis", "origin", "source", "hard_pass",
                        *REPORT_METRICS, "n_reports", "n_hard_pass", "comparability_note", "status_detail"]


def reporting_scores(ctx: Context) -> Table:
    run_index = {r.run_id: r for rs in ctx.runs_by_exp.values() for r in rs}
    entries: dict[tuple, dict] = {}     # (run_id, basis, validator_version) -> row
    notes = ["Each row is ONE validator version. Versions are shown side by side and never pooled, "
             "averaged across, or substituted for one another."]
    for r in run_index.values():
        if r.feasibility.outcome == "void_infra" or len(r.stages) < 3:
            continue
        st = r.stages[2]
        for v in (st.validation, st.conditional_validation):
            if v is not None:
                entries[(r.run_id, v.quality_basis, v.validator_version)] = {
                    "origin": "raw_record", "source": None, "hard_pass": v.hard_pass, **v.quality}
    for d in ctx.rescores:
        if d.get("source_records_sha256") not in ctx.source_hashes.values():
            notes.append(f"{d['_source']}: source_records_sha256 does not match any analysed record file")
        for rec in d.get("records", []):
            if rec["run_id"] not in run_index:
                continue
            for v in rec.values():
                if not (isinstance(v, dict) and "validator_version" in v and "quality_basis" in v):
                    continue
                key = (rec["run_id"], v["quality_basis"], v["validator_version"])
                if key in entries:
                    if entries[key]["hard_pass"] != v["hard_pass"]:
                        raise ValueError(f"rescore {d['_source']} disagrees with the raw record for {key}")
                    continue
                entries[key] = {"origin": "post_hoc_rescore", "source": d["_source"],
                                "hard_pass": v["hard_pass"], **v["quality"]}
    rows = []
    summary: dict[tuple, list] = defaultdict(list)
    for (run_id, basis, ver), e in sorted(entries.items()):
        r = run_index[run_id]
        pre = _prefix(ctx, r.experiment_id, r.project_id, [r])
        note = "post-freeze secondary analysis; not comparable to frozen v2" if e["origin"] == "post_hoc_rescore" \
            else None
        rows.append(pre | {"validator_version": ver, "row_type": "run", "run_id": run_id, "path_id": r.path_id,
                           "quality_basis": basis, "origin": e["origin"], "source": e["source"],
                           "hard_pass": e["hard_pass"], "comparability_note": note,
                           **{m: e.get(m) for m in REPORT_METRICS}})
        summary[(r.experiment_id, r.project_id, basis, ver, e["origin"])].append((r, e))
    for (exp, project, basis, ver, origin), items in sorted(summary.items()):
        runs = [r for r, _ in items]
        rows.append(_prefix(ctx, exp, project, runs) | {
            "validator_version": ver, "row_type": "version_summary", "quality_basis": basis, "origin": origin,
            "n_reports": len(items), "n_hard_pass": sum(bool(e["hard_pass"]) for _, e in items),
            "comparability_note": "count within this validator version only"})
    versions = {r["validator_version"] for r in rows}
    ev = "insufficient_evidence" if not rows else "complete"
    if not rows:
        rows = [_insufficient(ctx, None, None, [], "no reporting-stage validation found", REPORT_COLS)]
    return Table("reporting_scores", REPORT_COLS, rows, ctx.status(ev), ev, notes=notes,
                 extra_meta={"validator_versions": sorted(v for v in versions if v)})


# --------------------------------------------------------------------------- 8. variability

VAR_COLS = PREFIX + ["path_id", "quantity", "n", "min", "max", "spread", "repeat_indices", "status_detail"]


def variability(ctx: Context) -> Table:
    rows = []
    for exp, project, pruns in _iter_groups(ctx):
        found = False
        for path, runs in _by_path(pruns).items():
            valid = _valid(runs)
            if not any(r.repeat_index > 0 for r in valid):
                continue
            found = True
            pre = _prefix(ctx, exp, project, runs) | {"path_id": path,
                                                      "repeat_indices": sorted(r.repeat_index for r in valid)}
            series = {"feasible": [float(r.feasibility.feasible) for r in valid],
                      "end_to_end_ms": [r.efficiency.end_to_end_ms for r in valid],
                      "api_latency_ms": [r.efficiency.total_api_latency_ms for r in valid],
                      "total_tokens": [float(r.efficiency.input_tokens + r.efficiency.output_tokens) for r in valid]}
            for s, m in METRIC_KEYS:
                series[f"gt.{s}.{m}"] = [r.quality.get(s, {}).get(m) for r in valid]
            for q, xs in series.items():
                st = _stats(xs)
                if st["n"]:
                    rows.append(pre | {"quantity": q, "n": st["n"], "min": st["min"], "max": st["max"],
                                       "spread": st["max"] - st["min"]})
        if not found:
            rows.append(_insufficient(ctx, exp, project, pruns, "no repeat runs (repeat_index > 0)", VAR_COLS))
    ev = "complete" if any(r["quantity"] for r in rows) else "insufficient_evidence"
    return Table("variability", VAR_COLS, rows, ctx.status(ev), ev, notes=[
        "Variability over repeats of the same path (non-void runs): n, min, max, spread = max - min. "
        "No significance tests are computed or implied.",
    ])
