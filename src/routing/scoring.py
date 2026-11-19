"""Quantity access, constraint checks, Pareto dominance, lexicographic tolerance.

No weighted composite quality score is computed anywhere.
"""

from __future__ import annotations

from src.contracts import PathPrediction, QualityConstraint

# Quality metrics where LOWER is better (all other quality metrics: higher is better).
LOWER_IS_BETTER_QUALITY = frozenset({"reporting.unsupported_claim_count"})
EFFICIENCY_KEYS = ("cost_usd", "end_to_end_ms", "total_tokens", "n_switches")


def quantity(c: PathPrediction, key: str) -> float | None:
    if key in ("feasible", "feasibility_prob"):
        return c.feasibility_prob
    if key in ("end_to_end_ms", "cost_usd", "total_tokens"):
        return getattr(c, key)
    if key == "n_switches":
        return float(c.n_switches)
    return c.quality.get(key)


def fmt(v) -> str:
    if v is None:
        return "unavailable"
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def constraint_text(qc: QualityConstraint) -> str:
    return f"{qc.key} {qc.op} {fmt(float(qc.threshold))}"


def check_constraint(c: PathPrediction, qc: QualityConstraint) -> tuple[bool, str]:
    v = quantity(c, qc.key)
    if v is None:
        return False, f"no prediction for {qc.key}"
    ok = v >= qc.threshold if qc.op == ">=" else v <= qc.threshold
    if ok:
        return True, ""
    return False, f"predicted {qc.key}={fmt(v)} violates {qc.op} {fmt(float(qc.threshold))}"


def dominates(a: PathPrediction, b: PathPrediction, dims: list[tuple[str, str]]) -> bool:
    """a dominates b: at least as good on every dim and strictly better on one. dims: (key, 'max'|'min')."""
    strictly = False
    for key, sense in dims:
        va, vb = quantity(a, key), quantity(b, key)
        if sense == "max":
            va, vb = -va, -vb
        if va > vb:
            return False
        if va < vb:
            strictly = True
    return strictly


def pareto_front(cands: list[PathPrediction], dims: list[tuple[str, str]]) -> tuple[list[str], dict[str, str]]:
    """Non-dominated set. Removed paths get the reason 'dominated by <first dominator by path_id>'."""
    removed: dict[str, str] = {}
    ordered = sorted(cands, key=lambda c: c.path_id)
    for b in ordered:
        for a in ordered:
            if a.path_id != b.path_id and dominates(a, b, dims):
                removed[b.path_id] = f"dominated by {a.path_id}"
                break
    return [c.path_id for c in ordered if c.path_id not in removed], removed


def within_tolerance(v: float, best: float, tol: float) -> bool:
    return v <= best + tol * abs(best)
