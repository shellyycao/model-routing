"""Transparent estimators (no RL, no dynamic programming). See docs/methodology.md.

Stage level (Experiment A, training projects only)
--------------------------------------------------
For each (stage, model, training project) the repeats are averaged into one "cell":
  feasible          = (#PASSED) / (#non-void records)           [INFRA_ERROR records are void]
  <stage>.<metric>  = mean quality over PASSED records           (conditional on success)
  stage_time_ms     = mean over PASSED, non-cache-hit records of
                      generation_ms + execution_ms + validation_ms + handoff_ms (recorded parts)
  tokens            = mean input_tokens + output_tokens over PASSED, non-cache-hit records
  cost_usd          = mean cost only if every PASSED record has cost_status 'estimated'; else None
Pooled estimate  = unweighted mean of the per-project cell values (projects are the LOPO unit).
Uncertainty      = [min, max] of the per-project cell values ("project range"). cost_usd is
                   None if ANY training project lacks a verified cost.

Path level
----------
S2 / stage-additive (interactions ignored):
  feasible = prod_s feasible(s, m_s);  interval = [prod lo, prod hi]
  <stage>.<metric> = stage estimate of the model used at that stage
  end_to_end_ms = sum_s stage_time_ms;  total_tokens = sum_s tokens;  cost = sum or None
S3 / workflow-aware:
  For every training project j with Experiment B runs of path p:
     r_j(p, q) = observed_j(p, q) - additive_j(p, q)
  (observed_j = outcomes.aggregate_runs on project j; additive_j uses project j's own cells.)
  n = #projects with a residual; s = n / (n + k)  (k = interaction_shrinkage_k)
  interaction term I(p, q) = s * mean_j r_j(p, q)
  prediction  = pooled additive(p, q) + I(p, q)
  interval    = [additive_lo + s * min_j r_j, additive_hi + s * max_j r_j]
  feasible prediction and interval are clipped to [0, 1].
  These are "interaction terms": they absorb error propagation, handoff effects, orchestration
  overhead and project idiosyncrasies alike; they are NOT causally identified handoff costs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import prod
from statistics import mean

from src.contracts import (
    STAGES,
    EvidenceRef,
    PathPrediction,
    StageBenchmarkRecord,
    StageStatus,
    enumerate_paths,
    n_switches,
    parse_path_id,
)

from .data import TrainingView, evidence_ref, norm_project
from .outcomes import aggregate_runs

Triple = tuple[float, float, float]          # (value, lo, hi)
EXCLUDED_STAGE_STATUSES = frozenset({StageStatus.INFRA_ERROR, StageStatus.BLOCKED_BY_INVALID_ARTIFACT,
                                     StageStatus.NOT_RUN_UPSTREAM_FAILURE})
PATH_EFFICIENCY = ("end_to_end_ms", "total_tokens", "cost_usd")


def _require_view(view) -> TrainingView:
    if not isinstance(view, TrainingView):
        raise TypeError("estimators accept only a TrainingView (held-out project physically excluded)")
    return view


# ----------------------------------------------------------------------------- stage level
def _stage_time(rec) -> float | None:
    t = rec.timings
    if t.generation_ms is None:
        return None
    return sum(x for x in (t.generation_ms, t.execution_ms, t.validation_ms, t.handoff_ms) if x is not None)


def stage_cell(records: list[StageBenchmarkRecord]) -> dict[str, float | None]:
    """One (stage, model, project) cell from its repeats."""
    # Void: infrastructure errors. Upstream-attributed (v1.2): BLOCKED_BY_INVALID_ARTIFACT and
    # NOT_RUN_UPSTREAM_FAILURE are never counted against this stage's own model.
    valid = [r for r in records if r.record.status not in EXCLUDED_STAGE_STATUSES]
    if not valid:
        return {}
    stage = valid[0].stage.value
    passed = [r.record for r in valid if r.record.status == StageStatus.PASSED]
    cell: dict[str, float | None] = {"feasible": len(passed) / len(valid)}
    metrics = sorted({m for r in passed if r.validation for m in r.validation.quality})
    for m in metrics:
        xs = [r.validation.quality[m] for r in passed if r.validation and m in r.validation.quality]
        cell[f"{stage}.{m}"] = mean(xs)
    fresh = [r for r in passed if not r.cache_hit]
    times = [t for t in (_stage_time(r) for r in fresh) if t is not None]
    cell["stage_time_ms"] = mean(times) if times else None
    toks = [r.input_tokens + r.output_tokens for r in fresh if r.input_tokens is not None and r.output_tokens is not None]
    cell["tokens"] = mean(toks) if toks else None
    costs_ok = passed and all(r.cost_status == "estimated" and r.cost_usd is not None for r in passed)
    cell["cost_usd"] = mean(r.cost_usd for r in passed) if costs_ok else None
    return cell


@dataclass
class StageModelEstimate:
    stage: str
    model: str
    values: dict[str, Triple | None]                  # quantity -> (pooled, lo, hi) or None
    per_project: dict[str, dict[str, float | None]]   # project -> cell
    n_records: int
    n_void: int
    evidence: list[EvidenceRef] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _pool(per_project: dict[str, dict[str, float | None]], key: str, strict: bool) -> Triple | None:
    xs = [c.get(key) for c in per_project.values()]
    if strict and (not xs or any(x is None for x in xs)):
        return None
    xs = [x for x in xs if x is not None]
    if not xs:
        return None
    return (mean(xs), min(xs), max(xs))


def estimate_stage_models(view: TrainingView) -> dict[tuple[str, str], StageModelEstimate]:
    view = _require_view(view)
    groups: dict[tuple[str, str, str], list[StageBenchmarkRecord]] = {}
    for r in view.stage_records:
        groups.setdefault((r.stage.value, r.model_alias, norm_project(r.project_id)), []).append(r)
    out: dict[tuple[str, str], StageModelEstimate] = {}
    for (stage, model) in sorted({(s, m) for s, m, _ in groups}):
        recs = [r for (s, m, _), rs in groups.items() if (s, m) == (stage, model) for r in rs]
        per_project = {p: c for (s, m, p), rs in sorted(groups.items()) if (s, m) == (stage, model)
                       for c in [stage_cell(rs)] if c}
        keys = sorted({k for c in per_project.values() for k in c})
        values = {k: _pool(per_project, k, strict=(k == "cost_usd")) for k in keys}
        notes = []
        if values.get("cost_usd") is None:
            notes.append("cost_usd unavailable: at least one training record lacks a verified price")
        out[(stage, model)] = StageModelEstimate(
            stage=stage, model=model, values=values, per_project=per_project,
            n_records=len(recs), n_void=sum(r.record.status in EXCLUDED_STAGE_STATUSES for r in recs),
            evidence=sorted((evidence_ref(r) for r in recs), key=lambda e: (e.project_id, e.run_id)),
            notes=notes,
        )
    return out


# ----------------------------------------------------------------------------- path level
def additive(path_id: str, getter) -> dict[str, Triple | None]:
    """Stage-additive combination. getter(stage, model) -> dict quantity -> Triple | None (or None)."""
    models = parse_path_id(path_id)
    cells = [getter(STAGES[i].value, m) for i, m in enumerate(models)]
    out: dict[str, Triple | None] = {}
    if any(c is None or c.get("feasible") is None for c in cells):
        out["feasible"] = None
    else:
        fs = [c["feasible"] for c in cells]
        out["feasible"] = (prod(f[0] for f in fs), prod(f[1] for f in fs), prod(f[2] for f in fs))
    for c in cells:
        for k, v in (c or {}).items():
            if "." in k:
                out[k] = v
    for src, dst in (("stage_time_ms", "end_to_end_ms"), ("tokens", "total_tokens"), ("cost_usd", "cost_usd")):
        parts = [None if c is None else c.get(src) for c in cells]
        out[dst] = None if any(p is None for p in parts) else tuple(sum(p[i] for p in parts) for i in range(3))
    return out


def _to_prediction(path_id: str, q: dict[str, Triple | None], evidence: list[EvidenceRef],
                   interaction: dict[str, float] | None = None) -> PathPrediction:
    def val(k):
        return None if q.get(k) is None else q[k][0]
    quality = {k: v[0] for k, v in q.items() if "." in k and v is not None}
    unc = {k: (v[1], v[2]) for k, v in q.items() if v is not None}
    uniq = {(e.project_id, e.experiment_id, e.run_id): e for e in evidence}
    return PathPrediction(
        path_id=path_id, feasibility_prob=val("feasible"), quality=quality,
        end_to_end_ms=val("end_to_end_ms"), cost_usd=val("cost_usd"), total_tokens=val("total_tokens"),
        n_switches=n_switches(path_id), interaction_terms=dict(interaction or {}), uncertainty=unc,
        evidence=[uniq[k] for k in sorted(uniq)],
    )


def candidate_paths(view: TrainingView) -> list[str]:
    return enumerate_paths(view.model_aliases(), len(STAGES))


def _path_evidence(path_id: str, est) -> list[EvidenceRef]:
    ev: list[EvidenceRef] = []
    for i, m in enumerate(parse_path_id(path_id)):
        e = est.get((STAGES[i].value, m))
        if e:
            ev.extend(e.evidence)
    return ev


def predict_additive(view: TrainingView, est=None, paths: list[str] | None = None) -> list[PathPrediction]:
    """S2 (and S1) predictions: stage-additive, interactions ignored."""
    view = _require_view(view)
    est = est if est is not None else estimate_stage_models(view)
    out = []
    for p in paths or candidate_paths(view):
        q = additive(p, lambda s, m: est[(s, m)].values if (s, m) in est else None)
        out.append(_to_prediction(p, q, _path_evidence(p, est)))
    return out


@dataclass
class InteractionEstimate:
    path_id: str
    residuals: dict[str, dict[str, float]]   # quantity -> project -> residual
    shrink: dict[str, float]                 # quantity -> s = n/(n+k)
    terms: dict[str, float]                  # quantity -> s * mean residual
    run_evidence: list[EvidenceRef]


def estimate_interactions(view: TrainingView, est, path_id: str, k: float) -> InteractionEstimate:
    view = _require_view(view)
    residuals: dict[str, dict[str, float]] = {}
    ev: list[EvidenceRef] = []
    for proj in view.training_projects:
        runs = [r for r in view.workflow_runs if norm_project(r.project_id) == proj and r.path_id == path_id]
        if not runs:
            continue
        ev.extend(evidence_ref(r) for r in runs)
        obs = aggregate_runs(path_id, runs).values

        def getter(s, m, proj=proj):
            e = est.get((s, m))
            c = e.per_project.get(proj) if e else None
            return None if c is None else {kk: (None if v is None else (v, v, v)) for kk, v in c.items()}

        add = additive(path_id, getter)
        for q, a in add.items():
            o = obs.get(q)
            if a is None or o is None:
                continue
            residuals.setdefault(q, {})[proj] = o - a[0]
    shrink = {q: len(r) / (len(r) + k) for q, r in residuals.items()}
    terms = {q: shrink[q] * mean(r.values()) for q, r in residuals.items()}
    return InteractionEstimate(path_id=path_id, residuals=residuals, shrink=shrink, terms=terms, run_evidence=ev)


def predict_workflow_aware(view: TrainingView, k: float, est=None,
                           paths: list[str] | None = None) -> tuple[list[PathPrediction], dict[str, InteractionEstimate]]:
    """S3 predictions: stage-additive + shrunk interaction terms from training Experiment B runs."""
    view = _require_view(view)
    est = est if est is not None else estimate_stage_models(view)
    preds, details = [], {}
    for p in paths or candidate_paths(view):
        q = additive(p, lambda s, m: est[(s, m)].values if (s, m) in est else None)
        ie = estimate_interactions(view, est, p, k)
        details[p] = ie
        adj: dict[str, Triple | None] = dict(q)
        for qty, term in ie.terms.items():
            base = q.get(qty)
            if base is None:
                continue
            s, rs = ie.shrink[qty], ie.residuals[qty].values()
            v, lo, hi = base[0] + term, base[1] + s * min(rs), base[2] + s * max(rs)
            if qty == "feasible":
                v, lo, hi = (min(1.0, max(0.0, x)) for x in (v, lo, hi))
            adj[qty] = (v, lo, hi)
        terms = {qty: t for qty, t in ie.terms.items() if q.get(qty) is not None}
        preds.append(_to_prediction(p, adj, _path_evidence(p, est) + ie.run_evidence, terms))
    return preds, details
