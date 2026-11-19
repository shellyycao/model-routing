"""Routing tests (offline). All data is SYNTHETIC_FIXTURE (tests/fixtures/xai/); no number here is a result."""

from __future__ import annotations

import json
from math import prod

import pytest

from src.contracts import (
    CounterfactualPrediction,
    DecisionTrace,
    EvidenceRef,
    PathPrediction,
    QualityConstraint,
    RoutingObjective,
    StageStatus,
    Strategy,
)
from src.routing.config import RouterSettings, load_routing_config
from src.routing.counterfactual import PredictionLog, alternatives_for, generate_counterfactuals, verify_chain
from src.routing.data import (
    RecordStore,
    TrainingView,
    build_training_view,
    ensure_output_allowed,
    load_records,
)
from src.routing.estimation import (
    estimate_interactions,
    estimate_stage_models,
    predict_additive,
    predict_workflow_aware,
)
from src.routing.router import route, what_would_change, _with_threshold
from src.routing.scoring import pareto_front
from src.routing.strategies import decide_prospective, decide_s2, decide_s3, oracle_s4
from tests.fixtures.xai.SYNTHETIC_FIXTURE_generator import JSONL_PATH, build_records

HO = "synthetic_fixture_p3"
TS = "SYNTHETIC_FIXTURE_TIME"


@pytest.fixture(scope="module")
def store() -> RecordStore:
    return load_records(JSONL_PATH)


@pytest.fixture(scope="module")
def cfg():
    return load_routing_config()


@pytest.fixture(scope="module")
def view(store) -> TrainingView:
    return build_training_view(store, HO)


def pp(pid, feas=0.9, q=None, e2e=1000.0, cost=None, tok=100.0, ev=None):
    return PathPrediction(path_id=pid, feasibility_prob=feas, quality=q or {}, end_to_end_ms=e2e, cost_usd=cost,
                          total_tokens=tok, n_switches=0 if len(set(pid.split("-"))) == 1 else
                          sum(a != b for a, b in zip(pid.split("-"), pid.split("-")[1:])), evidence=ev or [])


def obj(**kw) -> RoutingObjective:
    base = dict(objective_id="SYNTHETIC_FIXTURE_obj", min_feasibility_prob=0.5, quality_constraints=[],
                preference_order=["cost_usd", "end_to_end_ms"], tie_tolerance=0.05)
    base.update(kw)
    return RoutingObjective(**base)


# ----------------------------------------------------------------------------- data / leakage
def test_fixture_file_matches_generator_and_is_labelled():
    lines = JSONL_PATH.read_text().splitlines()
    assert "SYNTHETIC_FIXTURE" in JSONL_PATH.name
    assert all("SYNTHETIC_FIXTURE" in json.loads(ln)["run_id"] for ln in lines)
    assert [json.loads(ln) for ln in lines] == [json.loads(r.model_dump_json()) for r in build_records()]


def test_loader_accepts_dir_and_records(tmp_path, store):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.jsonl").write_text(JSONL_PATH.read_text())
    s2 = load_records(tmp_path)
    s3 = load_records(build_records())
    assert len(s2.workflow_runs) == len(s3.workflow_runs) == len(store.workflow_runs)
    assert len(s2.stage_records) == len(store.stage_records)
    with pytest.raises(ValueError, match="duplicate"):
        load_records([*build_records()[:2], build_records()[0]])
    bad = json.loads(JSONL_PATH.read_text().splitlines()[0])
    bad["contract_version"] = "0.9"
    with pytest.raises(ValueError, match="contract_version"):
        load_records([bad])
    with pytest.raises(ValueError):
        load_records([{"foo": 1}])


def test_training_view_physically_excludes_held_out(store, view):
    assert HO in store.projects()
    assert HO not in view.training_projects
    assert all(r.project_id != HO for r in view.stage_records)
    assert all(r.project_id != HO for r in view.workflow_runs)
    assert all(e.project_id != HO for e in view.evidence_refs())
    # No back-reference to the full store.
    assert not any(isinstance(v, RecordStore) for v in vars(view).values())
    n_ho = sum(r.project_id == HO for r in store.stage_records) + len(store.retrospective_outcomes(HO))
    assert len(view.stage_records) + len(view.workflow_runs) == \
        len(store.stage_records) + len(store.workflow_runs) - n_ho
    # Every estimator output references only training evidence.
    est = estimate_stage_models(view)
    assert all(e.project_id != HO for se in est.values() for e in se.evidence)
    preds, _ = predict_workflow_aware(view, 2.0, est)
    assert all(e.project_id != HO for p in preds for e in p.evidence)
    # A TrainingView cannot be constructed with a held-out record inside it.
    with pytest.raises(ValueError, match="Leakage"):
        TrainingView(held_out_project=HO, training_projects=view.training_projects,
                     stage_records=view.stage_records + tuple(r for r in store.stage_records
                                                              if r.project_id == HO)[:1],
                     workflow_runs=())


def test_estimators_reject_full_store(store):
    with pytest.raises(TypeError):
        estimate_stage_models(store)
    with pytest.raises(ValueError):
        build_training_view(store, "unknown_project")


def test_trace_rejects_held_out_evidence(view, cfg):
    t = decide_s3(view, cfg, TS)
    d = t.model_dump(mode="json")
    d["candidates"][0]["evidence"].append({"project_id": HO, "run_id": "SYNTHETIC_FIXTURE-leak",
                                           "experiment_id": "SYNTHETIC_FIXTURE_expB_paths"})
    d["training_data_hash"] = DecisionTrace.compute_training_data_hash(
        [PathPrediction.model_validate(c) for c in d["candidates"]])
    with pytest.raises(ValueError, match="Leakage"):
        DecisionTrace.model_validate(d)


def test_synthetic_outputs_never_under_results(store, tmp_path):
    from src.routing.config import REPO_ROOT
    with pytest.raises(ValueError, match="SYNTHETIC_FIXTURE"):
        ensure_output_allowed(REPO_ROOT / "results" / "routing", store)
    ensure_output_allowed(tmp_path, store)


# ----------------------------------------------------------------------------- estimation
def test_stage_estimates_exclude_void_and_upstream_attributed(view):
    est = estimate_stage_models(view)
    e = est[("analysis", "C")]
    assert e.n_void == 1                                      # the INFRA_ERROR fixture record
    for proj, cell in e.per_project.items():
        recs = [r for r in view.stage_records if r.project_id == proj and r.stage.value == "analysis"
                and r.model_alias == "C" and r.record.status != StageStatus.INFRA_ERROR]
        assert cell["feasible"] == sum(r.record.status == StageStatus.PASSED for r in recs) / len(recs)
    v, lo, hi = e.values["feasible"]
    assert lo <= v <= hi and lo == min(c["feasible"] for c in e.per_project.values())
    assert e.values["cost_usd"] is None                       # prices unverified -> never 0


def test_s2_is_stage_additive(view):
    est = estimate_stage_models(view)
    preds = {p.path_id: p for p in predict_additive(view, est)}
    assert len(preds) == 27
    p = preds["B-C-A"]
    parts = [est[("cleaning", "B")], est[("analysis", "C")], est[("reporting", "A")]]
    assert p.feasibility_prob == pytest.approx(prod(x.values["feasible"][0] for x in parts))
    assert p.end_to_end_ms == pytest.approx(sum(x.values["stage_time_ms"][0] for x in parts))
    assert p.total_tokens == pytest.approx(sum(x.values["tokens"][0] for x in parts))
    assert p.quality["analysis.numerical_accuracy"] == est[("analysis", "C")].values["analysis.numerical_accuracy"][0]
    assert p.cost_usd is None and p.interaction_terms == {}
    assert p.uncertainty["feasible"][0] == pytest.approx(prod(x.values["feasible"][1] for x in parts))


def test_s3_interaction_terms_and_shrinkage(view):
    est = estimate_stage_models(view)
    k = 2.0
    s2 = {p.path_id: p for p in predict_additive(view, est)}
    s3, details = predict_workflow_aware(view, k, est)
    s3 = {p.path_id: p for p in s3}
    ie = estimate_interactions(view, est, "B-C-B", k)
    q = "analysis.numerical_accuracy"
    n = len(ie.residuals[q])
    assert 1 <= n <= 2 and ie.shrink[q] == pytest.approx(n / (n + k))
    term = ie.shrink[q] * sum(ie.residuals[q].values()) / n
    assert s3["B-C-B"].interaction_terms[q] == pytest.approx(term)
    assert s3["B-C-B"].quality[q] == pytest.approx(s2["B-C-B"].quality[q] + term)
    assert term < 0                       # the fixture's invented B->C interaction is visible
    assert 0.0 <= s3["B-C-B"].feasibility_prob <= 1.0
    assert all(e.experiment_id.endswith("expB_paths") for e in ie.run_evidence)
    assert "handoff" not in json.dumps(s3["B-C-B"].interaction_terms)


def test_strategies_on_fixture(view, cfg):
    d = decide_prospective(view, cfg, TS)
    s1 = d["S1"]
    assert [t.explanation_components["policy_path_id"] for t in s1] == ["A-A-A", "B-B-B", "C-C-C"]
    assert all(len(t.candidates) == 1 and t.strategy == Strategy.S1_SINGLE_MODEL for t in s1)
    s2, s3 = d["S2"][0], d["S3"][0]
    assert s2.strategy == Strategy.S2_GREEDY_TASK_ONLY and s3.strategy == Strategy.S3_WORKFLOW_AWARE
    assert all(not c.interaction_terms for c in s2.candidates)
    assert any(c.interaction_terms for c in s3.candidates)
    # Fixture is built so that the task-only router ignores the invented B->C interaction.
    assert s2.selected_path_id == "B-C-B"
    assert s3.selected_path_id != "B-C-B"
    for t in (*s1, s2, s3):
        assert t.held_out_project == HO and HO not in t.training_projects


# ----------------------------------------------------------------------------- router
def test_inactive_cost_criterion_never_zero():
    cands = [pp("A-A-A", e2e=3000), pp("B-B-B", e2e=1000), pp("C-C-C", e2e=2000, cost=0.0)]
    r = route(cands, obj())
    step = next(s for s in r.steps if s.rule == "lexicographic_preference" and "cost_usd" in s.detail)
    assert step.inactive and "not treated as 0" in step.inactive_reason
    assert r.inactive_criteria == ["cost_usd"]
    assert r.selected_path_id == "B-B-B"           # C-C-C's cost 0.0 does not win against unknown costs
    r2 = route([pp("A-A-A", cost=2.0, e2e=1), pp("B-B-B", cost=1.0, e2e=5)], obj())
    assert r2.inactive_criteria == [] and r2.selected_path_id == "B-B-B"


def test_no_feasible_path():
    cands = [pp("A-A-A", feas=0.3), pp("B-B-B", feas=0.9, q={"analysis.numerical_accuracy": 0.5}),
             pp("C-C-C", feas=None)]
    o = obj(quality_constraints=[QualityConstraint(stage="analysis", metric="numerical_accuracy", op=">=",
                                                   threshold=0.9)])
    r = route(cands, o)
    assert r.selected_path_id is None and r.feasible_path_ids == [] and r.pareto_path_ids == []
    assert [s.rule for s in r.steps] == ["feasibility_threshold", "quality_constraint", "no_feasible_path"]
    assert "no feasibility prediction" in r.steps[0].removed["C-C-C"]
    t = DecisionTrace(trace_id="SYNTHETIC_FIXTURE", created_at=TS, strategy=Strategy.S2_GREEDY_TASK_ONLY,
                      target_project="x", held_out_project="x", training_projects=["y"],
                      training_data_hash=DecisionTrace.compute_training_data_hash(r.candidates), objective=o,
                      candidates=r.candidates, selection_steps=r.steps, feasible_path_ids=[], pareto_path_ids=[],
                      selected_path_id=None, no_feasible_path=True, router_version="t", config_hash="t")
    assert t.no_feasible_path


def test_pareto_hand_checked():
    # dims: feasibility (max), q (max), e2e (min)
    a = pp("A-A-A", feas=0.9, q={"analysis.numerical_accuracy": 0.9}, e2e=100)
    b = pp("B-B-B", feas=0.9, q={"analysis.numerical_accuracy": 0.8}, e2e=100)   # dominated by A
    c = pp("C-C-C", feas=0.8, q={"analysis.numerical_accuracy": 0.95}, e2e=50)   # trade-off
    d = pp("A-B-C", feas=0.7, q={"analysis.numerical_accuracy": 0.7}, e2e=60)    # dominated by C
    dims = [("feasibility_prob", "max"), ("analysis.numerical_accuracy", "max"), ("end_to_end_ms", "min")]
    front, removed = pareto_front([a, b, c, d], dims)
    assert sorted(front) == ["A-A-A", "C-C-C"]
    assert removed == {"B-B-B": "dominated by A-A-A", "A-B-C": "dominated by C-C-C"}
    # Through the router: the unsupported_claim_count direction is "min".
    x = pp("A-A-A", q={"reporting.unsupported_claim_count": 0.0})
    y = pp("B-B-B", q={"reporting.unsupported_claim_count": 2.0})
    r = route([x, y], obj(preference_order=["end_to_end_ms"]))
    assert r.pareto_path_ids == ["A-A-A"]


def test_selection_steps_recorded_in_order_and_tie_tolerance():
    o = obj(quality_constraints=[QualityConstraint(stage="analysis", metric="numerical_accuracy", op=">=",
                                                   threshold=0.5)],
            preference_order=["cost_usd", "end_to_end_ms", "total_tokens"])
    q = {"analysis.numerical_accuracy": 0.9}
    cands = [pp("A-A-A", q=q, e2e=1000, tok=300), pp("B-B-B", q=q, e2e=1030, tok=100),
             pp("C-C-C", q=q, e2e=2000, tok=50)]
    r = route(cands, o, RouterSettings(pareto_quality_keys=[]))
    assert [s.rule for s in r.steps] == ["feasibility_threshold", "quality_constraint", "pareto_filter",
                                         "lexicographic_preference", "lexicographic_preference",
                                         "lexicographic_preference", "tie_break"]
    assert [s.order for s in r.steps] == list(range(len(r.steps)))
    # 1030 is within 5% of 1000 -> tie on e2e; tokens decide.
    e2e_step = r.steps[4]
    assert set(e2e_step.remaining) == {"A-A-A", "B-B-B"} and "C-C-C" in e2e_step.removed
    assert r.selected_path_id == "B-B-B"


def test_what_would_change_is_verified_by_rerun(view, cfg):
    t = decide_s3(view, cfg, TS)
    wwc = t.explanation_components["what_would_change"]
    assert any(w["flips"] for w in wwc)
    for w in wwc:
        if not w["flips"]:
            continue
        new = route(t.candidates, _with_threshold(t.objective, w["parameter"], w["flip_threshold"]),
                    cfg.settings).selected_path_id
        assert new == w["new_selected"] != t.selected_path_id
    assert wwc == what_would_change(t.candidates, t.objective, cfg.settings, t.selected_path_id)


# ----------------------------------------------------------------------------- counterfactuals
def test_alternatives_cover_swaps_and_baselines():
    alts = alternatives_for("B-C-B", ["A", "B", "C"])
    assert {"A-C-B", "C-C-B", "B-A-B", "B-B-B", "B-C-A", "B-C-C", "A-A-A", "C-C-C"} == set(alts)
    assert "B-C-B" not in alts


@pytest.fixture()
def logged(view, cfg, tmp_path):
    t = decide_s3(view, cfg, TS)
    preds, _ = generate_counterfactuals(t, TS)
    log = PredictionLog(tmp_path / "SYNTHETIC_FIXTURE_preds.jsonl")
    for p in preds:
        log.append_prediction(p)
    return t, preds, log


def test_counterfactual_predictions_content(logged):
    t, preds, log = logged
    assert len(preds) == 8 and log.verify().ok and log.verify().n_lines == 8
    by_id = {c.path_id: c for c in t.candidates}
    p = preds[0]
    sel, alt = by_id[p.selected_path_id], by_id[p.alternative_path_id]
    assert p.predicted_delta["end_to_end_ms"] == pytest.approx(alt.end_to_end_ms - sel.end_to_end_ms)
    lo, hi = p.predicted_delta_interval["feasible"]
    assert lo == pytest.approx(alt.uncertainty["feasible"][0] - sel.uncertainty["feasible"][1])
    assert p.predicted_delta["cost_usd"] is None
    assert [x.prediction_id for x in log.predictions()] == [x.prediction_id for x in preds]


def _lines(log):
    return log.path.read_text().splitlines()


def test_log_detects_edit(logged):
    _, _, log = logged
    lines = _lines(log)
    d = json.loads(lines[2])
    d["record"]["predicted_delta"]["end_to_end_ms"] = -1.0
    lines[2] = json.dumps(d)
    log.path.write_text("\n".join(lines) + "\n")
    rep = verify_chain(log.path, log.content_hash)
    assert not rep.ok and any("line 2" in e for e in rep.errors)
    with pytest.raises(ValueError, match="refusing to append"):
        log.append({"x": 1})


def test_log_detects_edit_with_recomputed_hash(logged):
    """Even if the editor recomputes the record hash with .create(), the chain breaks."""
    _, preds, log = logged
    lines = _lines(log)
    d = json.loads(lines[1])
    fields = {k: v for k, v in d["record"].items() if k not in ("content_hash", "contract_version")}
    fields["predicted_delta"] = {**fields["predicted_delta"], "end_to_end_ms": 0.0}
    forged = CounterfactualPrediction.create(**fields)
    d["record"] = forged.model_dump(mode="json")
    d["content_hash"] = forged.content_hash
    lines[1] = json.dumps(d)
    log.path.write_text("\n".join(lines) + "\n")
    assert not verify_chain(log.path, log.content_hash).ok


def test_log_detects_deletion_and_reorder(logged):
    _, _, log = logged
    orig = _lines(log)
    log.path.write_text("\n".join(orig[:3] + orig[4:]) + "\n")            # middle deletion
    assert not verify_chain(log.path, log.content_hash).ok
    log.path.write_text("\n".join(orig[:-1]) + "\n")                       # tail truncation (head anchor)
    assert not verify_chain(log.path, log.content_hash).ok
    log.path.write_text("\n".join([orig[1], orig[0]] + orig[2:]) + "\n")   # reorder
    assert not verify_chain(log.path, log.content_hash).ok
    log.path.write_text("\n".join(orig) + "\n")
    assert verify_chain(log.path, log.content_hash).ok


def test_s4_never_prospective(store, view, cfg, tmp_path):
    o = oracle_s4(store, HO, cfg, TS)
    assert o.strategy == Strategy.S4_ORACLE and o.explanation_components["deployable"] is False
    assert all(e.project_id == HO for c in o.candidates for e in c.evidence)
    with pytest.raises(ValueError, match="prospective"):
        generate_counterfactuals(o, TS)
    t = decide_s2(view, cfg, TS)
    preds, _ = generate_counterfactuals(t, TS)
    fields = {k: v for k, v in preds[0].model_dump().items() if k not in ("content_hash", "contract_version")}
    fields["strategy"] = Strategy.S4_ORACLE
    with pytest.raises(ValueError):
        CounterfactualPrediction.create(**fields)
    # Prospective traces never contain S4 and never reference held-out evidence.
    for traces in decide_prospective(view, cfg, TS).values():
        for t in traces:
            assert t.strategy != Strategy.S4_ORACLE
            assert all(e.project_id != HO for c in t.candidates for e in c.evidence)
