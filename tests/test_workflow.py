"""Offline workflow tests (M3/M4). No AWS calls; no model-generated code is executed.

Fakes (tests/fixtures/workflow/fakes.py, SYNTHETIC_FIXTURE): a scripted bedrock-runtime inside a real
BedrockClient, and an executor that only runs the Benchmark's trusted solution scripts.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.bedrock.provenance import hash_file
from src.contracts import (
    STAGES,
    ExecutionStatus,
    FailureType,
    StageId,
    StageStatus,
    WorkflowRunRecord,
    enumerate_paths,
)
from src.evaluation.workflow_metrics import group_by_switching, load_runs, summarize_paths
from src.storage import STAGE_BENCHMARK, DuplicateRunError, ExperimentModeError, RunStore
from src.workflow.orchestrator import (
    PRIMARY_EXPERIMENT_ID,
    SHARED_PREFIX_EXPERIMENT_ID,
    RunAlreadyCompleted,
    WorkflowOrchestrator,
)
from src.workflow.stages import PROMPT_VERSION, SandboxGate, display_path, load_template, reporting_prompt_v3
from tests.fixtures.workflow.fakes import (
    FAKE_IMAGE,
    PROJECTS,
    FakeBedrockRuntime,
    FixtureExecutor,
    make_client,
)

PID = "retail_sales"
PDIR = PROJECTS / PID
GT = json.loads((PDIR / "ground_truth.json").read_text())


@pytest.fixture(scope="module")
def executor():
    return FixtureExecutor()   # memoises trusted-script runs across tests


def make_orch(tmp_path, executor, behaviours=None, *, experiment_id=PRIMARY_EXPERIMENT_ID, mode="fresh",
              gate=None, policy="continue_with_actual_artifact", **kw):
    rt = FakeBedrockRuntime(behaviours)
    client = make_client(tmp_path, rt)
    store = RunStore(experiment_id, root=tmp_path / "results")
    orch = WorkflowOrchestrator(client, executor, store, gate=gate or SandboxGate.unverified_test_bypass(),
                                mode=mode, failure_policy=policy, **kw)
    return orch, rt, client, store


def statuses(rec: WorkflowRunRecord):
    return [s.status for s in rec.stages]


def test_prompt_v2_requires_a_numeric_finding_statement():
    assert PROMPT_VERSION == "v2"
    reporting = load_template(StageId.REPORTING)
    assert "statement MUST state at least one verified numeric value" in reporting


def test_post_freeze_prompt_v3_exposes_exact_structured_claim_contract():
    from src.contracts import ProjectSpec, StageId
    from src.workflow.handoff import build_handoff, canonical_upstream

    spec = ProjectSpec.model_validate_json((PDIR / "project.json").read_text())
    handoff = build_handoff(spec, "A-A-A", StageId.REPORTING,
                            canonical_upstream(spec, PDIR, StageId.REPORTING))
    prompt = reporting_prompt_v3(spec, handoff, GT["analysis"]["metrics"])
    assert "PROMPT_VERSION: v3-post-freeze" in prompt
    assert '"q3"' in prompt and '"ranking_required": true' in prompt
    assert '"revenue_2024_q3": "Q3"' in prompt
    assert "including trend questions" in prompt


def invocations(tmp_path):
    p = tmp_path / "invocations.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []


# --------------------------------------------------------------------------- M3: one full workflow
def test_full_three_stage_path_passes_end_to_end(tmp_path, executor):
    orch, rt, _, store = make_orch(tmp_path, executor)
    rec = orch.run_path(PID, "A-B-C", PRIMARY_EXPERIMENT_ID, 0)
    assert rec.feasibility.outcome == "feasible"
    assert statuses(rec) == [StageStatus.PASSED] * 3
    assert [s.model_alias for s in rec.stages] == ["A", "B", "C"]
    assert rec.failure_policy == "continue_with_actual_artifact" and rec.propagation is not None
    assert rec.quality["cleaning"]["cleaning_correctness"] == 1.0
    assert rec.quality["analysis"]["numerical_accuracy"] == 1.0
    assert rec.quality["analysis"]["reproducibility"] == 1.0
    assert rec.quality["reporting"]["unsupported_claim_count"] == 0.0
    an = rec.stages[1]
    assert an.conditional_validation.quality_basis == "conditional_reference"
    assert rec.stages[2].conditional_validation.quality_basis == "conditional_reference"
    for s in rec.stages:
        assert s.prompt_hash and len(s.invocation_ids) == 1 and s.cache_hit is False
        assert s.cost_usd is None and s.cost_status == "unavailable"        # unpriced: never 0
        assert s.timings.generation_ms is not None and s.timings.handoff_ms is not None
        assert s.handoff_in_path and s.handoff_size_bytes > 0 and s.structural_ok is True
        assert all(len(h) == 64 for h in s.output_artifact_hashes.values())
    assert rec.efficiency.cost_usd is None and rec.efficiency.n_calls == 3 and rec.efficiency.n_switches == 2
    assert rec.efficiency.end_to_end_ms >= rec.efficiency.total_api_latency_ms
    run_dir = store.run_dir(rec.run_id)
    for st in ("cleaning", "analysis", "reporting"):
        for f in ("handoff_in.json", "prompt.txt", "response.txt", "parsed.json", "stage_record.json"):
            assert (run_dir / st / f).is_file(), (st, f)
    report_md = run_dir / "reporting" / "output" / "report.md"
    assert report_md.is_file()
    rendered = report_md.read_text()
    assert "Reported values:" in rendered and "Direction:" in rendered and "Ranking:" in rendered
    assert (run_dir / "run_record.json").is_file()
    # the stored line round-trips through the v1.2 validators
    assert store.load_records()[0] == rec
    assert len(rt.calls) == 3


def test_reporting_receives_trusted_cleaning_counts(tmp_path, executor, monkeypatch):
    import src.workflow.stages as stage_module

    original = stage_module.validate_reporting
    seen = []

    def spy(*args, **kwargs):
        seen.append(kwargs.get("cleaning_counts"))
        return original(*args, **kwargs)

    monkeypatch.setattr(stage_module, "validate_reporting", spy)
    rec = make_orch(tmp_path, executor)[0].run_path(PID, "A-B-C", PRIMARY_EXPERIMENT_ID, 0)
    assert rec.feasibility.outcome == "feasible"
    assert seen == [GT["cleaning"]["rule_log"], None]


def test_stage2_consumes_stage1_actual_output(tmp_path, executor):
    orch, rt, _, store = make_orch(tmp_path, executor)
    rec = orch.run_path(PID, "A-B", PRIMARY_EXPERIMENT_ID, 0)
    cl, an = rec.stages
    cleaned = store.run_dir(rec.run_id) / "cleaning" / "output" / "cleaned.csv"
    key = display_path(cleaned)
    assert cl.output_artifact_hashes[key] == an.input_artifact_hashes[key] == hash_file(cleaned)
    assert an.input_artifacts == [key]
    # the sandbox received exactly that file, and the prompt shows its first line
    an_call = [c for c in executor.calls if c["output_dir"] == str(cleaned.parent.parent.parent / "analysis" / "output")]
    assert an_call and an_call[0]["inputs"] == {"cleaned.csv": str(cleaned)}
    assert cleaned.read_text().splitlines()[1] in rt.calls[1]["prompt"]
    # canonical file was not used
    assert "canonical" not in json.dumps(an.input_artifacts)


# --------------------------------------------------------------------------- continue policy / propagation
def test_imperfect_cleaned_csv_propagates_to_analysis(tmp_path, executor):
    """no_dedup: the cleaned CSV parses and has every column but fails validation (duplicates)."""
    orch, rt, _, store = make_orch(tmp_path, executor, {("B", "cleaning"): "bug:no_dedup"})
    rec = orch.run_path(PID, "B-A-C", PRIMARY_EXPERIMENT_ID, 0)
    cl, an, rp = rec.stages
    assert cl.status == StageStatus.FAILED and cl.failure_type == FailureType.VALIDATION_FAILED
    assert cl.structural_ok is True
    assert an.invocation_ids and rp.invocation_ids                  # downstream stages really ran
    assert an.status == StageStatus.FAILED                          # vs ground truth
    assert rec.feasibility.outcome == "infeasible" and rec.feasibility.first_failure_stage == StageId.CLEANING
    sev = rec.propagation.upstream_error_severity["analysis"]
    assert sev["data_integrity"] > 0
    # conditional quality: analysis did its own job correctly on the data it received
    assert rec.conditional_quality["analysis"]["numerical_accuracy"] == 1.0
    assert rec.propagation.propagation_impact["analysis"]["numerical_accuracy"] > 0
    assert rec.propagation.downstream_executable == {"cleaning": True, "analysis": True, "reporting": True}
    # analysis consumed the FAILED actual artifact, never the canonical one
    cleaned = store.run_dir(rec.run_id) / "cleaning" / "output" / "cleaned.csv"
    assert an.input_artifacts == [display_path(cleaned)]
    assert hash_file(cleaned) != hash_file(PDIR / "canonical" / "cleaned.csv")
    handoff = json.loads((store.run_dir(rec.run_id) / "analysis" / "handoff_in.json").read_text())
    assert handoff["validation_status"] == {"cleaning": "failed"}


def test_unconsumable_artifact_blocks_downstream(tmp_path, executor):
    orch, rt, _, _ = make_orch(tmp_path, executor, {("C", "cleaning"): "bug:drop_revenue"})
    rec = orch.run_path(PID, "C-A-A", PRIMARY_EXPERIMENT_ID, 0)
    assert statuses(rec) == [StageStatus.FAILED, StageStatus.BLOCKED_BY_INVALID_ARTIFACT,
                             StageStatus.BLOCKED_BY_INVALID_ARTIFACT]
    assert "cleaned_csv" in rec.stages[1].failure_detail
    assert rec.stages[1].invocation_ids == [] and len(rt.calls) == 1
    assert rec.propagation.blocked_stages == ["analysis", "reporting"]
    assert rec.feasibility.outcome == "infeasible"


def test_parse_failure_blocks_under_continue(tmp_path, executor):
    orch, rt, _, _ = make_orch(tmp_path, executor, {("A", "cleaning"): "garbage"})
    rec = orch.run_path(PID, "A-B-C", PRIMARY_EXPERIMENT_ID, 0)
    assert rec.stages[0].failure_type == FailureType.PARSE_ERROR
    assert statuses(rec)[1:] == [StageStatus.BLOCKED_BY_INVALID_ARTIFACT] * 2
    assert len(rt.calls) == 1


# --------------------------------------------------------------------------- terminate policy
def test_injected_cleaning_failure_terminates_and_stays_visible(tmp_path, executor):
    orch, rt, _, _ = make_orch(tmp_path, executor, {("A", "cleaning"): "bug:no_dedup"},
                               policy="terminate_on_mandatory_failure")
    rec = orch.run_path(PID, "A-B-C", PRIMARY_EXPERIMENT_ID, 0)
    assert rec.feasibility.outcome == "infeasible"
    assert statuses(rec) == [StageStatus.FAILED, StageStatus.NOT_RUN_UPSTREAM_FAILURE,
                             StageStatus.NOT_RUN_UPSTREAM_FAILURE]
    assert rec.stages[0].validation.hard_pass is False          # failure visible per stage
    assert rec.feasibility.failure_type == FailureType.VALIDATION_FAILED
    assert len(rt.calls) == 1 and rec.propagation is None


def test_truncated_output_is_model_failure(tmp_path, executor):
    orch, _, _, _ = make_orch(tmp_path, executor, {("B", "analysis"): "truncated"},
                              policy="terminate_on_mandatory_failure")
    rec = orch.run_path(PID, "A-B-C", PRIMARY_EXPERIMENT_ID, 0)
    assert rec.stages[1].failure_type == FailureType.TRUNCATED and rec.feasibility.outcome == "infeasible"


def test_unknown_failure_policy_refused(tmp_path, executor):
    with pytest.raises(NotImplementedError):
        make_orch(tmp_path, executor, policy="retry_forever")


# --------------------------------------------------------------------------- infra failures
@pytest.mark.parametrize("behaviour,ftype", [("throttle", FailureType.API_ERROR),
                                             ("access_denied", FailureType.API_ERROR)])
def test_api_infra_failure_is_void(tmp_path, executor, behaviour, ftype):
    orch, _, _, _ = make_orch(tmp_path, executor, {("B", "analysis"): behaviour})
    rec = orch.run_path(PID, "A-B-C", PRIMARY_EXPERIMENT_ID, 0)
    assert rec.feasibility.outcome == "void_infra"
    assert statuses(rec) == [StageStatus.PASSED, StageStatus.INFRA_ERROR, StageStatus.NOT_RUN_UPSTREAM_FAILURE]
    assert rec.stages[1].failure_type == ftype


def test_sandbox_unavailable_is_void(tmp_path):
    orch, _, _, _ = make_orch(tmp_path, FixtureExecutor(ExecutionStatus.SANDBOX_UNAVAILABLE))
    rec = orch.run_path(PID, "A-B", PRIMARY_EXPERIMENT_ID, 0)
    assert rec.feasibility.outcome == "void_infra" and rec.stages[0].failure_type == FailureType.INFRA


def test_budget_refusal_is_void(tmp_path, executor):
    from src.bedrock.usage import UsageLimits
    rt = FakeBedrockRuntime()
    client = make_client(tmp_path, rt, UsageLimits(max_calls=1, max_input_tokens=10**9, max_output_tokens=10**9))
    orch = WorkflowOrchestrator(client, executor, RunStore(PRIMARY_EXPERIMENT_ID, root=tmp_path / "r"),
                                gate=SandboxGate.unverified_test_bypass())
    rec = orch.run_path(PID, "A-B", PRIMARY_EXPERIMENT_ID, 0)
    assert rec.feasibility.outcome == "void_infra"
    assert rec.stages[1].failure_type == FailureType.INFRA and rec.stages[1].cost_status == "not_incurred"


# --------------------------------------------------------------------------- sandbox gate
class _StubDocker:
    """Has availability() like DockerExecutor; delegates execution to the fixture executor."""
    image = "model-routing-xai-sandbox:1.0"

    def __init__(self, inner, image_id):
        self.inner, self.image_id_ = inner, image_id

    def availability(self):
        return True, self.image_id_

    def execute(self, *a, **k):
        return self.inner.execute(*a, **k)


def test_sandbox_gate_refuses_without_verification_record(tmp_path):
    ex = FixtureExecutor()
    gate = SandboxGate(tmp_path / "missing.json")
    orch, rt, _, _ = make_orch(tmp_path, ex, gate=gate)
    rec = orch.run_path(PID, "A-B", PRIMARY_EXPERIMENT_ID, 0)
    assert rec.feasibility.outcome == "void_infra"
    assert rec.stages[0].status == StageStatus.INFRA_ERROR and "sandbox gate refused" in rec.stages[0].failure_detail
    assert rt.calls == [] and ex.calls == []             # no paid call, no execution


def test_sandbox_gate_checks_flag_and_image_id(tmp_path, executor):
    vf = tmp_path / "sandbox_verification.json"
    stub = _StubDocker(executor, FAKE_IMAGE)
    vf.write_text(json.dumps({"all_controls_verified": False, "image_id": FAKE_IMAGE}))
    assert not SandboxGate(vf).check(stub).ok
    vf.write_text(json.dumps({"all_controls_verified": True, "image_id": "sha256:other"}))
    d = SandboxGate(vf).check(stub)
    assert not d.ok and "image ID" in d.reason
    vf.write_text(json.dumps({"all_controls_verified": True, "image_id": FAKE_IMAGE,
                              "image": "model-routing-xai-sandbox:1.0"}))
    assert SandboxGate(vf).check(stub).ok
    orch, _, _, _ = make_orch(tmp_path, stub, gate=SandboxGate(vf))
    assert orch.run_path(PID, "A-B", PRIMARY_EXPERIMENT_ID, 0).feasibility.outcome == "feasible"


# --------------------------------------------------------------------------- M4: grid, resume, fresh calls
def test_nine_two_stage_and_27_three_stage_paths_run(tmp_path, executor):
    from experiments.run_workflow_grid import execute_plan, plan_grid
    orch, rt, client, store = make_orch(tmp_path, executor)
    for n, expected in ((2, 9), (3, 27)):
        plan = plan_grid([PID], n, registry=client.registry, results_root=tmp_path / "results")
        assert plan.paths == enumerate_paths(["A", "B", "C"], n) and len(plan.paths) == expected
        out = execute_plan(plan, orch, log=lambda *_: None)
        assert len(out["executed"]) == expected
    recs = store.load_records()
    assert len(recs) == 36 and all(r.feasibility.outcome == "feasible" for r in recs)
    assert len({r.run_id for r in recs}) == 36
    assert len(rt.calls) == 9 * 2 + 27 * 3
    summary = summarize_paths(recs)[PID]
    assert summary["A-B-C"]["feasibility_rate"] == 1.0 and summary["A-B-C"]["efficiency"]["cost_usd"] is None
    groups = group_by_switching(recs)[PID]
    assert groups["same_model"]["n_runs"] == 3 + 3 and groups["cross_model"]["n_runs"] == 30


def test_resume_skips_completed_runs(tmp_path, executor):
    from experiments.run_workflow_grid import execute_plan, plan_grid
    orch, rt, client, store = make_orch(tmp_path, executor, {("C", "cleaning"): "garbage"})
    root = tmp_path / "results"
    first = execute_plan(plan_grid([PID], 2, paths=["A-A", "C-A"], registry=client.registry, results_root=root),
                         orch, log=lambda *_: None)
    assert len(first["executed"]) == 2
    n_calls = len(rt.calls)
    plan = plan_grid([PID], 2, registry=client.registry, results_root=root)
    assert plan.totals()["n_runs_completed_skipped"] == 2 and plan.totals()["planned_model_calls"] == 7 * 2
    second = execute_plan(plan, orch, log=lambda *_: None)
    assert sorted(second["skipped_completed"]) == sorted(first["executed"])    # incl. the infeasible C-A
    # 7 runs; C-B and C-C are blocked after C's unparseable cleaning (1 call each) -> 5*2 + 2*1
    assert len(second["executed"]) == 7 and len(rt.calls) == n_calls + 12
    with pytest.raises(RunAlreadyCompleted):
        orch.run_path(PID, "A-A", PRIMARY_EXPERIMENT_ID, 0)
    with pytest.raises(DuplicateRunError):
        store.append(store.load_records()[0])
    assert len(store.load_records()) == 9          # failed run kept, nothing duplicated


def test_interrupted_run_dir_is_moved_aside(tmp_path, executor):
    orch, _, _, store = make_orch(tmp_path, executor)
    rid = orch.run_id(PID, "A-A", 0)
    stale = store.run_dir(rid)
    stale.mkdir(parents=True)
    (stale / "partial.txt").write_text("x")
    orch.run_path(PID, "A-A", PRIMARY_EXPERIMENT_ID, 0)
    assert not (stale / "partial.txt").exists()
    assert list(stale.parent.glob(f"{rid}.incomplete-*/partial.txt"))


def test_primary_mode_makes_fresh_calls_with_separate_artifacts(tmp_path, executor):
    orch, rt, _, store = make_orch(tmp_path, executor)
    r1 = orch.run_path(PID, "A-B", PRIMARY_EXPERIMENT_ID, 0)
    r2 = orch.run_path(PID, "A-C", PRIMARY_EXPERIMENT_ID, 0)     # same cleaning prompt and model
    r3 = orch.run_path(PID, "A-B", PRIMARY_EXPERIMENT_ID, 1)     # repeat
    assert len({r1.run_id, r2.run_id, r3.run_id}) == 3
    assert len(rt.calls) == 6                                    # nothing served from a cache
    inv = invocations(tmp_path)
    assert len(inv) == 6 and not any(i["from_cache"] for i in inv)
    assert all(i["cache_namespace"] is None for i in inv)
    assert {i["context"]["repeat_index"] for i in inv} == {0, 1}
    assert not (tmp_path / "cache").exists() or not any((tmp_path / "cache").iterdir())
    dirs = [store.run_dir(r.run_id) for r in (r1, r2, r3)]
    assert len(set(dirs)) == 3 and all(d.is_dir() for d in dirs)
    a = dirs[0] / "cleaning" / "output" / "cleaned.csv"
    b = dirs[1] / "cleaning" / "output" / "cleaned.csv"
    assert a != b and a.is_file() and b.is_file()
    assert all(not s.cache_hit and not s.shared_with_run_ids for r in (r1, r2, r3) for s in r.stages)


def test_shared_prefix_mode_is_separate(tmp_path, executor):
    with pytest.raises(ValueError):
        make_orch(tmp_path, executor, experiment_id=PRIMARY_EXPERIMENT_ID, mode="shared_prefix")
    orch, rt, _, store = make_orch(tmp_path, executor, experiment_id=SHARED_PREFIX_EXPERIMENT_ID,
                                   mode="shared_prefix")
    r1 = orch.run_path(PID, "A-B", SHARED_PREFIX_EXPERIMENT_ID, 0)
    r2 = orch.run_path(PID, "A-C", SHARED_PREFIX_EXPERIMENT_ID, 0)
    assert r2.stages[0].cache_hit is True and r2.efficiency.n_cache_hits == 1
    assert r1.run_id in r2.stages[0].shared_with_run_ids
    assert len(rt.calls) == 3
    # results live in a different file; the store refuses to mix modes
    assert store.records_path.name == f"{SHARED_PREFIX_EXPERIMENT_ID}.jsonl"
    with pytest.raises(ExperimentModeError):
        RunStore(SHARED_PREFIX_EXPERIMENT_ID, root=tmp_path / "results", mode="fresh")
    assert not (tmp_path / "results" / "workflow_runs" / f"{PRIMARY_EXPERIMENT_ID}.jsonl").exists()


# --------------------------------------------------------------------------- plan mode
def test_plan_mode_makes_zero_aws_calls(tmp_path, monkeypatch, capsys):
    import boto3

    from experiments import run_workflow_grid as g

    def boom(*a, **k):
        raise AssertionError("AWS session created in plan mode")
    monkeypatch.setattr(boto3, "Session", boom)
    monkeypatch.setattr(boto3, "client", boom)
    assert g.main(["--projects", PID, "--stages", "3", "--results-root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert '"planned_model_calls": 81' in out and "PLAN ONLY" in out
    with pytest.raises(SystemExit):
        g.main(["--projects", PID, "--stages", "2", "--execute", "--results-root", str(tmp_path)])


def test_paid_runner_refuses_missing_sandbox_before_bedrock_client(tmp_path, monkeypatch):
    from experiments import run_workflow_grid as g
    from src.bedrock import client as client_module
    from src.workflow import executor as executor_module

    class MissingDocker:
        image = "model-routing-xai-sandbox:1.0"

        def availability(self):
            return False, "synthetic missing image"

    def boom(*args, **kwargs):
        raise AssertionError("BedrockClient constructed before sandbox preflight")

    monkeypatch.setattr(executor_module, "DockerExecutor", MissingDocker)
    monkeypatch.setattr(client_module, "BedrockClient", boom)
    with pytest.raises(SystemExit, match="sandbox preflight failed before any model call"):
        g.main(["--projects", PID, "--stages", "2", "--execute", "--results-root", str(tmp_path),
                "--max-calls", "30", "--max-input-tokens", "300000", "--max-output-tokens", "80000"])


def test_paid_stage_runner_refuses_missing_sandbox_before_bedrock_client(tmp_path, monkeypatch):
    from experiments import run_stage_benchmark as b
    from src.bedrock import client as client_module
    from src.workflow import executor as executor_module

    class MissingDocker:
        image = "model-routing-xai-sandbox:1.0"

        def availability(self):
            return False, "synthetic missing image"

    def boom(*args, **kwargs):
        raise AssertionError("BedrockClient constructed before sandbox preflight")

    monkeypatch.setattr(executor_module, "DockerExecutor", MissingDocker)
    monkeypatch.setattr(client_module, "BedrockClient", boom)
    with pytest.raises(SystemExit, match="sandbox preflight failed before any model call"):
        b.main(["--projects", PID, "--execute", "--results-root", str(tmp_path),
                "--max-calls", "15", "--max-input-tokens", "200000", "--max-output-tokens", "40000"])


def test_estimate_pilot_usage():
    from experiments.run_workflow_grid import estimate_pilot_usage
    a = estimate_pilot_usage([PID], 2)
    b = estimate_pilot_usage([PID], 3)
    assert a["planned_model_calls"] == 18 and a["planned_calls_by_stage"] == {"cleaning": 9, "analysis": 9}
    assert b["planned_model_calls"] == 81
    assert a["worst_case_output_tokens"] == 18 * 4096 and b["worst_case_output_tokens"] == 81 * 4096
    assert 0 < a["worst_case_input_tokens"] < b["worst_case_input_tokens"]
    shared = estimate_pilot_usage([PID], 3, mode="shared_prefix")
    assert shared["planned_model_calls"] == 3 + 9 + 27


def test_prompt_bound_covers_actual_prompts(tmp_path, executor):
    from src.bedrock.client import estimate_input_tokens_upper
    from src.contracts import ProjectSpec
    from src.workflow.stages import prompt_input_token_upper_bound
    orch, rt, _, _ = make_orch(tmp_path, executor)
    orch.run_path(PID, "A-B-C", PRIMARY_EXPERIMENT_ID, 0)
    spec = ProjectSpec.model_validate_json((PDIR / "project.json").read_text())
    for call, st in zip(rt.calls, STAGES):
        actual = estimate_input_tokens_upper([{"role": "user", "content": [{"text": call["prompt"]}]}], None)
        assert actual <= prompt_input_token_upper_bound(st, spec, PDIR)


# --------------------------------------------------------------------------- leakage & allow-list
def test_no_ground_truth_leakage_into_prompts_or_handoffs(tmp_path, executor):
    """Failing upstream stage: nothing a model sees contains validator details or reference values."""
    orch, rt, _, store = make_orch(tmp_path, executor, {("A", "cleaning"): "bug:no_dedup"})
    rec = orch.run_path(PID, "A-B-C", PRIMARY_EXPERIMENT_ID, 0)
    assert rec.stages[0].status == StageStatus.FAILED and "repeat an existing" in rec.stages[0].failure_detail
    spec = json.loads((PDIR / "project.json").read_text())
    # validator detail phrasing ("(expected 445325.07)", "reference rows missing"), not the
    # legitimate AnalysisOutput field name `expected_artifacts`
    forbidden = ["(expected", "expected ", "reference", "canonical", "ground_truth", "tolerance", "repeat an existing",
                 "no_duplicate_keys", "values_within_tolerance", spec["notes"][:60], "Known raw imperfections"]
    gt_values = [repr(v) for k, v in GT["analysis"]["metrics"].items()
                 if k in ("total_revenue", "order_count", "average_order_value", "revenue_north")]
    run_dir = store.run_dir(rec.run_id)
    seen = [c["prompt"] for c in rt.calls]
    for s in ("analysis", "reporting"):
        h = json.loads((run_dir / s / "handoff_in.json").read_text())
        # executed_code / stage_outputs are the (fixture) model's own text; everything else is harness-written
        h.pop("executed_code"), h.pop("stage_outputs")
        seen.append(json.dumps(h))
    for text in seen:
        text = text.replace(str(tmp_path), "<tmp>")    # pytest's tmp dir is named after this test
        for f in forbidden + gt_values:
            assert f not in text, f
    for s in ("analysis", "reporting"):
        h = json.loads((run_dir / s / "handoff_in.json").read_text())
        assert set(h["validation_status"].values()) <= {"passed", "failed"}


def test_input_allow_list(tmp_path):
    ex = FixtureExecutor()
    orch, rt, _, store = make_orch(tmp_path, ex)
    rec = orch.run_path(PID, "A-B", PRIMARY_EXPERIMENT_ID, 0)
    cl_call, an_call = ex.calls[0], ex.calls[1]
    assert cl_call["inputs"] == {"raw.csv": str(PDIR / "raw.csv")}
    assert an_call["inputs"] == {"cleaned.csv": str(store.run_dir(rec.run_id) / "cleaning" / "output" / "cleaned.csv")}
    for c in ex.calls:
        assert not any("canonical" in p or "ground_truth" in p for p in c["inputs"].values())
    assert rec.stages[0].input_artifacts == [display_path(PDIR / "raw.csv")]


# --------------------------------------------------------------------------- Experiment A
def test_stage_benchmark_on_canonical_inputs(tmp_path, executor):
    from experiments.run_stage_benchmark import plan_stage_benchmark, run_stage_benchmark
    rt = FakeBedrockRuntime({("B", "analysis"): "bug:population_std"})
    client = make_client(tmp_path, rt)
    store = RunStore("expA_stage", root=tmp_path / "results", kind=STAGE_BENCHMARK)
    gate = SandboxGate.unverified_test_bypass()
    recs = {}
    for st in STAGES:
        for a in ("A", "B"):
            recs[(st, a)] = run_stage_benchmark(client, executor, store, PID, st, a, 0, gate=gate)
    assert recs[(StageId.ANALYSIS, "A")].record.status == StageStatus.PASSED
    assert recs[(StageId.ANALYSIS, "B")].record.status == StageStatus.FAILED
    assert recs[(StageId.REPORTING, "A")].record.status == StageStatus.PASSED
    an = recs[(StageId.ANALYSIS, "A")]
    assert an.canonical_inputs == [display_path(PDIR / "canonical" / "cleaned.csv")]
    assert executor.calls[-1]["inputs"] != {}      # sanity
    assert len(store.load_records()) == 6
    plan = plan_stage_benchmark([PID], registry=client.registry, results_root=tmp_path / "results")
    assert plan["planned_model_calls"] == 3 and len(plan["skipped_completed"]) == 6


# --------------------------------------------------------------------------- metrics
def test_metrics_from_raw_records_only(tmp_path, executor):
    orch, _, _, store = make_orch(tmp_path, executor, {("B", "cleaning"): "bug:no_dedup",
                                                      ("C", "analysis"): "throttle"})
    for p in ("A-A", "B-A", "A-C"):
        orch.run_path(PID, p, PRIMARY_EXPERIMENT_ID, 0)
    runs = load_runs(store.records_path)
    s = summarize_paths(runs)[PID]
    assert s["A-A"]["feasibility_rate"] == 1.0 and s["A-A"]["same_model"] is True
    assert s["B-A"]["feasibility_rate"] == 0.0 and s["B-A"]["first_failure_stage"] == {"cleaning": 1}
    assert s["A-C"]["n_void_infra"] == 1 and s["A-C"]["feasibility_rate"] is None
    assert s["B-A"]["conditional_quality"]["analysis"]["numerical_accuracy"]["mean"] == 1.0
    eff = s["A-A"]["efficiency"]
    assert eff["end_to_end_ms"] is not None and eff["total_api_latency_ms"] is not None
    assert eff["cost_usd"] is None and eff["cost_status"] == "unavailable"
    other = runs[0].model_copy(update={"experiment_id": SHARED_PREFIX_EXPERIMENT_ID})
    with pytest.raises(ValueError):
        summarize_paths(runs + [other])


# --------------------------------------------------------------------------- protocol v3 (prospective primary)
def test_protocol_v3_uses_v3_prompts_and_validator(tmp_path, executor):
    orch, rt, _, store = make_orch(tmp_path, executor, experiment_id=PRIMARY_EXPERIMENT_ID + "_v3", protocol="v3")
    rec = orch.run_path(PID, "A-B-C", PRIMARY_EXPERIMENT_ID + "_v3", 0)
    assert all(s.prompt_version == "v3" for s in rec.stages)
    assert all("PROMPT_VERSION: v3" in c["prompt"] for c in rt.calls)
    assert "ranking_metric_key_to_label" in rt.calls[-1]["prompt"]          # v3 reporting contract shown
    v2 = make_orch(tmp_path / "v2", executor)[0]
    assert orch.run_id(PID, "A-B-C") != v2.run_id(PID, "A-B-C")           # never collide with v2 runs


def test_protocol_and_experiment_id_cannot_mix(tmp_path, executor):
    with pytest.raises(ValueError, match="cannot write"):
        make_orch(tmp_path, executor, protocol="v3")                        # v3 into the v2 experiment
    with pytest.raises(ValueError, match="cannot write"):
        make_orch(tmp_path, executor, experiment_id=PRIMARY_EXPERIMENT_ID + "_v3")   # v2 into a v3 experiment
