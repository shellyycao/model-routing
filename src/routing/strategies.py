"""Routing strategies S1-S4.

S1-S3 are PROSPECTIVE: they receive only a TrainingView (held-out project physically excluded).
S4 is a RETROSPECTIVE reference built from the target project's executed outcomes. It is never
used for predictions, never logged as a counterfactual, and is not a deployable router.
"""

from __future__ import annotations

from src.contracts import STAGES, DecisionTrace, PathPrediction, Strategy, enumerate_paths, make_path_id, n_switches

from .config import RoutingConfig
from .data import RecordStore, TrainingView, evidence_ref, norm_project
from .estimation import estimate_stage_models, predict_additive, predict_workflow_aware
from .outcomes import aggregate_runs
from .router import build_trace


def _common(view: TrainingView, cfg: RoutingConfig, created_at: str) -> dict:
    return dict(target_project=view.held_out_project, held_out_project=view.held_out_project,
                training_projects=list(view.training_projects), objective=cfg.objective,
                settings=cfg.settings, router_version=cfg.router_version, config_hash=cfg.config_hash,
                created_at=created_at)


def decide_s1(view: TrainingView, cfg: RoutingConfig, created_at: str, est=None) -> list[DecisionTrace]:
    """One trace per single-model baseline. The policy path is fixed (X-X-X); the router reports whether
    it is predicted to satisfy the objective (stage-additive prediction from Experiment A)."""
    est = est if est is not None else estimate_stage_models(view)
    traces = []
    for m in view.model_aliases():
        pid = make_path_id([m] * len(STAGES))
        cands = predict_additive(view, est, [pid])
        traces.append(build_trace(strategy=Strategy.S1_SINGLE_MODEL, candidates=cands,
                                  extra_components={"policy_path_id": pid, "predictor": "stage_additive",
                                                    "note": "fixed single-model baseline; no oracle knowledge"},
                                  **_common(view, cfg, created_at)))
    return traces


def decide_s2(view: TrainingView, cfg: RoutingConfig, created_at: str, est=None) -> DecisionTrace:
    est = est if est is not None else estimate_stage_models(view)
    cands = predict_additive(view, est)
    return build_trace(strategy=Strategy.S2_GREEDY_TASK_ONLY, candidates=cands,
                       extra_components={"predictor": "stage_additive",
                                         "note": "task-only: Experiment A estimates only; cross-stage "
                                                 "interactions ignored"},
                       **_common(view, cfg, created_at))


def decide_s3(view: TrainingView, cfg: RoutingConfig, created_at: str, est=None) -> DecisionTrace:
    est = est if est is not None else estimate_stage_models(view)
    cands, details = predict_workflow_aware(view, cfg.interaction_shrinkage_k, est)
    shrink = {p: d.shrink for p, d in details.items() if d.shrink}
    return build_trace(strategy=Strategy.S3_WORKFLOW_AWARE, candidates=cands,
                       extra_components={"predictor": "stage_additive_plus_interaction_terms",
                                         "interaction_shrinkage_k": cfg.interaction_shrinkage_k,
                                         "interaction_shrinkage": shrink,
                                         "note": "interaction terms = observed training path outcome minus "
                                                 "stage-additive prediction, shrunk; not causally identified"},
                       **_common(view, cfg, created_at))


def decide_prospective(view: TrainingView, cfg: RoutingConfig, created_at: str) -> dict[str, list[DecisionTrace]]:
    est = estimate_stage_models(view)
    return {"S1": decide_s1(view, cfg, created_at, est), "S2": [decide_s2(view, cfg, created_at, est)],
            "S3": [decide_s3(view, cfg, created_at, est)]}


# ----------------------------------------------------------------------------- S4 oracle
def oracle_candidates(store: RecordStore, project: str, aliases: list[str]) -> list[PathPrediction]:
    """ACTUAL outcomes of `project` (retrospective) in PathPrediction form; uncertainty = repeat range."""
    runs = store.retrospective_outcomes(project)
    out = []
    for pid in enumerate_paths(aliases, len(STAGES)):
        po = aggregate_runs(pid, runs)
        if po.n_runs == 0:
            continue
        v = po.values
        unc = {}
        for k in v:
            xs = [r.get(k) for r in po.per_repeat.values() if r.get(k) is not None]
            if xs and k != "n_switches":
                unc[k] = (min(xs), max(xs))
        out.append(PathPrediction(
            path_id=pid, feasibility_prob=v.get("feasible"),
            quality={k: x for k, x in v.items() if "." in k and x is not None},
            end_to_end_ms=v.get("end_to_end_ms"), cost_usd=v.get("cost_usd"), total_tokens=v.get("total_tokens"),
            n_switches=n_switches(pid), uncertainty=unc,
            evidence=[evidence_ref(r) for r in runs if r.path_id == pid],
        ))
    return out


def oracle_s4(store: RecordStore, project: str, cfg: RoutingConfig, created_at: str,
              aliases: list[str] | None = None) -> DecisionTrace:
    """RETROSPECTIVE best / Pareto set from the target project's executed outcomes. NOT deployable."""
    p = norm_project(project)
    aliases = aliases or sorted({m for r in store.retrospective_outcomes(p) for m in r.models})
    cands = oracle_candidates(store, p, aliases)
    return build_trace(strategy=Strategy.S4_ORACLE, target_project=p, held_out_project=None, training_projects=[],
                       objective=cfg.objective, candidates=cands, settings=cfg.settings,
                       router_version=cfg.router_version, config_hash=cfg.config_hash, created_at=created_at,
                       extra_components={"retrospective_oracle": True, "deployable": False,
                                         "note": "S4 oracle: computed from the target project's OBSERVED outcomes "
                                                 "after the fact; a reference, not a router"})
