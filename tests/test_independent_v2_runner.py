"""Offline safety and planning tests for the prospective Independent-v2 runner."""

from __future__ import annotations

import json

import pytest

from experiments import run_independent_v2_benchmark as runner


def test_v2_plan_has_frozen_scope_and_token_caps(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "RAW", tmp_path)
    planned = runner.plan()
    assert planned["planned_logical_calls"] == 270
    assert planned["by_task"] == {"a1": 90, "a2": 90, "a3": 90}
    assert planned["worst_case_output_tokens"] == 1_474_560
    assert planned["maximum_api_attempts_with_five_attempt_retry_policy"] == 1350
    assert planned["estimated_input_tokens"] <= runner.MAX_INPUT_TOKENS
    assert len({run_id for *_, run_id in planned["runs"]}) == 270


@pytest.mark.parametrize("task", ["a1", "a2", "a3"])
def test_v2_prompts_render_without_placeholders(task):
    prompt = runner.render(task, runner.load_cases(task)[0])
    assert "{{" not in prompt
    assert prompt.strip()


def test_paid_execution_requires_exact_frozen_tag(monkeypatch):
    monkeypatch.setattr(runner, "_current_tags", lambda: set())
    with pytest.raises(SystemExit, match="exact tag independent-v2-frozen-v1.1"):
        runner.verify_frozen_protocol()


def test_paid_cli_requires_dollar_guard(capsys):
    with pytest.raises(SystemExit, match="max-budget-usd"):
        runner.main([
            "--execute",
            "--max-api-attempts", "1350",
            "--max-input-tokens", "500000",
            "--max-output-tokens", "1474560",
        ])


def test_freeze_hash_verifier_detects_changes(monkeypatch, tmp_path):
    manifest = runner._expected_freeze_values()
    manifest["runner_sha256"] = "wrong"
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(runner, "FREEZE_MANIFEST", path)
    monkeypatch.setattr(runner, "_current_tags", lambda: {runner.FROZEN_TAG})
    with pytest.raises(SystemExit, match="hash mismatch"):
        runner.verify_frozen_protocol()


def test_plan_cli_never_creates_aws_client(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(runner, "RAW", tmp_path)
    assert runner.main(["--plan"]) == 0
    output = capsys.readouterr().out
    assert "PLAN ONLY" in output
    assert '"planned_logical_calls": 270' in output
