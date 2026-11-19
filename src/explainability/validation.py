"""Two separate evaluations — never merged into one score:

1. COMPUTATIONAL FAITHFULNESS (check_faithfulness -> FaithfulnessCheck)
   Does the explanation say what the router actually computed? Every claim's bound parameters are
   re-resolved against the trace, its text is re-rendered from the fixed template, derived values are
   re-derived, "what would change" claims are re-verified by re-running the router, sentences not
   backed by a claim are flagged, and the router is replayed from the trace inputs.
   It says nothing about whether the predictions were right.

2. EMPIRICAL VALIDITY (validate_prediction / validate_log -> CounterfactualValidation)
   Did the logged counterfactual prediction match the executed outcome of the held-out project?
   Requires an intact hash chain; refuses modified predictions (check_against).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean

from src.contracts import (
    STAGES,
    CounterfactualPrediction,
    CounterfactualValidation,
    DecisionTrace,
    FaithfulnessCheck,
    Strategy,
    parse_path_id,
)
from src.routing.config import RouterSettings
from src.routing.counterfactual import HashChainLog, PredictionLog
from src.routing.data import RecordStore
from src.routing.outcomes import aggregate_runs
from src.routing.router import _with_threshold, replay, route, what_would_change

from .explanations import TEMPLATES, Explanation, Unresolvable, candidate_field, path_str, render_text, resolve

ALLOWED_DERIVED = {
    "transition": {"kind"},
    "swap_removed": {"alt", "alt_model"},
    "swap_missing": {"alt", "alt_model"},
    "uncertainty": {"quantity"},
    "uncertainty_point": {"quantity"},
    "interaction": {"quantity"},
}
SELECTED_CANDIDATE_KINDS = {"n_switches", "uncertainty", "uncertainty_point", "interaction"}


# ============================================================================ faithfulness
def _relation_errors(c: dict, trace: DecisionTrace, doc: dict, settings: RouterSettings) -> list[str]:
    kind, p, b = c["kind"], c["params"], c["bindings"]
    errs: list[str] = []
    sel = trace.selected_path_id
    if kind in SELECTED_CANDIDATE_KINDS:
        for path in b.values():
            for seg in path:
                if isinstance(seg, dict) and seg.get("path_id") != sel:
                    errs.append(f"refers to candidate {seg.get('path_id')} but the selected path is {sel}")
    if kind == "selected" and trace.no_feasible_path:
        errs.append("claims a selection but the trace has no feasible path")
    if kind == "no_feasible" and not trace.no_feasible_path:
        errs.append("claims no feasible path but the trace selected a path")
    if kind == "oracle_note" and trace.strategy != Strategy.S4_ORACLE:
        errs.append("oracle note on a non-oracle trace")
    if kind == "transition":
        expect = "stay" if p.get("from_model") == p.get("to_model") else "switch"
        if p.get("kind") != expect:
            errs.append(f"transition kind {p.get('kind')!r} but models imply {expect!r}")
    if kind in ("swap_removed", "swap_missing"):
        try:
            alt, sm = parse_path_id(p["alt"]), parse_path_id(sel)
            i = [s.value for s in STAGES].index(p["stage"])
            diff = [j for j in range(len(sm)) if alt[j] != sm[j]]
            if diff != [i] or alt[i] != p["alt_model"]:
                errs.append(f"{p['alt']} is not the single-stage swap to {p['alt_model']} at {p['stage']}")
        except (KeyError, ValueError, TypeError) as exc:
            errs.append(f"malformed swap claim: {exc}")
        cand_ids = {x.path_id for x in trace.candidates}
        if kind == "swap_missing" and p.get("alt") in cand_ids:
            errs.append(f"claims {p.get('alt')} has no prediction but it is a candidate")
        if kind == "swap_removed":
            expected = ["selection_steps", p.get("order"), "removed", p.get("alt")]
            if b.get("reason") != expected:
                errs.append("reason is not bound to the removal of this alternative")
    if kind == "decisive":
        dec = [s.order for s in trace.selection_steps if s.removed]
        if not dec or p.get("order") != max(dec):
            errs.append(f"decisive step claimed {p.get('order')}, trace implies {max(dec) if dec else None}")
    if kind in ("uncertainty", "uncertainty_point"):
        expect = ["candidates", {"path_id": sel}] + candidate_field(p.get("quantity", ""))
        if b.get("value") != expect:
            errs.append(f"value bound to {path_str(b.get('value', []))}, quantity implies {path_str(expect)}")
        if kind == "uncertainty":
            up = ["candidates", {"path_id": sel}, "uncertainty", p.get("quantity")]
            if b.get("lo") != up + [0] or b.get("hi") != up + [1]:
                errs.append("range not bound to this quantity's uncertainty interval")
    if kind == "interaction":
        expect = ["candidates", {"path_id": sel}, "interaction_terms", p.get("quantity")]
        if b.get("value") != expect:
            errs.append("interaction value not bound to this quantity's interaction term")
    if kind.startswith("wwc_"):
        errs += _wwc_errors(c, trace, settings)
    return errs


def _wwc_errors(c: dict, trace: DecisionTrace, settings: RouterSettings) -> list[str]:
    """Re-run the router to verify a 'what would change' claim (and recompute the minimal change)."""
    p, errs = c["params"], []
    fresh = what_would_change(trace.candidates, trace.objective, settings, trace.selected_path_id)
    match = [w for w in fresh if w["parameter"] == p.get("parameter")]
    if not match:
        return [f"unknown parameter {p.get('parameter')!r}"]
    w = match[0]
    if c["kind"] == "wwc_none":
        if w["flips"]:
            errs.append(f"claims no flip for {p['parameter']}, replay finds one at {w['flip_threshold']}")
        return errs
    if p.get("flip") != w["flip_threshold"]:
        errs.append(f"claimed flip threshold {p.get('flip')} is not the smallest change found by replay "
                    f"({w['flip_threshold']})")
    try:
        new = route(trace.candidates, _with_threshold(trace.objective, p["parameter"], p["flip"]),
                    settings).selected_path_id
    except Exception as exc:  # noqa: BLE001
        return errs + [f"replay with modified threshold failed: {exc}"]
    claimed_new = p.get("new") if c["kind"] == "wwc_flip" else None
    if new != claimed_new:
        errs.append(f"replay with {p['parameter']}={p['flip']} selects {new}, claim says {claimed_new}")
    if new == trace.selected_path_id:
        errs.append("claimed change does not alter the selection on replay")
    return errs


@dataclass
class ReplayResult:
    matches_selection: bool
    matches_steps: bool
    matches_sets: bool
    detail: str = ""


def replay_trace(trace: DecisionTrace) -> ReplayResult:
    res = replay(trace)
    steps_ok = [s.model_dump() for s in res.steps] == [s.model_dump() for s in trace.selection_steps]
    sets_ok = (res.feasible_path_ids == trace.feasible_path_ids and res.pareto_path_ids == trace.pareto_path_ids
               and res.inactive_criteria == trace.inactive_criteria)
    return ReplayResult(res.selected_path_id == trace.selected_path_id, steps_ok, sets_ok,
                        f"replay selected {res.selected_path_id}, trace says {trace.selected_path_id}")


def check_faithfulness(trace: DecisionTrace, explanation: Explanation, checked_at: str) -> FaithfulnessCheck:
    doc = trace.model_dump(mode="json")
    settings = RouterSettings.from_dict(trace.explanation_components.get("router_settings", {}))
    checks: list[dict] = []
    lines = [ln for ln in explanation.text.split("\n") if ln.strip()]
    claim_texts = set()
    for c in explanation.claims:
        errs: list[str] = []
        kind = c.get("kind")
        if kind not in TEMPLATES:
            errs.append(f"unknown claim kind {kind!r}")
        else:
            params, bindings = c.get("params", {}), c.get("bindings", {})
            for name, path in bindings.items():
                try:
                    actual = resolve(doc, path)
                except Unresolvable as exc:
                    errs.append(str(exc))
                    continue
                if params.get(name) != actual:
                    errs.append(f"{name}={params.get(name)!r} but trace {path_str(path)}={actual!r}")
            unbound = set(params) - set(bindings) - ALLOWED_DERIVED.get(kind, set())
            if unbound:
                errs.append(f"parameters not bound to the trace: {sorted(unbound)}")
            try:
                if render_text(kind, params) != c.get("text"):
                    errs.append("text differs from the template rendered with the claim's parameters")
            except (KeyError, IndexError) as exc:
                errs.append(f"template parameter missing: {exc}")
            if c.get("text") not in lines:
                errs.append("claim text does not appear in the explanation")
            errs += _relation_errors(c, trace, doc, settings)
        claim_texts.add(c.get("text"))
        checks.append({"claim": c.get("text"), "claim_id": c.get("claim_id"),
                       "source_field": "; ".join(f"{k}<-{path_str(v)}" for k, v in c.get("bindings", {}).items()),
                       "consistent": not errs, "detail": "; ".join(errs)})
    for ln in lines:
        if ln not in claim_texts:
            checks.append({"claim": ln, "claim_id": None, "source_field": None, "consistent": False,
                           "detail": "sentence is not backed by any trace-bound claim"})
    rp = replay_trace(trace)
    checks.append({"claim": "router replay from trace inputs", "claim_id": "replay", "source_field":
                   "candidates, objective, explanation_components.router_settings",
                   "consistent": rp.matches_selection and rp.matches_steps and rp.matches_sets,
                   "detail": f"{rp.detail}; steps match={rp.matches_steps}; sets match={rp.matches_sets}"})
    claim_checks = [c for c in checks if c["claim_id"] != "replay"]
    return FaithfulnessCheck(
        trace_id=trace.trace_id, trace_hash=trace.trace_hash(), explanation_hash=explanation.explanation_hash,
        checked_at=checked_at, explanation_kind="template", checks=checks,
        replay_matches_selection=rp.matches_selection, claims_checked=len(claim_checks),
        claims_consistent=sum(c["consistent"] for c in claim_checks),
        inconsistencies=[f"{c['claim']}: {c['detail']}" for c in checks if not c["consistent"]],
    )


# ============================================================================ empirical validity
EPS = 1e-12


def _sign(x: float) -> int:
    return 0 if abs(x) <= EPS else (1 if x > 0 else -1)


def validate_prediction(pred: CounterfactualPrediction, runs, validated_at: str) -> CounterfactualValidation:
    """Compare ONE logged prediction against executed Experiment B runs of its held-out project."""
    if pred.content_hash != pred.computed_hash():
        raise ValueError(f"prediction {pred.prediction_id} was modified after it was logged (hash mismatch)")
    runs = [r for r in runs if r.project_id.strip().lower() == pred.held_out_project]
    so, ao = aggregate_runs(pred.selected_path_id, runs), aggregate_runs(pred.alternative_path_id, runs)
    keys = sorted(pred.predicted_delta)
    asel = {k: so.values.get(k) for k in keys}
    aalt = {k: ao.values.get(k) for k in keys}
    adelta = {k: (aalt[k] - asel[k]) if aalt[k] is not None and asel[k] is not None else None for k in keys}
    spread: dict = {}
    common = sorted(set(so.per_repeat) & set(ao.per_repeat))
    for k in keys:
        ds = [ao.per_repeat[i][k] - so.per_repeat[i][k] for i in common
              if ao.per_repeat[i].get(k) is not None and so.per_repeat[i].get(k) is not None]
        spread[k] = (min(ds), max(ds)) if len(ds) >= 2 else None
    abs_err, direction, cover = {}, {}, {}
    for k in keys:
        pd_, ad = pred.predicted_delta.get(k), adelta[k]
        if pd_ is None or ad is None:
            abs_err[k], direction[k], cover[k] = None, None, None
            continue
        abs_err[k] = abs(pd_ - ad)
        direction[k] = _sign(pd_) == _sign(ad)
        iv = pred.predicted_delta_interval.get(k)
        cover[k] = None if iv is None else (iv[0] - EPS <= ad <= iv[1] + EPS)
    # Feasibility agreement (stored under direction_correct with a distinct key; see methodology).
    for role, pv, ov in (("selected", pred.predicted_selected.get("feasible"), so),
                         ("alternative", pred.predicted_alternative.get("feasible"), ao)):
        act = ov.values.get("feasible")
        direction[f"feasibility_agreement:{role}"] = None if pv is None or act is None else ((pv >= 0.5) == (act >= 0.5))
    notes = []
    for role, o in (("selected", so), ("alternative", ao)):
        if o.n_runs == 0:
            notes.append(f"{role} path {o.path_id} was not executed for {pred.held_out_project}")
        if o.n_void:
            notes.append(f"{role}: {o.n_void} void_infra run(s) excluded")
    v = CounterfactualValidation(
        prediction_id=pred.prediction_id, prediction_hash=pred.content_hash, validated_at=validated_at,
        actual_selected=asel, actual_alternative=aalt, actual_delta=adelta, actual_delta_spread=spread,
        n_repeats={"selected": so.n_runs - so.n_void, "alternative": ao.n_runs - ao.n_void},
        abs_error=abs_err, direction_correct=direction, interval_covers_actual=cover,
        actual_outcome={"selected": so.outcome_label, "alternative": ao.outcome_label},
        selected_run_ids=so.run_ids, alternative_run_ids=ao.run_ids, notes="; ".join(notes),
    )
    v.check_against(pred)
    return v


@dataclass
class ValidationRun:
    validations: list[CounterfactualValidation]
    predictions: list[CounterfactualPrediction]
    summary: dict = field(default_factory=dict)


def validate_log(prediction_log: str | Path, store: RecordStore, validated_at: str,
                 validation_log: str | Path | None = None) -> ValidationRun:
    log = PredictionLog(prediction_log)
    rep = log.verify()
    if not rep.ok:
        raise ValueError(f"refusing to validate: prediction log hash chain is broken: {rep.errors}")
    preds = log.predictions()
    out_log = HashChainLog(validation_log) if validation_log else None
    vals = []
    for pred in preds:
        v = validate_prediction(pred, store.retrospective_outcomes(pred.held_out_project), validated_at)
        v.check_against(pred)
        vals.append(v)
        if out_log:
            out_log.append(v.model_dump(mode="json"))
    return ValidationRun(vals, preds, summarise_validity(preds, vals))


def summarise_validity(preds: list[CounterfactualPrediction], vals: list[CounterfactualValidation]) -> dict:
    """Descriptive only (no significance claims). Failed predictions are counted, never dropped."""
    by_strat: dict[str, dict] = {}
    for p, v in zip(preds, vals):
        s = by_strat.setdefault(p.strategy.value, {"n_predictions": 0, "n_with_executed_outcomes": 0,
                                                     "per_quantity": {}, "failed_predictions": []})
        s["n_predictions"] += 1
        if v.n_repeats.get("selected", 0) and v.n_repeats.get("alternative", 0):
            s["n_with_executed_outcomes"] += 1
        failed = False
        for k in sorted(set(v.abs_error) | set(v.direction_correct)):
            pq = s["per_quantity"].setdefault(k, {"abs_errors": [], "direction": [], "coverage": []})
            if v.abs_error.get(k) is not None:
                pq["abs_errors"].append(v.abs_error[k])
            if v.direction_correct.get(k) is not None:
                pq["direction"].append(v.direction_correct[k])
                failed |= v.direction_correct[k] is False
            if v.interval_covers_actual.get(k) is not None:
                pq["coverage"].append(v.interval_covers_actual[k])
        if failed:
            s["failed_predictions"].append(p.prediction_id)
    for s in by_strat.values():
        for k, pq in s["per_quantity"].items():
            s["per_quantity"][k] = {
                "n": max(len(pq["abs_errors"]), len(pq["direction"])),
                "mean_abs_error": mean(pq["abs_errors"]) if pq["abs_errors"] else None,
                "max_abs_error": max(pq["abs_errors"]) if pq["abs_errors"] else None,
                "direction_or_agreement_rate": (sum(pq["direction"]) / len(pq["direction"])) if pq["direction"] else None,
                "interval_coverage_rate": (sum(pq["coverage"]) / len(pq["coverage"])) if pq["coverage"] else None,
            }
    return by_strat
