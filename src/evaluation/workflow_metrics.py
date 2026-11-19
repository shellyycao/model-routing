"""Per-path summaries derived ONLY from saved raw WorkflowRunRecords (no composite score).

Inputs: the JSONL written by src.storage.RunStore (results/raw/workflow_runs/<experiment_id>.jsonl).
Nothing here is stored in place of the raw records; summaries are recomputed on demand.

Per (project_id, path_id):
  A. Feasibility  n_runs, n_feasible, n_infeasible, n_void_infra,
                  feasibility_rate = n_feasible / (n_feasible + n_infeasible)   (void_infra excluded;
                  None if no valid run), first_failure_stage counts, failure_type counts.
  B. Quality      per stage and metric: mean/min/max/n over runs in which that stage was validated,
                  separately for ground truth (`quality`) and the conditional reference
                  (`conditional_quality`). Failed stages' quality is included (it was measured);
                  not-run stages have none.
  C. Efficiency   mean/min/max/n of end_to_end_ms and total_api_latency_ms (KEPT SEPARATE: lower API
                  latency is not lower end-to-end time), execution/validation/handoff ms, tokens,
                  n_calls, n_cache_hits, n_switches. Cost: mean over runs only when EVERY run has a
                  known cost; otherwise None with cost_status "unavailable"/"partial" (never 0).
Variability is reported as min/max over repeats; no significance claims.

`group_by_switching` aggregates paths into same-model (n_switches == 0) vs cross-model groups,
per project, using the per-run records (not averages of averages).
Records from different experiment_ids are refused (primary and shared-prefix results never mix).
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from src.contracts import WorkflowRunRecord, is_single_model


def load_runs(path: str | Path) -> list[WorkflowRunRecord]:
    p = Path(path)
    if not p.exists():
        return []
    return [WorkflowRunRecord.model_validate_json(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _stats(values: Iterable[float | None]) -> dict | None:
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return None
    return {"mean": sum(vals) / len(vals), "min": min(vals), "max": max(vals), "n": len(vals)}


def _check_single_experiment(runs: list[WorkflowRunRecord]) -> None:
    exps = {r.experiment_id for r in runs}
    if len(exps) > 1:
        raise ValueError(f"records from several experiments {sorted(exps)}; summarise each separately")


def summarize_runs(runs: list[WorkflowRunRecord]) -> dict:
    """Summary of an arbitrary set of runs (one path, or a group)."""
    outcomes = Counter(r.feasibility.outcome for r in runs)
    valid = outcomes["feasible"] + outcomes["infeasible"]
    quality: dict[str, dict] = defaultdict(dict)
    cond: dict[str, dict] = defaultdict(dict)
    for target, attr in ((quality, "quality"), (cond, "conditional_quality")):
        keys = {(s, m) for r in runs for s, q in getattr(r, attr).items() for m in q}
        for s, m in sorted(keys):
            target[s][m] = _stats(getattr(r, attr).get(s, {}).get(m) for r in runs)
    eff = [r.efficiency for r in runs]
    costs = [e.cost_usd for e in eff]
    statuses = Counter(e.cost_status for e in eff)
    if runs and all(c is not None for c in costs):
        cost, cost_status = _stats(costs), ("estimated" if set(statuses) <= {"estimated", "not_incurred"}
                                            else "partial")
    else:
        cost, cost_status = None, ("unavailable" if not any(c is not None for c in costs) else "partial")
    return {
        "n_runs": len(runs),
        "n_feasible": outcomes["feasible"],
        "n_infeasible": outcomes["infeasible"],
        "n_void_infra": outcomes["void_infra"],
        "feasibility_rate": outcomes["feasible"] / valid if valid else None,
        "first_failure_stage": dict(Counter(r.feasibility.first_failure_stage.value
                                            for r in runs if r.feasibility.first_failure_stage)),
        "failure_type": dict(Counter(r.feasibility.failure_type.value for r in runs if r.feasibility.failure_type)),
        "quality": dict(quality),
        "conditional_quality": dict(cond),
        "efficiency": {
            "end_to_end_ms": _stats(e.end_to_end_ms for e in eff),
            "total_api_latency_ms": _stats(e.total_api_latency_ms for e in eff),
            "total_execution_ms": _stats(e.total_execution_ms for e in eff),
            "total_validation_ms": _stats(e.total_validation_ms for e in eff),
            "total_handoff_ms": _stats(e.total_handoff_ms for e in eff),
            "input_tokens": _stats(e.input_tokens for e in eff),
            "output_tokens": _stats(e.output_tokens for e in eff),
            "n_calls": _stats(e.n_calls for e in eff),
            "n_cache_hits": sum(e.n_cache_hits for e in eff),
            "handoff_bytes_total": _stats(e.handoff_bytes_total for e in eff),
            "cost_usd": cost,
            "cost_status": cost_status,
        },
        "run_ids": [r.run_id for r in runs],
    }


def summarize_paths(runs: list[WorkflowRunRecord]) -> dict[str, dict[str, dict]]:
    """{project_id: {path_id: summary}} with n_switches and same_model flags."""
    _check_single_experiment(runs)
    groups: dict[tuple[str, str], list[WorkflowRunRecord]] = defaultdict(list)
    for r in runs:
        groups[(r.project_id, r.path_id)].append(r)
    out: dict[str, dict[str, dict]] = defaultdict(dict)
    for (proj, path), rs in sorted(groups.items()):
        s = summarize_runs(rs)
        s["n_switches"] = rs[0].efficiency.n_switches
        s["same_model"] = is_single_model(path)
        s["repeat_indices"] = sorted(r.repeat_index for r in rs)
        out[proj][path] = s
    return dict(out)


def group_by_switching(runs: list[WorkflowRunRecord]) -> dict[str, dict[str, dict]]:
    """{project_id: {"same_model": summary, "cross_model": summary}}."""
    _check_single_experiment(runs)
    groups: dict[str, dict[str, list]] = defaultdict(lambda: {"same_model": [], "cross_model": []})
    for r in runs:
        groups[r.project_id]["same_model" if is_single_model(r.path_id) else "cross_model"].append(r)
    return {p: {k: summarize_runs(v) | {"paths": sorted({r.path_id for r in v})} for k, v in g.items()}
            for p, g in sorted(groups.items())}


def summarize_file(path: str | Path) -> dict:
    runs = load_runs(path)
    return {"source": str(path), "experiment_ids": sorted({r.experiment_id for r in runs}),
            "per_path": summarize_paths(runs), "by_switching": group_by_switching(runs)}


if __name__ == "__main__":  # pragma: no cover
    import sys
    print(json.dumps(summarize_file(sys.argv[1]), indent=2))
