"""Offline/mock tests for the approved price-matched compatibility re-pilot."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from experiments import run_price_matched_v2_pilot as pilot


class FakeClient:
    def __init__(self, fail_parameter_model: str | None = None):
        self.fail_parameter_model = fail_parameter_model
        self.calls = []
        self.failed = set()

    @staticmethod
    def parameters(model: str) -> dict:
        result = {"maxTokens": 16384}
        if model != "kimi_k3":
            result["temperature"] = 0.0
        return result

    def converse_structured(self, model, prompt, schema, **kwargs):
        self.calls.append((model, kwargs))
        parameters = self.parameters(model)
        if model == self.fail_parameter_model and model not in self.failed:
            self.failed.add(model)
            error = RuntimeError("inference parameter is unsupported")
            error.record = SimpleNamespace(
                error={"code": "ValidationException", "message": "inference parameter is unsupported"},
                input_tokens=None,
                output_tokens=None,
                inference_settings=parameters,
                stop_reason=None,
                latency_ms=4.0,
                incurred_cost_usd=0.0,
                invocation_id="failed-invocation",
            )
            raise error
        record = SimpleNamespace(
            input_tokens=100,
            output_tokens=20,
            inference_settings=parameters,
            stop_reason="end_turn",
            latency_ms=12.5,
            incurred_cost_usd=0.001,
            invocation_id=f"inv-{len(self.calls)}",
        )
        result = SimpleNamespace(
            record=record,
            raw_response={
                "usage": {
                    "inputTokens": 100,
                    "outputTokens": 20,
                    "outputTokenDetails": {"reasoningTokens": 5},
                },
                "stopReason": "end_turn",
            },
            text='{"ok": true}',
        )
        return SimpleNamespace(result=result, parsed=object(), parse_error=None)


def factory_for(client, captured):
    def factory(limits, ledger, log):
        captured.update(limits=limits, ledger=ledger, log=log)
        return client
    return factory


def test_default_entry_point_is_plan_only(monkeypatch, capsys):
    called = False

    def forbidden():
        nonlocal called
        called = True
        raise AssertionError("paid path should not run")

    monkeypatch.setattr(pilot, "execute_repilot", forbidden)
    assert pilot.main([]) == 0
    assert called is False
    assert "PLAN/AUDIT ONLY" in capsys.readouterr().out


def test_completed_repilot_flag_is_no_longer_an_execution_option(monkeypatch):
    called = False

    def fake_execute():
        nonlocal called
        called = True
        return {"status": "mocked"}

    monkeypatch.setattr(pilot, "execute_repilot", fake_execute)
    with pytest.raises(SystemExit):
        pilot.main(["--execute-approved-repilot"])
    assert called is False


def test_old_pilot_flag_is_not_an_execution_option():
    with pytest.raises(SystemExit):
        pilot.main(["--execute-approved-pilot"])


def test_plans_preserve_initial_nine_and_allow_only_six_repilot_calls():
    historical = pilot.plan()
    assert historical["logical_call_cap"] == 9
    assert [(row["task"], row["model_alias"]) for row in historical["calls"]] == [
        (task, model)
        for task in ("a1", "a2", "a3")
        for model in ("sonnet_4_6", "kimi_k3", "grok_4_7")
    ]

    planned = pilot.repilot_plan()
    assert planned["status"] == "executed_2026-11-18_6_of_6_success"
    assert planned["logical_call_cap"] == 6
    assert [(row["task"], row["model_alias"]) for row in planned["calls"]] == [
        (task, model)
        for task in ("a1", "a2", "a3")
        for model in ("kimi_k3", "glm_5")
    ]
    assert len({row["run_id"] for row in planned["calls"]}) == 6
    assert all(row["temperature"] is None for row in planned["calls"] if row["model_alias"] == "kimi_k3")
    assert all(row["temperature"] == 0 for row in planned["calls"] if row["model_alias"] == "glm_5")
    assert planned["retry_policy"] == {
        "source": "BedrockClient default",
        "max_attempts": 5,
        "parameter_errors_retryable": False,
    }


def test_repilot_uses_shared_15_cap_and_records_model_specific_parameters(tmp_path):
    client, captured = FakeClient(), {}
    shared_ledger = tmp_path / "shared-ledger.json"
    summary = pilot.execute_repilot(
        client_factory=factory_for(client, captured),
        output_dir=tmp_path / "pilot",
        ledger_path=shared_ledger,
    )
    assert captured["limits"].max_budget_usd == 15.0
    assert captured["limits"].max_calls == 15 * 5
    assert captured["ledger"] == shared_ledger
    assert len(client.calls) == 6
    assert summary["status"] == "complete" and summary["successes"] == 6
    rows = pilot._read_jsonl(tmp_path / "pilot/repilot_records.jsonl")
    assert len(rows) == 6
    assert all(row["raw_usage"]["outputTokens"] == 20 for row in rows)
    assert all(row["reasoning_tokens"] == 5 for row in rows)
    assert all(row["effective_parameters"] == {"maxTokens": 16384} for row in rows if row["model_alias"] == "kimi_k3")
    assert all(row["effective_parameters"] == {"maxTokens": 16384, "temperature": 0.0} for row in rows if row["model_alias"] == "glm_5")
    assert all(row["stopReason"] == "end_turn" and row["schema_parsed"] for row in rows)
    assert all(row["latency_ms"] == 12.5 and row["cost_usd"] == 0.001 for row in rows)
    assert all(row["quality_inspected"] is False for row in rows)


def test_parameter_failure_stops_only_that_model_without_fallback(tmp_path):
    client, captured = FakeClient(fail_parameter_model="glm_5"), {}
    summary = pilot.execute_repilot(
        client_factory=factory_for(client, captured),
        output_dir=tmp_path / "pilot",
        ledger_path=tmp_path / "ledger.json",
    )
    assert len(client.calls) == 4  # GLM attempted once; its remaining two slots are skipped.
    assert [model for model, _ in client.calls].count("glm_5") == 1
    assert summary["errors"] == 1
    assert summary["skipped_after_parameter_failure"] == 2
    assert set(summary["blocked_models"]) == {"glm_5"}
    rows = pilot._read_jsonl(tmp_path / "pilot/repilot_records.jsonl")
    glm = [row for row in rows if row["model_alias"] == "glm_5"]
    assert [row["status"] for row in glm] == [
        "parameter_error", "skipped_model_parameter_failure", "skipped_model_parameter_failure"
    ]
    assert all(row["effective_parameters"] == {"maxTokens": 16384, "temperature": 0.0} for row in glm)


def test_resume_never_repeats_recorded_slots(tmp_path):
    client, captured = FakeClient(), {}
    kwargs = {
        "client_factory": factory_for(client, captured),
        "output_dir": tmp_path / "pilot",
        "ledger_path": tmp_path / "ledger.json",
    }
    pilot.execute_repilot(**kwargs)
    second = pilot.execute_repilot(**kwargs)
    assert len(client.calls) == 6
    assert second["logical_calls_attempted_this_run"] == 0


def test_repilot_does_not_modify_initial_record_file(tmp_path):
    output = tmp_path / "pilot"
    output.mkdir()
    initial = output / "records.jsonl"
    initial.write_text('{"immutable":"initial"}\n')
    pilot.execute_repilot(
        client_factory=factory_for(FakeClient(), {}),
        output_dir=output,
        ledger_path=tmp_path / "ledger.json",
    )
    assert initial.read_text() == '{"immutable":"initial"}\n'
    assert (output / "repilot_records.jsonl").exists()


def test_orphaned_repilot_invocation_refuses_possible_duplicate(tmp_path):
    output = tmp_path / "pilot"
    output.mkdir()
    (output / "repilot_invocations.jsonl").write_text(
        '{"status":"success","context":{"run_id":"orphan"}}\n'
    )
    with pytest.raises(RuntimeError, match="unreconciled"):
        pilot.execute_repilot(
            client_factory=factory_for(FakeClient(), {}),
            output_dir=output,
            ledger_path=tmp_path / "ledger.json",
        )
