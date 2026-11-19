"""Offline price-matched workflow protocol and runner tests; no paid client is constructed."""

from __future__ import annotations

import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from experiments import build_price_matched_workflow_main_manifest as manifest_builder
from experiments import run_price_matched_workflow as workflow


def test_plan_has_exact_new_only_design_and_main_approval():
    plan = workflow.build_plan()
    assert plan["status"] == "main_approved_pending_freeze_tag"
    assert plan["user_decision"] == {
        "wording": "16384, $100 cap",
        "date": "2026-11-19",
        "selected_maxTokens": 16384,
        "hard_budget_cap_usd": 100.0,
        "pilot_approved": True,
        "main_approved": True,
        "pilot_requires_separate_explicit_approval": True,
        "main_requires_separate_explicit_approval": True,
    }
    assert plan["main_approval"] == {
        "wording": "Approve the main run (504 calls, about $43 expected, $100 cap)",
        "date": "2026-11-19",
        "logical_call_ceiling": 504,
        "realistic_estimate_usd_rounded": 43,
        "hard_budget_cap_usd": 100.0,
    }
    assert plan["call_counts"] == {
        "part_a": 36, "part_b_main": 324, "part_b_repeats": 144,
        "pilot": 9, "main": 504, "combined": 513,
    }
    assert plan["fixed"]["repeat_paths"] == list(workflow.REPEAT_PATHS)


def test_registry_maps_abc_to_verified_price_matched_models_and_kimi_omits_temperature():
    registry = workflow.registry(4096)
    assert [registry.get(alias).model_id for alias in "ABC"] == [
        "us.anthropic.claude-sonnet-4-6", "us.moonshotai.kimi-k3", "zai.glm-5"
    ]
    assert registry.get("A").inference.temperature == 0
    assert registry.get("B").inference.temperature is None
    assert registry.get("C").inference.temperature == 0
    assert all(registry.get(alias).pricing.verified for alias in "ABC")


def test_pilot_order_and_main_model_call_inventory_are_fixed():
    rows = workflow.call_inventory()
    pilot = [row for row in rows if row["phase"] == "pilot"]
    assert [(row["stage"], row["model_alias"]) for row in pilot] == [
        (stage.value, alias) for stage in workflow.STAGES for alias in "ABC"
    ]
    main = [row for row in rows if row["phase"] != "pilot"]
    assert len(main) == 504
    assert {alias: sum(row["model_alias"] == alias for row in main) for alias in "ABC"} == {
        "A": 184, "B": 144, "C": 176
    }


def test_both_budget_options_are_preserved_and_16384_cap_is_selected():
    plan = workflow.build_plan()
    expected = {
        "4096": (21.961643551483487, 198.648376),
        "16384": (42.81721377191824, 572.437048),
    }
    for option, (realistic, worst) in expected.items():
        budget = plan["budget_options"][option]["combined"]
        assert budget["realistic_estimate"]["total"]["cost_usd"] == pytest.approx(realistic)
        assert budget["static_worst_case"]["total"]["cost_usd"] == pytest.approx(worst)
        assert budget["static_worst_case"]["total"]["api_attempts"] == 513 * 5
    assert plan["selected_budget"] == plan["budget_options"]["16384"]
    assert plan["user_decision"]["hard_budget_cap_usd"] == 100.0


def test_default_is_plan_only_and_paid_flags_refuse_before_client(tmp_path, monkeypatch, capsys):
    assert workflow.main([]) == 0
    assert "PLAN ONLY" in capsys.readouterr().out
    monkeypatch.setattr(workflow, "APPROVAL_MANIFEST", tmp_path / "not-approved.json")
    with pytest.raises(SystemExit, match="no paid-call approval manifest"):
        workflow.main(["--execute-approved-pilot"])
    with pytest.raises(SystemExit, match="no paid-call approval manifest"):
        workflow.main(["--execute-approved-main"])


def test_main_manifest_is_exact_and_verifies_only_at_main_tag(tmp_path, monkeypatch):
    manifest = manifest_builder.build_manifest()
    checked_in = json.loads(workflow.APPROVAL_MANIFEST.read_text())
    assert checked_in == manifest
    assert manifest["status"] == "main_frozen_paid_execution_approved"
    assert manifest["pilot_approved"] is True
    assert manifest["pilot_outcome"]["api_success"] == 9
    assert manifest["pilot_outcome"]["actual_cost_usd"] == 0.449949
    assert manifest["main_approved"] is True
    assert manifest["main_required_tag"] == workflow.MAIN_TAG
    assert manifest["previous_main_tag_retained"] == workflow.PREVIOUS_MAIN_TAG
    assert manifest["previous_main_tags_retained"] == [workflow.MAIN_TAG_V1, workflow.MAIN_TAG_V1_1]
    assert manifest["sandbox_execution"]["immutable_image_id"] == workflow.SANDBOX_IMAGE_ID
    assert manifest["sandbox_execution"]["short_name_fallback"] is False
    assert manifest["amendments"][0]["scientific_protocol_changed"] is False
    assert manifest["amendments"][0]["main_calls_before_amendment"] == 0
    assert manifest["amendments"][1]["user_authorization"]["wording"] == \
        "可以不用我批准，如果是docker的问题你之间重跑就行"
    assert manifest["docker_void_rerun"]["logical_cell_ceiling"] == 5
    assert manifest["docker_void_rerun"]["analysis_resolution"] == \
        "successful_rerun_replaces_void"
    assert manifest["selected_max_tokens"] == 16384
    assert manifest["hard_budget_cap_usd"] == 100.0
    assert next(row for row in manifest["model_parameters"] if row["alias"] == "B")[
        "temperature_field"] == "omitted"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(workflow, "APPROVAL_MANIFEST", path)
    monkeypatch.setattr(workflow, "_current_tags", lambda: {workflow.MAIN_TAG})
    assert workflow.verify_paid_approval("main") == manifest
    monkeypatch.setattr(workflow, "_current_tags", lambda: {workflow.PREVIOUS_MAIN_TAG})
    with pytest.raises(SystemExit, match=workflow.MAIN_TAG):
        workflow.verify_paid_approval("main")


def test_manifest_pre_rerun_evidence_survives_appended_rerun(tmp_path, monkeypatch):
    from src.contracts import WorkflowRunRecord

    baseline = manifest_builder._verify_completed_main_and_docker_voids()
    destination = tmp_path / "main_b.jsonl"
    all_records = [WorkflowRunRecord.model_validate(row)
                   for row in workflow._read_task_records(workflow.WORKFLOW_RECORDS)]
    originals = [row for row in all_records if row.rerun_of is None]
    rerun = next(row for row in all_records if row.rerun_of is not None)
    destination.write_text("".join(row.model_dump_json() + "\n" for row in originals))
    with destination.open("a") as handle:
        handle.write(rerun.model_dump_json() + "\n")
    monkeypatch.setattr(workflow, "WORKFLOW_RECORDS", destination)

    after_append = manifest_builder._verify_completed_main_and_docker_voids()
    assert after_append == baseline


def test_resume_completion_reads_only_exact_task_files(tmp_path, monkeypatch):
    stage = tmp_path / "stage_benchmark" / "main_a.jsonl"
    workflow_records = tmp_path / "workflow_runs" / "main_b.jsonl"
    invocations = tmp_path / "price_matched_workflow" / "invocations.jsonl"
    pilot = tmp_path / "stage_benchmark" / "pilot.jsonl"
    for path in (stage, workflow_records, invocations, pilot):
        path.parent.mkdir(parents=True, exist_ok=True)
    stage.write_text(json.dumps({"run_id": "stage-task"}) + "\n")
    workflow_records.write_text(json.dumps({"run_id": "workflow-task", "repeat_index": 0}) + "\n")
    invocations.write_text(json.dumps({"context": {"run_id": "invocation-only"}}) + "\n")
    pilot.write_text(json.dumps({"run_id": "pilot-only"}) + "\n")
    monkeypatch.setattr(workflow, "STAGE_RECORDS", stage)
    monkeypatch.setattr(workflow, "WORKFLOW_RECORDS", workflow_records)
    completed = workflow._completed_task_run_ids()
    assert completed == {"part_a": {"stage-task"}, "part_b": {"workflow-task"}}
    progress = workflow._task_record_progress()
    assert progress["part_a"]["completed_records"] == 1
    assert progress["part_b"]["completed_records"] == 1
    assert "invocation-only" not in completed["part_a"] | completed["part_b"]
    assert "pilot-only" not in completed["part_a"] | completed["part_b"]


def test_docker_void_selection_is_exact_and_excludes_other_void_causes():
    from src.storage import RunStore

    records = RunStore(workflow.WORKFLOW_EXPERIMENT, root=workflow.RAW_ROOT).load_records()
    plan = workflow.plan_docker_void_reruns(records)
    assert [(row.project_id, row.path_id, row.repeat_index) for row in plan.eligible] == \
        list(workflow.APPROVED_DOCKER_VOID_CELLS)
    assert plan.pending == () and len(plan.completed_reruns) == 5
    original = plan.eligible[0]
    stages = list(original.stages)
    infra_index = next(i for i, stage in enumerate(stages) if stage.status.value == "infra_error")
    stages[infra_index] = stages[infra_index].model_copy(
        update={"failure_detail": "model call failed (api_error): synthetic non-Docker void"})
    non_docker = original.model_copy(
        update={"run_id": "SYNTHETIC_NON_DOCKER_VOID", "stages": stages})
    expanded = workflow.plan_docker_void_reruns([*records, non_docker])
    assert non_docker not in expanded.eligible
    assert len(expanded.eligible) == 5


def test_docker_void_rerun_planning_is_idempotent_and_append_preserves_original(tmp_path):
    from src.storage import RunStore

    records = RunStore(workflow.WORKFLOW_EXPERIMENT, root=workflow.RAW_ROOT).load_records()
    originals = [row for row in records if row.rerun_of is None]
    initial = workflow.plan_docker_void_reruns(originals)
    original = initial.eligible[0]
    rerun = original.model_copy(update={"run_id": "synthetic-rerun-1", "rerun_of": original.run_id})
    resumed = workflow.plan_docker_void_reruns([*originals, rerun])
    assert len(resumed.pending) == 4
    assert [row.rerun_of for row in resumed.completed_reruns] == [original.run_id]

    store = RunStore(original.experiment_id, root=tmp_path)
    store.append(original)
    original_bytes = store.records_path.read_bytes()
    store.append(rerun)
    combined = store.records_path.read_bytes()
    assert combined.startswith(original_bytes)
    assert len(combined.splitlines()) == 2
    loaded = store.load_records()
    assert loaded[0].run_id == original.run_id and loaded[0].rerun_of is None
    assert loaded[1].rerun_of == original.run_id


def test_analysis_uses_nonvoid_rerun_but_retains_void_when_rerun_is_void(tmp_path):
    from src.analysis.io import load_inputs
    from src.analysis.reruns import SUCCESSFUL_RERUN_REPLACES_VOID, resolve_workflow_reruns
    from src.storage import RunStore

    records = RunStore(workflow.WORKFLOW_EXPERIMENT, root=workflow.RAW_ROOT).load_records()
    original = next(row for row in workflow.plan_docker_void_reruns(records).eligible
                    if row.path_id == "A-A-A")
    comparison = next(row for row in records
                      if row.project_id == original.project_id and row.path_id == original.path_id
                      and row.repeat_index == 1 and row.feasibility.outcome != "void_infra")
    successful = comparison.model_copy(update={"run_id": "synthetic-successful-rerun",
                                                "repeat_index": original.repeat_index,
                                                "rerun_of": original.run_id})
    effective, audit = resolve_workflow_reruns([original, successful])
    assert [row.run_id for row in effective] == [successful.run_id]
    assert audit["replacements"][0]["original_run_id"] == original.run_id
    assert audit["original_void_records_retained_in_raw"] == [original.run_id]

    void_again = original.model_copy(update={"run_id": "synthetic-void-rerun",
                                              "rerun_of": original.run_id})
    effective_void, audit_void = resolve_workflow_reruns([original, void_again])
    assert [row.run_id for row in effective_void] == [original.run_id]
    assert audit_void["rerun_voids_not_used_as_replacements"] == [void_again.run_id]

    path = tmp_path / "records.jsonl"
    path.write_text(original.model_dump_json() + "\n" + successful.model_dump_json() + "\n")
    inputs = load_inputs([path], rerun_resolution=SUCCESSFUL_RERUN_REPLACES_VOID)
    assert [row.run_id for row in inputs.store.workflow_runs] == [successful.run_id]
    assert inputs.rerun_resolution["effective_records"] == 1


def test_parameter_failure_is_detected_without_mutating_parameters():
    stage = SimpleNamespace(
        status=SimpleNamespace(value="infra_error"),
        failure_detail="ValidationException: model doesn't support the temperature field",
    )
    invocation = SimpleNamespace(error={"code": "ValidationException"})
    assert workflow._parameter_failure(stage, invocation) is True
    stage.failure_detail = "EndpointConnectionError"
    invocation.error = {"code": "EndpointConnectionError"}
    assert workflow._parameter_failure(stage, invocation) is False


def test_pilot_stops_only_failed_model_and_adds_no_calls(tmp_path, monkeypatch):
    planned = [
        {"run_id": f"run-{stage}-{model}", "project_id": workflow.PILOT_PROJECT,
         "stage": stage, "model": model, "repeat_index": 0}
        for stage in ("cleaning", "analysis", "reporting") for model in "ABC"
    ]

    class FakeExecutor:
        @contextmanager
        def image_lease(self, _image_id):
            yield

    monkeypatch.setattr(workflow, "registry", lambda _max_tokens: object())
    monkeypatch.setattr(workflow, "plan_stage_benchmark", lambda *args, **kwargs: {"planned": planned})
    monkeypatch.setattr(workflow, "_runtime",
                        lambda *args: (FakeExecutor(), object(), "image", object()))
    monkeypatch.setattr(workflow, "RunStore", lambda *args, **kwargs: object())
    executed = []

    def fake_run(_client, _executor, _store, _project, _stage, model, *_args, **_kwargs):
        executed.append(model)
        return SimpleNamespace(run_id=f"executed-{len(executed)}")

    def fake_record(item, record, _client):
        return {"run_id": record.run_id, "project_id": item["project_id"],
                "stage": item["stage"], "model_alias": item["model"],
                "parameter_failure": item["model"] == "B" and item["stage"] == "cleaning",
                "quality_inspected": False}

    monkeypatch.setattr(workflow, "run_stage_benchmark", fake_run)
    monkeypatch.setattr(workflow, "_pilot_record", fake_record)
    monkeypatch.setattr(workflow, "_ledger_state", lambda: {"spent_usd_priced": 0.5})
    monkeypatch.setattr(workflow, "PILOT_SUMMARY", tmp_path / "pilot_summary.json")
    summary = workflow.execute_pilot({"selected_max_tokens": 16384,
                                      "hard_budget_cap_usd": 100.0})
    assert executed == ["A", "B", "C", "A", "C", "A", "C"]
    assert summary["stopped_models_after_parameter_failure"] == ["B"]
    assert summary["automatic_parameter_changes"] == 0
    assert summary["quality_analyzed"] is False
    skipped = [row for row in summary["records"]
               if row.get("stage_status") == "skipped_after_parameter_failure"]
    assert [(row["stage"], row["model_alias"]) for row in skipped] == [
        ("analysis", "B"), ("reporting", "B")]


def test_main_grid_checkpoint_projects_repeats_and_preserves_shared_cap(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.json"
    part_a = tmp_path / "part_a.json"
    ledger.write_text(json.dumps({"spent_usd_priced": 25.0, "calls": 200}))
    part_a.write_text(json.dumps({"ledger_state": {"spent_usd_priced": 5.0, "calls": 40}}))
    monkeypatch.setattr(workflow, "LEDGER", ledger)
    monkeypatch.setattr(workflow, "PART_A_CHECKPOINT", part_a)
    checkpoint = workflow._main_grid_checkpoint(100.0)
    assert checkpoint["status"] == "main_grid_complete_manual_resume_required"
    assert checkpoint["pilot_and_part_a_spend_usd"] == 5.0
    assert checkpoint["main_grid_actual_usd"] == 20.0
    assert checkpoint["projected_total_usd"] > 25.0
    assert checkpoint["projection_within_cap"] is True
    assert checkpoint["repeats_started"] is False
    assert workflow._main_grid_checkpoint(25.0)["projection_within_cap"] is False


def test_pinned_sandbox_availability_run_and_lease_all_use_immutable_id(tmp_path, monkeypatch):
    from src.contracts import ResourceLimits
    from src.workflow import executor as executor_module

    executor = executor_module.DockerExecutor(image=workflow.SANDBOX_IMAGE_ID)
    calls = []

    def fake_docker(*args, **_kwargs):
        calls.append(args)
        if args[0] == "info":
            return SimpleNamespace(returncode=0, stdout="synthetic-version\n", stderr="")
        assert args[:3] == ("image", "inspect", "--format")
        assert args[-1] == workflow.SANDBOX_IMAGE_ID
        return SimpleNamespace(returncode=0, stdout=workflow.SANDBOX_IMAGE_ID + "\n", stderr="")

    monkeypatch.setattr(executor_module.shutil, "which", lambda _binary: "/synthetic/docker")
    monkeypatch.setattr(executor, "_docker", fake_docker)
    assert executor.availability() == (True, workflow.SANDBOX_IMAGE_ID)
    code = tmp_path / "main.py"
    code.write_text("print('ok')")
    out = tmp_path / "out"
    out.mkdir()
    run = executor.build_run_command("run-1", code, {}, out, ResourceLimits())
    lease = executor.build_image_lease_command("lease-1")
    assert run[-2:] == [workflow.SANDBOX_IMAGE_ID, "/sandbox/code/main.py"]
    assert lease[-2:] == [workflow.SANDBOX_IMAGE_ID, "infinity"]
    assert calls[-1][-1] == workflow.SANDBOX_IMAGE_ID


def test_runtime_constructs_executor_with_pinned_verified_image(monkeypatch):
    from src.bedrock import client as client_module
    from src.workflow import executor as executor_module

    class PinnedDocker:
        def __init__(self, image):
            assert image == workflow.SANDBOX_IMAGE_ID
            self.image = image

        def availability(self):
            return True, self.image

    class OfflineClient:
        def __init__(self, *args, **kwargs):
            self.args, self.kwargs = args, kwargs

    monkeypatch.setattr(executor_module, "DockerExecutor", PinnedDocker)
    monkeypatch.setattr(client_module, "BedrockClient", OfflineClient)
    executor, _gate, image_id, _client = workflow._runtime(16384, 100.0)
    assert executor.image == image_id == workflow.SANDBOX_IMAGE_ID


def test_sandbox_failure_is_void_infra_not_model_failure(tmp_path, monkeypatch):
    from src.bedrock import client as client_module
    from src.workflow import executor as executor_module

    class MissingDocker:
        def __init__(self, image):
            assert image == workflow.SANDBOX_IMAGE_ID
            self.image = image

        def availability(self):
            return False, "synthetic image lookup failure"

    def boom(*args, **kwargs):
        raise AssertionError("Bedrock client constructed after failed sandbox preflight")

    events = tmp_path / "events.jsonl"
    monkeypatch.setattr(workflow, "EVENTS", events)
    monkeypatch.setattr(executor_module, "DockerExecutor", MissingDocker)
    monkeypatch.setattr(client_module, "BedrockClient", boom)
    with pytest.raises(SystemExit, match="no short-name fallback is permitted"):
        workflow._runtime(4096, 100)
    reason = (f"required immutable sandbox image {workflow.SANDBOX_IMAGE_ID} failed preflight; "
              "no short-name fallback is permitted: sandbox unavailable: synthetic image lookup failure")
    event = json.loads(events.read_text())
    assert event == {
        "classification": "sandbox_unavailable", "model_calls_made": 0,
        "model_failure": False, "reason": reason,
        "void_infra": True,
    }


def test_analysis_config_and_protocol_hashes_are_new_only():
    config = (workflow.REPO / "configs/analysis_price_matched_workflow_v3.yaml").read_text()
    assert workflow.STAGE_EXPERIMENT in config and workflow.WORKFLOW_EXPERIMENT in config
    assert "expA_stage_v3.jsonl" not in config and "expB_paths_v3.jsonl" not in config
    hashes = workflow.protocol_hashes()
    assert hashes["files"]["docs/PRICE_MATCHED_WORKFLOW_PLAN.md"]
    assert hashes["files"]["experiments/build_price_matched_workflow_main_manifest.py"]
    assert hashes["files"]["results/raw/price_matched_workflow/pilot_summary.json"]
    assert hashes["files"]["results/raw/stage_benchmark/expA_price_matched_workflow_pilot_v3.jsonl"]
    assert hashes["files"]["results/verification/sandbox_verification.json"]
    assert hashes["files"]["src/workflow/executor.py"]
    assert hashes["prompts_v3_tree"] and hashes["projects_tree"]
