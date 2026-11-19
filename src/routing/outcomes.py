"""Aggregation of executed Experiment B runs for one (project, path).

Used in three places with the SAME rules:
  * S3 training residuals (training projects only, via TrainingView),
  * counterfactual validation (held-out project, after predictions are logged),
  * the S4 retrospective oracle (held-out project, after predictions are logged).

Rules:
  * runs with outcome ``void_infra`` are excluded (infrastructure, not model behaviour) and counted;
  * ``feasible`` = fraction of non-void runs that are feasible;
  * quality "<stage>.<metric>" = mean over FEASIBLE runs (quality is conditional on feasibility);
  * end_to_end_ms / total_tokens = mean over feasible runs with no cache hits (cached stages make
    efficiency incomparable) and a recorded value;
  * cost_usd = mean only if every such run has a verified cost (cost_status 'estimated'), else None.
    A missing price is never 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean

from src.contracts import WorkflowRunRecord, n_switches


@dataclass
class PathOutcome:
    path_id: str
    n_runs: int
    n_void: int
    n_feasible: int
    values: dict[str, float | None]          # quantity key -> mean (see module docstring)
    per_repeat: dict[int, dict[str, float | None]] = field(default_factory=dict)
    run_ids: list[str] = field(default_factory=list)
    outcome_label: str = "not_executed"       # feasible | infeasible | mixed | void_infra | not_executed


def run_values(r: WorkflowRunRecord) -> dict[str, float | None]:
    """Quantities of ONE run (None where not applicable)."""
    v: dict[str, float | None] = {"feasible": 1.0 if r.feasibility.feasible else 0.0,
                                  "n_switches": float(n_switches(r.path_id))}
    if r.feasibility.feasible:
        for stage, metrics in r.quality.items():
            for m, x in metrics.items():
                v[f"{stage}.{m}"] = float(x)
        eff = r.efficiency
        clean = eff.n_cache_hits == 0
        v["end_to_end_ms"] = eff.end_to_end_ms if clean else None
        v["total_tokens"] = float(eff.input_tokens + eff.output_tokens) if clean else None
        v["cost_usd"] = eff.cost_usd if (clean and eff.cost_status == "estimated" and eff.cost_usd is not None) else None
    return v


def aggregate_runs(path_id: str, runs: list[WorkflowRunRecord] | tuple[WorkflowRunRecord, ...]) -> PathOutcome:
    runs = [r for r in runs if r.path_id == path_id]
    valid = [r for r in runs if r.feasibility.outcome != "void_infra"]
    n_void = len(runs) - len(valid)
    feas = [r for r in valid if r.feasibility.feasible]
    values: dict[str, float | None] = {"n_switches": float(n_switches(path_id))}
    values["feasible"] = (len(feas) / len(valid)) if valid else None
    per_run = [run_values(r) for r in feas]
    qkeys = sorted({k for pv in per_run for k in pv if "." in k})
    for k in qkeys:
        xs = [pv[k] for pv in per_run if pv.get(k) is not None]
        values[k] = mean(xs) if xs else None
    for k in ("end_to_end_ms", "total_tokens"):
        xs = [pv[k] for pv in per_run if pv.get(k) is not None]
        values[k] = mean(xs) if xs else None
    costs = [pv.get("cost_usd") for pv in per_run]
    values["cost_usd"] = mean(costs) if costs and all(c is not None for c in costs) else None
    if not runs:
        label = "not_executed"
    elif not valid:
        label = "void_infra"
    elif len(feas) == len(valid):
        label = "feasible"
    elif not feas:
        label = "infeasible"
    else:
        label = "mixed"
    return PathOutcome(
        path_id=path_id, n_runs=len(runs), n_void=n_void, n_feasible=len(feas), values=values,
        per_repeat={r.repeat_index: run_values(r) for r in valid},
        run_ids=sorted(r.run_id for r in runs), outcome_label=label,
    )
