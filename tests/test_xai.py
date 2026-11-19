"""Explanation faithfulness and counterfactual validation tests (offline, SYNTHETIC_FIXTURE data only)."""

from __future__ import annotations

import copy
import json

import pytest

from experiments.evaluate_routing import PRED_LOG, run_predict
from experiments.validate_counterfactuals import run_validate
from src.contracts import CounterfactualValidation, QualityConstraint, Strategy
from src.explainability.explanations import Explanation, render_explanation, render_text
from src.explainability.validation import (
    check_faithfulness,
    replay_trace,
    validate_log,
    validate_prediction,
)
from src.routing.config import load_routing_config
from src.routing.counterfactual import PredictionLog, generate_counterfactuals
from src.routing.data import build_training_view, load_records
from src.routing.outcomes import aggregate_runs
from src.routing.strategies import decide_prospective, decide_s2, decide_s3, oracle_s4
from tests.fixtures.xai.SYNTHETIC_FIXTURE_generator import JSONL_PATH

HO = "synthetic_fixture_p3"
TS = "SYNTHETIC_FIXTURE_TIME"


@pytest.fixture(scope="module")
def store():
    return load_records(JSONL_PATH)


@pytest.fixture(scope="module")
def cfg():
    return load_routing_config()


@pytest.fixture(scope="module")
def view(store):
    return build_training_view(store, HO)


@pytest.fixture(scope="module")
def s3(view, cfg):
    return decide_s3(view, cfg, TS)


def _all_ok(fc):
    return fc.claims_consistent == fc.claims_checked and not fc.inconsistencies and fc.replay_matches_selection


# ----------------------------------------------------------------------------- faithfulness
def test_explanations_faithful_for_all_strategies(store, view, cfg):
    traces = [t for ts in decide_prospective(view, cfg, TS).values() for t in ts] + [oracle_s4(store, HO, cfg, TS)]
    for t in traces:
        e = render_explanation(t)
        fc = check_faithfulness(t, e, TS)
        assert _all_ok(fc), (t.strategy, fc.inconsistencies)
        assert fc.trace_hash == t.trace_hash() and fc.explanation_hash == e.explanation_hash
        assert fc.claims_checked == len(e.claims) >= 10


def test_explanation_content(s3):
    e = render_explanation(s3)
    assert f"Selected path {s3.selected_path_id}." in e.text
    assert "INACTIVE: cost_usd unavailable" in e.text
    assert "Interaction term" in e.text and "not a causal handoff cost" in e.text
    assert "What would change" in e.text
    assert e.text == "\n".join(c["text"] for c in e.claims)
    assert render_explanation(s3).text == e.text          # deterministic


def test_oracle_explanation_labelled(store, cfg):
    e = render_explanation(oracle_s4(store, HO, cfg, TS))
    assert "retrospective oracle" in e.text and "not a deployable router" in e.text


def test_no_feasible_path_explanation(view, cfg):
    strict = cfg.objective.model_copy(update={"quality_constraints": [QualityConstraint(
        stage="analysis", metric="numerical_accuracy", op=">=", threshold=1.01)]})
    c = type(cfg)(**{**cfg.__dict__, "objective": strict})
    t = decide_s2(view, c, TS)
    assert t.no_feasible_path
    e = render_explanation(t)
    assert "No feasible path" in e.text
    assert _all_ok(check_faithfulness(t, e, TS))
    assert generate_counterfactuals(t, TS)[0] == []


def _corrupt(e: Explanation, idx: int, *, text=None, params=None, kind=None) -> Explanation:
    claims = copy.deepcopy(e.claims)
    c = claims[idx]
    if params:
        c["params"].update(params)
        c["text"] = render_text(c["kind"], c["params"])     # consistent text, wrong value
    if text:
        c["text"] = text
    if kind:
        c["kind"] = kind
    return Explanation(e.trace_id, e.trace_hash, claims, "\n".join(x["text"] for x in claims))


def _idx(e, kind):
    return next(i for i, c in enumerate(e.claims) if c["kind"] == kind)


def test_corrupted_explanations_detected(s3):
    e = render_explanation(s3)
    other = next(c.path_id for c in s3.candidates if c.path_id != s3.selected_path_id)
    cases = [
        _corrupt(e, _idx(e, "selected"), params={"path": other}),                 # wrong selection (re-rendered)
        _corrupt(e, _idx(e, "selected"), text=f"Selected path {other}."),         # text edited only
        _corrupt(e, _idx(e, "decisive"), params={"order": 0}),                    # wrong decisive step
        _corrupt(e, _idx(e, "transition"), params={"kind": "stay"}
                 if e.claims[_idx(e, "transition")]["params"]["kind"] == "switch" else {"kind": "switch"}),
        _corrupt(e, _idx(e, "uncertainty"), params={"value": 0.123}),             # wrong number
        _corrupt(e, _idx(e, "interaction"), params={"quantity": "end_to_end_ms_x"}),
    ]
    wi = next(i for i, c in enumerate(e.claims) if c["kind"] == "wwc_flip")
    cases.append(_corrupt(e, wi, params={"flip": e.claims[wi]["params"]["flip"] + 0.2}))  # wrong counterfactual
    for bad in cases:
        fc = check_faithfulness(s3, bad, "t")
        assert fc.claims_consistent < fc.claims_checked and fc.inconsistencies, bad.text[:80]
        assert fc.replay_matches_selection            # replay of the (untouched) trace is still fine
    # An invented sentence not backed by a claim.
    added = Explanation(e.trace_id, e.trace_hash, e.claims, e.text + "\nModel A is the best model overall.")
    fc = check_faithfulness(s3, added, "t")
    assert any("not backed" in x for x in fc.inconsistencies)


def test_replay_matches_and_detects_tampered_trace(s3):
    rp = replay_trace(s3)
    assert rp.matches_selection and rp.matches_steps and rp.matches_sets
    other = next(p for p in s3.feasible_path_ids if p != s3.selected_path_id)
    forged = s3.model_copy(update={"selected_path_id": other})      # bypasses validation on purpose
    assert not replay_trace(forged).matches_selection
    fc = check_faithfulness(forged, render_explanation(forged), "t")
    assert fc.replay_matches_selection is False


# ----------------------------------------------------------------------------- empirical validity
def test_validate_prediction_against_outcomes(store, s3):
    preds, _ = generate_counterfactuals(s3, TS)
    runs = store.retrospective_outcomes(HO)
    for p in preds:
        v = validate_prediction(p, runs, TS)
        v.check_against(p)
        so, ao = aggregate_runs(p.selected_path_id, runs), aggregate_runs(p.alternative_path_id, runs)
        assert v.actual_outcome == {"selected": so.outcome_label, "alternative": ao.outcome_label}
        f_delta = ao.values["feasible"] - so.values["feasible"]
        assert v.actual_delta["feasible"] == pytest.approx(f_delta)
        assert v.abs_error["feasible"] == pytest.approx(abs(p.predicted_delta["feasible"] - f_delta))
        assert v.abs_error["cost_usd"] is None and v.direction_correct["cost_usd"] is None
        assert "feasibility_agreement:selected" in v.direction_correct
        assert v.n_repeats["selected"] == 2


def test_validation_refuses_modified_prediction(store, s3):
    p = generate_counterfactuals(s3, TS)[0][0]
    modified = p.model_copy(update={"predicted_delta": {**p.predicted_delta, "feasible": 0.99}})
    with pytest.raises(ValueError, match="modified"):
        validate_prediction(modified, store.retrospective_outcomes(HO), TS)
    v = validate_prediction(p, store.retrospective_outcomes(HO), TS)
    with pytest.raises(ValueError, match="hash mismatch"):
        v.check_against(modified)
    assert isinstance(v, CounterfactualValidation)


def test_validate_log_refuses_broken_chain(store, s3, tmp_path):
    log = PredictionLog(tmp_path / "SYNTHETIC_FIXTURE_preds.jsonl")
    for p in generate_counterfactuals(s3, TS)[0]:
        log.append_prediction(p)
    ok = validate_log(log.path, store, TS)
    assert len(ok.validations) == len(ok.predictions) == 8
    lines = log.path.read_text().splitlines()
    log.path.write_text("\n".join(lines[1:]) + "\n")
    with pytest.raises(ValueError, match="hash chain is broken"):
        validate_log(log.path, store, TS)


# ----------------------------------------------------------------------------- LOPO driver
def test_lopo_driver_end_to_end(store, cfg, tmp_path):
    out = tmp_path / "SYNTHETIC_FIXTURE_run"
    m = run_predict(store, cfg, out, created_at=TS)
    assert m["synthetic_fixture"] and m["prediction_log"]["chain_ok"]
    assert [f["held_out_project"] for f in m["folds"]] == store.projects()
    for f in m["folds"]:
        assert f["held_out_project"] not in f["training_projects"]
        assert {d["strategy"] for d in f["decisions"]} == {"S1_single_model", "S2_greedy_task_only",
                                                           "S3_workflow_aware"}
    # Predictions are logged before validation; no S4 prediction ever.
    preds = PredictionLog(out / PRED_LOG).predictions()
    assert preds and all(p.strategy != Strategy.S4_ORACLE for p in preds)
    assert not (out / "counterfactual_validations.jsonl").exists()
    for ln in (out / "computational_faithfulness.jsonl").read_text().splitlines():
        fc = json.loads(ln)
        assert fc["claims_consistent"] == fc["claims_checked"] and fc["replay_matches_selection"]
    r = run_validate(store, cfg, out, validated_at=TS)
    assert r["n_validations"] == len(preds)
    emp = json.loads((out / "empirical_validity.json").read_text())
    orc = json.loads((out / "oracle_comparison.json").read_text())
    assert emp["section"].startswith("EMPIRICAL VALIDITY") and "NOT a deployable" in orc["section"]
    assert "claims_consistent" not in json.dumps(emp)       # faithfulness and validity kept separate
    with pytest.raises(FileExistsError):
        run_validate(store, cfg, out, validated_at=TS)
