"""Constraint -> Pareto -> lexicographic router, recorded step by step as SelectionSteps.

Order of steps (every step is recorded, including no-op and inactive ones):
  1. feasibility_threshold   predicted feasibility_prob >= objective.min_feasibility_prob
                             (None = no evidence -> removed)
  2. quality_constraint      one step per constraint, in config order (None -> removed)
     -> if nothing remains: a `no_feasible_path` step and selection stops.
  3. pareto_filter           non-dominated set over: feasibility_prob (max), the configured quality
                             keys (max, or min for LOWER_IS_BETTER_QUALITY), every active preference
                             key (min). A dimension with any None among the remaining paths is dropped
                             (and listed in the step detail).
  4. lexicographic_preference  one step per preference key. If any remaining path has None for the key
                             (e.g. cost_usd while prices are unverified) the step is INACTIVE and
                             skipped; None is never treated as 0. Otherwise keep paths with
                             value <= best + tie_tolerance * |best|.
  5. tie_break               highest predicted feasibility_prob, then path_id (alphabetical).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from src.contracts import (
    DecisionTrace,
    PathPrediction,
    RoutingObjective,
    SelectionStep,
    Strategy,
)

from .config import RouterSettings
from .scoring import (
    LOWER_IS_BETTER_QUALITY,
    check_constraint,
    constraint_text,
    fmt,
    pareto_front,
    quantity,
    within_tolerance,
)


@dataclass
class RoutingResult:
    candidates: list[PathPrediction]          # annotated copies (satisfies_constraints, violated_constraints)
    steps: list[SelectionStep]
    feasible_path_ids: list[str]
    pareto_path_ids: list[str]
    selected_path_id: str | None
    inactive_criteria: list[str] = field(default_factory=list)

    @property
    def no_feasible_path(self) -> bool:
        return self.selected_path_id is None


def _annotate(c: PathPrediction, obj: RoutingObjective) -> PathPrediction:
    violated = []
    if c.feasibility_prob is None or c.feasibility_prob < obj.min_feasibility_prob:
        violated.append(f"feasibility_prob >= {fmt(float(obj.min_feasibility_prob))}")
    for qc in obj.quality_constraints:
        if not check_constraint(c, qc)[0]:
            violated.append(constraint_text(qc))
    return c.model_copy(update={"satisfies_constraints": not violated, "violated_constraints": violated})


def pareto_dims(remaining: list[PathPrediction], obj: RoutingObjective,
                settings: RouterSettings) -> tuple[list[tuple[str, str]], list[str]]:
    if settings.pareto_quality_keys == "all":
        qkeys = sorted({k for c in remaining for k in c.quality})
    else:
        qkeys = list(settings.pareto_quality_keys)
    dims = [("feasibility_prob", "max")]
    dims += [(k, "min" if k in LOWER_IS_BETTER_QUALITY else "max") for k in qkeys]
    dims += [(k, "min") for k in obj.preference_order]
    used, dropped = [], []
    for k, s in dims:
        (used if all(quantity(c, k) is not None for c in remaining) else dropped).append((k, s))
    return used, [k for k, _ in dropped]


def route(candidates: list[PathPrediction], objective: RoutingObjective,
          settings: RouterSettings | None = None) -> RoutingResult:
    settings = settings or RouterSettings()
    cands = [_annotate(c, objective) for c in sorted(candidates, key=lambda c: c.path_id)]
    if len({c.path_id for c in cands}) != len(cands):
        raise ValueError("duplicate candidate path_id")
    by_id = {c.path_id: c for c in cands}
    steps: list[SelectionStep] = []
    remaining = [c.path_id for c in cands]

    def add(rule, detail, removed=None, inactive=False, reason=None):
        steps.append(SelectionStep(order=len(steps), rule=rule, detail=detail, removed=removed or {},
                                   remaining=list(remaining), inactive=inactive, inactive_reason=reason))

    # 1. feasibility threshold
    thr = objective.min_feasibility_prob
    removed = {}
    for pid in remaining:
        p = by_id[pid].feasibility_prob
        if p is None:
            removed[pid] = "no feasibility prediction (no evidence)"
        elif p < thr:
            removed[pid] = f"predicted feasibility_prob={fmt(p)} < {fmt(float(thr))}"
    remaining = [p for p in remaining if p not in removed]
    add("feasibility_threshold", f"feasibility_prob >= {fmt(float(thr))}", removed)

    # 2. quality constraints
    for qc in objective.quality_constraints:
        removed = {}
        for pid in remaining:
            ok, why = check_constraint(by_id[pid], qc)
            if not ok:
                removed[pid] = why
        remaining = [p for p in remaining if p not in removed]
        add("quality_constraint", constraint_text(qc), removed)

    feasible = list(remaining)
    if not feasible:
        add("no_feasible_path", "no candidate satisfies the feasibility threshold and quality constraints")
        return RoutingResult(cands, steps, [], [], None, [])

    # 3. Pareto filter
    rem_c = [by_id[p] for p in remaining]
    dims, dropped = pareto_dims(rem_c, objective, settings)
    front, removed = pareto_front(rem_c, dims)
    remaining = front
    detail = "non-dominated over " + ", ".join(f"{k}({s})" for k, s in dims)
    if dropped:
        detail += "; dropped (unavailable): " + ", ".join(dropped)
    add("pareto_filter", detail, removed)
    pareto = list(front)

    # 4. lexicographic preferences
    inactive: list[str] = []
    tol = objective.tie_tolerance
    for key in objective.preference_order:
        vals = {p: quantity(by_id[p], key) for p in remaining}
        missing = sorted(p for p, v in vals.items() if v is None)
        if missing:
            inactive.append(key)
            add("lexicographic_preference", f"minimise {key}", inactive=True,
                reason=f"{key} unavailable (None) for {len(missing)} of {len(vals)} remaining paths; "
                       f"skipped, not treated as 0")
            continue
        best = min(vals.values())
        removed = {p: f"{key}={fmt(v)} worse than best {fmt(best)} beyond tolerance {fmt(float(tol))}"
                   for p, v in vals.items() if not within_tolerance(v, best, tol)}
        remaining = [p for p in remaining if p not in removed]
        add("lexicographic_preference", f"minimise {key} (relative tie tolerance {fmt(float(tol))})", removed)

    # 5. tie-break
    order = sorted(remaining, key=lambda p: (-by_id[p].feasibility_prob, p))
    selected = order[0]
    removed = {p: f"tie-break: {selected} ranks first (higher feasibility_prob, then path_id)" for p in order[1:]}
    remaining = [selected]
    add("tie_break", "highest predicted feasibility_prob, then alphabetical path_id"
        if removed else "single path remains; no tie", removed)
    return RoutingResult(cands, steps, feasible, pareto, selected, inactive)


# ----------------------------------------------------------------------------- what would change
def _with_threshold(obj: RoutingObjective, param: str, value: float) -> RoutingObjective:
    if param == "min_feasibility_prob":
        return obj.model_copy(update={"min_feasibility_prob": value})
    idx = int(param.split("[")[1].rstrip("]"))
    qcs = [qc.model_copy() for qc in obj.quality_constraints]
    qcs[idx] = qcs[idx].model_copy(update={"threshold": value})
    return obj.model_copy(update={"quality_constraints": qcs})


def threshold_parameters(obj: RoutingObjective) -> list[tuple[str, str, str, float]]:
    """(parameter, quantity key, op, current value)."""
    out = [("min_feasibility_prob", "feasibility_prob", ">=", float(obj.min_feasibility_prob))]
    out += [(f"quality_constraints[{i}]", qc.key, qc.op, float(qc.threshold))
            for i, qc in enumerate(obj.quality_constraints)]
    return out


def what_would_change(candidates: list[PathPrediction], objective: RoutingObjective,
                      settings: RouterSettings, baseline_selected: str | None) -> list[dict]:
    """Smallest single-threshold change that flips the selection, found by RE-RUNNING the router.

    Selection only changes when a threshold crosses a candidate's predicted value, so the search
    tries every such breakpoint (the value itself and the next representable float beyond it).
    """
    out = []
    for param, key, op, cur in threshold_parameters(objective):
        vals = sorted({v for c in candidates if (v := quantity(c, key)) is not None})
        trials = set()
        for v in vals:
            trials.add(v)
            trials.add(math.nextafter(v, math.inf if op == ">=" else -math.inf))
        if param == "min_feasibility_prob":
            trials = {t for t in trials if 0.0 <= t <= 1.0}
        trials.discard(cur)
        best = None
        for t in sorted(trials, key=lambda t: (abs(t - cur), t)):
            new = route(candidates, _with_threshold(objective, param, t), settings).selected_path_id
            if new != baseline_selected:
                best = (t, new)
                break
        entry = {"parameter": param, "quantity": key, "op": op, "current": cur}
        if best is None:
            entry.update({"flip_threshold": None, "change": None, "direction": None, "new_selected": None,
                          "flips": False})
        else:
            t, new = best
            tighten = (t > cur) if op == ">=" else (t < cur)
            entry.update({"flip_threshold": t, "change": t - cur, "direction": "tighten" if tighten else "relax",
                          "new_selected": new, "flips": True})
        out.append(entry)
    return out


# ----------------------------------------------------------------------------- traces
def build_trace(*, strategy: Strategy, target_project: str, held_out_project: str | None,
                training_projects: list[str], objective: RoutingObjective, candidates: list[PathPrediction],
                settings: RouterSettings, router_version: str, config_hash: str, created_at: str,
                extra_components: dict | None = None) -> DecisionTrace:
    res = route(candidates, objective, settings)
    components = {
        "router_settings": settings.to_dict(),
        "what_would_change": what_would_change(res.candidates, objective, settings, res.selected_path_id),
        **(extra_components or {}),
    }
    training_hash = DecisionTrace.compute_training_data_hash(res.candidates)
    trace_id = f"{strategy.value}:{target_project}:{objective.objective_id}:{training_hash[:12]}"
    if extra_components and extra_components.get("policy_path_id"):
        trace_id += f":{extra_components['policy_path_id']}"
    return DecisionTrace(
        trace_id=trace_id, created_at=created_at, strategy=strategy, target_project=target_project,
        held_out_project=held_out_project, training_projects=training_projects,
        training_data_hash=training_hash, objective=objective, candidates=res.candidates,
        selection_steps=res.steps, feasible_path_ids=res.feasible_path_ids, pareto_path_ids=res.pareto_path_ids,
        selected_path_id=res.selected_path_id, no_feasible_path=res.no_feasible_path,
        inactive_criteria=res.inactive_criteria, explanation_components=components,
        router_version=router_version, config_hash=config_hash,
    )


def replay(trace: DecisionTrace) -> RoutingResult:
    """Re-run the router from the inputs recorded in the trace."""
    settings = RouterSettings.from_dict(trace.explanation_components.get("router_settings", {}))
    return route(trace.candidates, trace.objective, settings)
