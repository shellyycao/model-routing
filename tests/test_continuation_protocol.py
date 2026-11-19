import json
from pathlib import Path

import pytest

from experiments import run_continuations as continuation
from experiments import build_continuation_manifest as manifest_builder
from src.contracts import StageStatus
from src.workflow.stages import StageResult


def test_inventory_and_remaining_call_counts_are_frozen():
    plan = continuation.build_plan()
    assert plan["eligible_cells"] == 40
    assert plan["recovered_stage_counts"] == {
        "original_4096|B|analysis": 9,
        "original_4096|C|analysis": 2,
        "price_matched_16384|C|analysis": 29,
    }
    assert plan["remaining_call_counts"] == {
        "original_4096|A|reporting": 4,
        "original_4096|B|reporting": 5,
        "original_4096|C|reporting": 2,
        "price_matched_16384|A|reporting": 7,
        "price_matched_16384|B|reporting": 7,
        "price_matched_16384|C|reporting": 15,
    }
    assert all([(stage.value, alias) for _, stage, alias in cell.remaining]
               == [("reporting", cell.original.models[2])]
               for cell in continuation.eligible_cells())


def test_budget_uses_five_attempt_static_and_observed_mean_realistic():
    result = continuation.budget(continuation.eligible_cells())
    worst, realistic = result["static_worst_case"], result["realistic_estimate"]
    assert worst["total"]["logical_calls"] == 40
    assert worst["total"]["attempts"] == 200
    assert worst["total"]["input_tokens"] == 2_814_045
    assert worst["total"]["output_tokens"] == 2_600_960
    assert worst["total"]["cost_usd"] == pytest.approx(30.086433)
    assert realistic["total"]["attempts"] == 40
    assert realistic["total"]["cost_usd"] == pytest.approx(1.4092798278317638)
    assert result["proposed_hard_cap_usd"] == 15
    assert result["cap_below_static_worst_case"] is True
    assert realistic["by_group_alias"]["original_4096|B"]["observed_sample_n"] == 17
    assert realistic["by_group_alias"]["price_matched_16384|B"]["observed_sample_n"] == 37


def test_default_main_is_plan_only_and_never_constructs_runtime(monkeypatch, capsys):
    monkeypatch.setattr(continuation, "_runtime",
                        lambda *args, **kwargs: pytest.fail("plan-only mode constructed paid runtime"))
    assert continuation.main([]) == 0
    output = capsys.readouterr().out
    assert "PLAN ONLY" in output
    assert '"eligible_cells": 40' in output
    assert "explicit_paid_approval_present" in output


def test_paid_gate_refuses_missing_manifest(monkeypatch, tmp_path):
    monkeypatch.setattr(continuation, "MANIFEST", tmp_path / "missing.json")
    with pytest.raises(SystemExit, match="no continuation freeze/approval manifest"):
        continuation.verify_frozen_approval()


def test_manifest_freezes_exact_approval_and_verifies_at_required_tag(monkeypatch, tmp_path):
    manifest = manifest_builder.build_manifest()
    assert manifest["status"] == "continuation_frozen_paid_execution_approved"
    assert manifest["approval"] == {
        "question": "花费上限 $15（预计实际约 $1.41），补跑这 40 次，行吗？",
        "wording": "批准了",
        "date": "2026-11-19",
    }
    assert manifest["logical_call_ceiling"] == manifest["complete_record_lines"] == 40
    assert manifest["hard_budget_cap_usd"] == 15
    assert manifest["ledger_path"] == "results/raw/ledgers/continuations.json"
    assert len(manifest["eligible_replay_evidence"]) == 40
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(continuation, "MANIFEST", path)
    monkeypatch.setattr(continuation, "_tags_at_head", lambda: {continuation.TAG})
    assert continuation.verify_frozen_approval() == manifest


def test_handoff_uses_original_code_and_recovered_file_without_validator_details(tmp_path):
    cell = continuation.eligible_cells()[0]
    pkg, size, _ = continuation.build_continuation_handoff(cell, tmp_path / "handoff.json")
    saved = json.loads((tmp_path / "handoff.json").read_text())
    assert size > 0
    assert saved["current_stage"] == "reporting"
    assert saved["completed_stages"] == ["cleaning", "analysis"]
    assert saved["executed_code"]["analysis"] == (continuation.REPO / cell.replay["code_path"]).read_text()
    assert str(continuation.REPO / cell.replay["output_path"]) in saved["source_files"]
    assert saved["validation_status"]["analysis"] == "passed"
    serialized = json.dumps(saved)
    assert "values_within_tolerance" not in serialized
    assert "frozen_validation" not in serialized
    assert "validator_version" not in serialized
    assert pkg.verified_results["analysis"]["findings"]


def test_pending_selection_is_idempotent_by_continued_from():
    cells = continuation.eligible_cells()
    existing = [{"continued_from": cells[0].original.run_id, "run_id": "continuation-existing"}]
    pending = continuation.pending_cells(cells, existing)
    assert len(pending) == 39
    assert cells[0].original.run_id not in {cell.original.run_id for cell in pending}


@pytest.mark.parametrize("status,expected", [
    (StageStatus.PASSED, "complete_for_corrected_view"),
    (StageStatus.FAILED, "complete_for_corrected_view"),
    (StageStatus.INFRA_ERROR, "void_infra"),
])
def test_mock_execution_labels_infrastructure_without_model_blame(monkeypatch, tmp_path, status, expected):
    cell = continuation.eligible_cells()[0]
    source = cell.original.stages[2]
    record = source.model_copy(update={"status": status, "failure_type": None,
                                       "failure_detail": None, "invocation_ids": ["mock"]})
    monkeypatch.setattr(continuation, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(continuation, "run_reporting",
                        lambda *args, **kwargs: StageResult(record=record, artifacts=None))
    result = continuation.execute_cell(cell, client=object())
    assert result["outcome"] == expected
    assert result["continued_from"] == cell.original.run_id
    assert result["frozen_original_modified"] is False

