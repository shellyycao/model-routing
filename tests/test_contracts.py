import json

import pytest
from pydantic import ValidationError

from src.contracts import (
    CounterfactualPrediction,
    CounterfactualValidation,
    DecisionTrace,
    EvidenceRef,
    FailureType,
    Feasibility,
    PathPrediction,
    RoutingObjective,
    SelectionStep,
    StageBenchmarkRecord,
    StageId,
    StageRunRecord,
    StageStatus,
    Strategy,
    ValidationResult,
    WorkflowEfficiency,
    WorkflowRunRecord,
    enumerate_paths,
    n_switches,
    parse_path_id,
)

STAGE_ORDER = [StageId.CLEANING, StageId.ANALYSIS, StageId.REPORTING]


# ----------------------------------------------------------------------------- ids
def test_enumerate_27_paths():
    paths = enumerate_paths(["A", "B", "C"])
    assert len(paths) == 27 and len(set(paths)) == 27
    assert {"A-A-A", "B-B-B", "C-C-C", "A-B-C"} <= set(paths)
    assert len(enumerate_paths(["A", "B", "C"], n_stages=2)) == 9


def test_switch_count_and_path_validation():
    assert n_switches("A-A-A") == 0 and n_switches("A-B-A") == 2 and n_switches("A-A-B") == 1
    for bad in ["", "A--B", "a-b", "A-B-C-A", "AB-C"]:
        with pytest.raises(ValueError):
            parse_path_id(bad)


# ----------------------------------------------------------------------------- workflow records
def _stage(i, model, status, ft=None):
    return StageRunRecord(stage=STAGE_ORDER[i], model_alias=model, model_id="x", prompt_version="v1",
                          invocation_ids=[], status=status, failure_type=ft)


def _run(path, statuses, outcome, first=None, ft=None, **kw):
    models = path.split("-")
    stages = [_stage(i, m, s, FailureType.VALIDATION_FAILED if s == StageStatus.FAILED else
                     (FailureType.INFRA if s == StageStatus.INFRA_ERROR else None))
              for i, (m, s) in enumerate(zip(models, statuses))]
    stage_status = {s.stage.value: s.status for s in stages}
    return WorkflowRunRecord(
        run_id="r", experiment_id="e", project_id="p", path_id=path, models=models,
        config_hash="h", started_at="t", stages=stages,
        feasibility=Feasibility(outcome=outcome, stage_status=stage_status, first_failure_stage=first, failure_type=ft),
        efficiency=WorkflowEfficiency(), **kw)


P, F, N, I = StageStatus.PASSED, StageStatus.FAILED, StageStatus.NOT_RUN_UPSTREAM_FAILURE, StageStatus.INFRA_ERROR


def test_feasible_run():
    assert _run("A-B-C", [P, P, P], "feasible").feasibility.feasible


def test_intermediate_failure_blocks_feasibility_and_stays_visible():
    with pytest.raises(ValidationError):
        _run("A-B-C", [P, F, N], "feasible")
    r = _run("A-B-C", [P, F, N], "infeasible", first=StageId.ANALYSIS)
    assert r.stages[1].status == F and not r.feasibility.feasible


def test_missing_stage_record_cannot_pass_gate():  # review B3
    models = ["A", "B", "C"]
    stages = [_stage(0, "A", P), _stage(1, "B", P)]
    with pytest.raises(ValidationError, match="needs 3 stage records"):
        WorkflowRunRecord(run_id="r", experiment_id="e", project_id="p", path_id="A-B-C", models=models,
                          config_hash="h", started_at="t", stages=stages,
                          feasibility=Feasibility(outcome="feasible", stage_status={s.stage.value: s.status for s in stages}),
                          efficiency=WorkflowEfficiency())


def test_stage_order_and_model_must_match_path():
    with pytest.raises(ValidationError, match="ran model C, path says B"):
        WorkflowRunRecord(
            run_id="r", experiment_id="e", project_id="p", path_id="A-B-C", models=["A", "B", "C"],
            config_hash="h", started_at="t",
            stages=[_stage(0, "A", P), _stage(1, "C", P), _stage(2, "C", P)],
            feasibility=Feasibility(outcome="feasible", stage_status={"cleaning": P, "analysis": P, "reporting": P}),
            efficiency=WorkflowEfficiency())


def test_terminate_policy_forbids_running_after_failure():
    with pytest.raises(ValidationError, match="NOT_RUN_UPSTREAM_FAILURE"):
        _run("A-B-C", [F, P, P], "infeasible", first=StageId.CLEANING)


def test_infra_error_voids_run_instead_of_infeasible():  # review M11
    r = _run("A-B", [I, N], "void_infra", first=StageId.CLEANING)
    assert r.feasibility.outcome == "void_infra"
    with pytest.raises(ValidationError):
        _run("A-B", [I, N], "infeasible", first=StageId.CLEANING)


def test_failed_stage_requires_failure_type():
    with pytest.raises(ValidationError):
        StageRunRecord(stage=StageId.CLEANING, model_alias="A", model_id="x", prompt_version="v1",
                       invocation_ids=[], status=F)


def test_quality_basis_slots():  # review M9
    gt = ValidationResult(stage=StageId.ANALYSIS, hard_pass=True, checks=[])
    cond = ValidationResult(stage=StageId.ANALYSIS, hard_pass=True, checks=[], quality_basis="conditional_reference")
    StageRunRecord(stage=StageId.ANALYSIS, model_alias="A", model_id="x", prompt_version="v1", invocation_ids=[],
                   status=P, validation=gt, conditional_validation=cond)
    with pytest.raises(ValidationError):
        StageRunRecord(stage=StageId.ANALYSIS, model_alias="A", model_id="x", prompt_version="v1",
                       invocation_ids=[], status=P, validation=cond)


def test_stage_benchmark_record_consistency():
    rec = _stage(0, "A", P)
    with pytest.raises(ValidationError):
        StageBenchmarkRecord(run_id="r", experiment_id="e", project_id="p", stage=StageId.ANALYSIS,
                             model_alias="A", canonical_inputs=[], config_hash="h", record=rec)


# ----------------------------------------------------------------------------- decision traces
def _pred(path, project="p2", run="r1"):
    return PathPrediction(path_id=path, feasibility_prob=0.9, quality={}, end_to_end_ms=1.0, cost_usd=None,
                          total_tokens=10, n_switches=n_switches(path),
                          evidence=[EvidenceRef(project_id=project, run_id=run, experiment_id="expB")])


def _trace(**kw):
    cands = kw.pop("candidates", [_pred("A-A-A"), _pred("A-B-C", run="r2")])
    base = dict(trace_id="t", created_at="now", strategy=Strategy.S3_WORKFLOW_AWARE, target_project="p1",
                held_out_project="p1", training_projects=["p2", "p3"],
                training_data_hash=DecisionTrace.compute_training_data_hash(cands),
                objective=RoutingObjective(objective_id="o", preference_order=["end_to_end_ms"]),
                candidates=cands, selection_steps=[SelectionStep(order=0, rule="feasibility_threshold", detail="p>=0.5",
                                                                 remaining=["A-A-A", "A-B-C"])],
                feasible_path_ids=["A-A-A", "A-B-C"], pareto_path_ids=["A-A-A"], selected_path_id="A-A-A",
                no_feasible_path=False, router_version="0", config_hash="h")
    base.update(kw)
    return DecisionTrace(**base)


def test_valid_trace():
    assert len(_trace().trace_hash()) == 64


def test_trace_declared_leakage_rejected():
    with pytest.raises(ValidationError, match="Leakage"):
        _trace(training_projects=["p1", "p2"])
    with pytest.raises(ValidationError, match="Leakage"):
        _trace(training_projects=[" P1 ", "p2"])  # normalisation defeats case/space tricks


def test_trace_evidence_leakage_rejected():  # review M6
    cands = [_pred("A-A-A"), _pred("A-B-C", project="P1", run="heldout_run")]
    with pytest.raises(ValidationError, match="Leakage: evidence"):
        _trace(candidates=cands)


def test_training_data_hash_must_match_evidence():
    with pytest.raises(ValidationError, match="training_data_hash"):
        _trace(training_data_hash="0" * 64)


def test_trace_set_consistency():  # review M10
    with pytest.raises(ValidationError):
        _trace(selected_path_id="C-C-C")                         # not feasible
    with pytest.raises(ValidationError):
        _trace(pareto_path_ids=["C-C-C"])                        # not subset of feasible
    with pytest.raises(ValidationError):
        _trace(feasible_path_ids=[], pareto_path_ids=[])          # selected but nothing feasible
    t = _trace(feasible_path_ids=[], pareto_path_ids=[], selected_path_id=None, no_feasible_path=True)
    assert t.no_feasible_path


def test_prospective_strategy_requires_holdout():
    with pytest.raises(ValidationError):
        _trace(held_out_project=None)
    _trace(strategy=Strategy.S4_ORACLE, held_out_project=None)   # oracle: retrospective, target only


# ----------------------------------------------------------------------------- counterfactuals
def _cf_fields(**kw):
    f = dict(prediction_id="c", trace_id="t", created_at="now", strategy=Strategy.S3_WORKFLOW_AWARE,
             router_version="0", config_hash="h", objective_id="o", held_out_project="p1",
             training_projects=["p3", "p2"], training_data_hash="d", selected_path_id="A-B-C",
             alternative_path_id="A-A-C",
             predicted_selected={"end_to_end_ms": 1000.0, "feasible": 0.9},
             predicted_alternative={"feasible": 0.8, "end_to_end_ms": 1100.0},
             predicted_delta={"end_to_end_ms": 100.0, "feasible": -0.1},
             predicted_delta_interval={"end_to_end_ms": (50.0, 150.0)})
    f.update(kw)
    return f


def test_counterfactual_create_and_roundtrip():
    cp = CounterfactualPrediction.create(**_cf_fields())
    assert len(cp.content_hash) == 64 and cp.training_projects == ["p2", "p3"]
    again = CounterfactualPrediction.model_validate(cp.model_dump())
    assert again.content_hash == cp.content_hash


def test_counterfactual_hash_stable_under_key_reordering():  # review M7
    cp = CounterfactualPrediction.create(**_cf_fields())
    reloaded = json.loads(json.dumps(cp.model_dump(mode="json"), sort_keys=True))
    assert CounterfactualPrediction.model_validate(reloaded).content_hash == cp.content_hash


def test_counterfactual_tampering_detected():
    cp = CounterfactualPrediction.create(**_cf_fields())
    tampered = cp.model_dump()
    tampered["predicted_delta"] = {"end_to_end_ms": -5.0, "feasible": -0.1}
    with pytest.raises(ValidationError, match="hash mismatch"):
        CounterfactualPrediction.model_validate(tampered)
    tampered["content_hash"] = ""                       # reset-and-rehash attack
    with pytest.raises(ValidationError, match="hash mismatch"):
        CounterfactualPrediction.model_validate(tampered)
    with pytest.raises(ValidationError):                # frozen: no in-place edits
        cp.selected_path_id = "B-B-B"


def test_counterfactual_rejects_leakage_and_oracle():
    with pytest.raises(ValidationError, match="Leakage"):
        CounterfactualPrediction.create(**_cf_fields(training_projects=["P1"]))
    with pytest.raises(ValidationError, match="prospective"):
        CounterfactualPrediction.create(**_cf_fields(strategy=Strategy.S4_ORACLE))


def test_validation_checks_prediction_hash():
    cp = CounterfactualPrediction.create(**_cf_fields())
    v = CounterfactualValidation(prediction_id="c", prediction_hash=cp.content_hash, validated_at="later",
                                 actual_selected={}, actual_alternative={}, actual_delta={}, abs_error={},
                                 direction_correct={}, actual_outcome={"selected": "feasible", "alternative": "infeasible"},
                                 selected_run_ids=["r1"], alternative_run_ids=["r2"])
    v.check_against(cp)
    other = CounterfactualPrediction.create(**_cf_fields(predicted_delta={"end_to_end_ms": 1.0}))
    with pytest.raises(ValueError):
        v.check_against(other)


# ----------------------------------------------------------------------------- v1.2 propagation policy
from src.contracts import PropagationSummary, ProjectSpec  # noqa: E402

B = StageStatus.BLOCKED_BY_INVALID_ARTIFACT


def _crun(path, statuses, outcome, blocked=(), first=None, prop=True):
    models = path.split("-")
    stages = []
    for i, (m, st) in enumerate(zip(models, statuses)):
        ft = FailureType.VALIDATION_FAILED if st == F else (FailureType.INFRA if st == I else None)
        stages.append(StageRunRecord(stage=STAGE_ORDER[i], model_alias=m, model_id="x", prompt_version="v1",
                                     invocation_ids=[] if st in (B, N) else ["i"], status=st, failure_type=ft,
                                     failure_detail="upstream cleaned.csv unparseable" if st == B else None))
    return WorkflowRunRecord(
        run_id="r", experiment_id="e", project_id="p", path_id=path, models=models, config_hash="h",
        started_at="t", stages=stages, failure_policy="continue_with_actual_artifact",
        feasibility=Feasibility(outcome=outcome, stage_status={s.stage.value: s.status for s in stages},
                                first_failure_stage=first),
        propagation=PropagationSummary(downstream_executable={}, blocked_stages=list(blocked)) if prop else None,
        efficiency=WorkflowEfficiency())


def test_continue_policy_lets_failed_upstream_flow_downstream():
    r = _crun("A-B-C", [F, P, F], "infeasible", first=StageId.CLEANING)
    assert r.stages[1].status == P and not r.feasibility.feasible   # strict gate still fails


def test_continue_policy_blocked_downstream_attributed_upstream():
    r = _crun("A-B-C", [F, B, B], "infeasible", blocked=("analysis", "reporting"), first=StageId.CLEANING)
    assert r.propagation.blocked_stages == ["analysis", "reporting"]
    with pytest.raises(ValidationError):   # cannot run after a blocked stage
        _crun("A-B-C", [F, B, P], "infeasible", blocked=("analysis",), first=StageId.CLEANING)
    with pytest.raises(ValidationError):   # first stage reads raw input, cannot be blocked
        _crun("A-B", [B, B], "infeasible", blocked=("cleaning", "analysis"), first=StageId.CLEANING)


def test_continue_policy_requires_propagation_summary_and_terminate_forbids_blocked():
    with pytest.raises(ValidationError, match="PropagationSummary"):
        _crun("A-B", [F, P], "infeasible", first=StageId.CLEANING, prop=False)
    with pytest.raises(ValidationError):
        _run("A-B", [F, B], "infeasible", first=StageId.CLEANING)


def test_project_model_view_hides_notes_and_ground_truth():
    import pathlib
    for pj in pathlib.Path("datasets/projects").glob("*/project.json"):
        spec = ProjectSpec.model_validate_json(pj.read_text())
        view = json.dumps(spec.model_view())
        assert "notes" not in spec.model_view() and "canonical" not in view and "ground_truth" not in view
        assert all("canonical" not in f.path for f in spec.model_input_files())
