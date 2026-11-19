"""Additive, post-hoc cost estimates for the frozen S1--S3 routing machinery.

This module never mutates source records or the frozen estimator.  It deep-copies the
ordinary stage estimates and replaces only their ``cost_usd`` quantity using the rules in
``docs/COST_AWARE_ROUTER_RULES.md``.
"""

from __future__ import annotations

import copy
from collections import defaultdict
from statistics import mean
from typing import Literal

from src.bedrock.models import ModelRegistry
from src.contracts import STAGES, StageStatus, Strategy, make_path_id

from .config import RoutingConfig
from .data import TrainingView, norm_project
from .estimation import estimate_stage_models, predict_additive, predict_workflow_aware
from .router import build_trace

CostScope = Literal["all_non_void_executed", "passed_only"]
EXECUTED = frozenset({StageStatus.PASSED, StageStatus.FAILED})


def record_cost_usd(record, alias: str, registry: ModelRegistry) -> float | None:
    """Price one fresh stage record from its recorded input/output token split."""
    if record.cache_hit:
        return None
    pricing = registry.get(alias).pricing
    if not pricing.verified or record.input_tokens is None or record.output_tokens is None:
        return None
    return (
        record.input_tokens * pricing.input_per_mtok
        + record.output_tokens * pricing.output_per_mtok
    ) / 1_000_000


def _included(status: StageStatus, scope: CostScope) -> bool:
    return status == StageStatus.PASSED if scope == "passed_only" else status in EXECUTED


def estimate_stage_models_with_cost(
    view: TrainingView, registry: ModelRegistry, scope: CostScope = "all_non_void_executed"
):
    """Return copied frozen estimates with only ``cost_usd`` replaced, plus coverage rows."""
    if scope not in ("all_non_void_executed", "passed_only"):
        raise ValueError(f"unknown cost scope {scope!r}")
    estimates = copy.deepcopy(estimate_stage_models(view))
    groups = defaultdict(list)
    for envelope in view.stage_records:
        groups[(envelope.stage.value, envelope.model_alias, norm_project(envelope.project_id))].append(envelope)

    cells = []
    for (stage, alias), est in sorted(estimates.items()):
        project_costs: dict[str, float | None] = {}
        for project in view.training_projects:
            records = [e.record for e in groups.get((stage, alias, project), [])
                       if _included(e.record.status, scope) and not e.record.cache_hit]
            costs = [record_cost_usd(record, alias, registry) for record in records]
            complete = bool(records) and all(cost is not None for cost in costs)
            value = mean(costs) if complete else None
            project_costs[project] = value
            if project not in est.per_project:
                est.per_project[project] = {}
            est.per_project[project]["cost_usd"] = value
            cells.append({
                "held_out_project": view.held_out_project,
                "training_project": project,
                "stage": stage,
                "model_alias": alias,
                "scope": scope,
                "n_eligible_records": len(records),
                "n_complete_usage_records": sum(cost is not None for cost in costs),
                "cost_usd": value,
                "estimable": value is not None,
            })
        values = list(project_costs.values())
        est.values["cost_usd"] = (
            (mean(values), min(values), max(values))
            if values and all(value is not None for value in values)
            else None
        )
        est.notes = [note for note in est.notes if not note.startswith("cost_usd unavailable")]
        est.notes.append(
            f"post-hoc cost scope={scope}; separate input/output repricing; "
            f"estimable_projects={sum(v is not None for v in values)}/{len(values)}"
        )
    return estimates, cells


def _common(view: TrainingView, cfg: RoutingConfig, created_at: str) -> dict:
    return dict(
        target_project=view.held_out_project,
        held_out_project=view.held_out_project,
        training_projects=list(view.training_projects),
        objective=cfg.objective,
        settings=cfg.settings,
        router_version=cfg.router_version,
        config_hash=cfg.config_hash,
        created_at=created_at,
    )


def decide_cost_aware(
    view: TrainingView,
    cfg: RoutingConfig,
    registry: ModelRegistry,
    created_at: str,
    scope: CostScope = "all_non_void_executed",
):
    """Build cost-aware S1--S3 traces while leaving all frozen non-cost estimates intact."""
    estimates, cells = estimate_stage_models_with_cost(view, registry, scope)
    cost_predictor = "stage_additive_all_nonvoid" if scope == "all_non_void_executed" else "stage_additive_passed_only"
    scope_label = "passed_only_cost_sensitivity" if scope == "passed_only" else scope
    common_meta = {"cost_predictor": cost_predictor, "cost_scope": scope_label,
                   "evidence_level": "post-hoc / exploratory"}

    s1 = []
    for alias in view.model_aliases():
        path_id = make_path_id([alias] * len(STAGES))
        candidates = predict_additive(view, estimates, [path_id])
        s1.append(build_trace(
            strategy=Strategy.S1_SINGLE_MODEL,
            candidates=candidates,
            extra_components={
                "policy_path_id": path_id,
                "predictor": "stage_additive",
                "note": "fixed single-model baseline; no oracle knowledge",
                **common_meta,
            },
            **_common(view, cfg, created_at),
        ))

    additive_candidates = predict_additive(view, estimates)
    s2 = build_trace(
        strategy=Strategy.S2_GREEDY_TASK_ONLY,
        candidates=additive_candidates,
        extra_components={
            "predictor": "stage_additive",
            "note": "task-only: Experiment A estimates only; cross-stage interactions ignored",
            **common_meta,
        },
        **_common(view, cfg, created_at),
    )

    workflow_candidates, details = predict_workflow_aware(view, cfg.interaction_shrinkage_k, estimates)
    additive_by_path = {candidate.path_id: candidate for candidate in additive_candidates}
    corrected = []
    for candidate in workflow_candidates:
        additive = additive_by_path[candidate.path_id]
        interaction = {key: value for key, value in candidate.interaction_terms.items() if key != "cost_usd"}
        uncertainty = dict(candidate.uncertainty)
        if "cost_usd" in additive.uncertainty:
            uncertainty["cost_usd"] = additive.uncertainty["cost_usd"]
        else:
            uncertainty.pop("cost_usd", None)
        corrected.append(candidate.model_copy(update={
            "cost_usd": additive.cost_usd,
            "interaction_terms": interaction,
            "uncertainty": uncertainty,
        }))
    shrink = {path: detail.shrink for path, detail in details.items() if detail.shrink}
    s3 = build_trace(
        strategy=Strategy.S3_WORKFLOW_AWARE,
        candidates=corrected,
        extra_components={
            "predictor": "stage_additive_plus_interaction_terms",
            "interaction_shrinkage_k": cfg.interaction_shrinkage_k,
            "interaction_shrinkage": shrink,
            "note": "non-cost interaction terms are observed minus additive and shrunk; cost remains additive",
            **common_meta,
        },
        **_common(view, cfg, created_at),
    )
    return {"S1": s1, "S2": [s2], "S3": [s3]}, cells

