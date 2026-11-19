"""Offline tests for the price-matched-v2 protocol and cost analysis."""

from __future__ import annotations

import json

import pytest

from experiments import run_price_matched_v2 as runner
from experiments.analyze_price_matched_v2 import analyze
from experiments.build_price_matched_v2_protocol import OUT as MANIFEST_OUT, build_manifest
from experiments.verify_price_matched_models import OUT as VERIFICATION_OUT, build_verification


def test_final_models_have_exact_regional_prices_and_real_invoke_access():
    result = build_verification()
    assert result == json.loads(VERIFICATION_OUT.read_text())
    assert [row["callable_model_id"] for row in result["models"]] == [
        "us.anthropic.claude-sonnet-4-6",
        "us.moonshotai.kimi-k3",
        "zai.glm-5",
    ]
    assert [(row["input_per_mtok"], row["output_per_mtok"]) for row in result["models"]] == [
        (3.3, 16.5), (3.3, 16.5), (1.0, 3.2)
    ]
    assert all(
        row["verified"]
        and all(row["control_plane_access_checks"].values())
        and row["invoke_access"]["access_eligible"]
        and row["invoke_access"]["compatibility_verified"]
        for row in result["models"]
    )
    assert result["removed_models"][0]["alias"] == "grok_4_7"
    assert result["removed_models"][0]["invoke_evidence"]["access_denied_calls"] == 3
    for model in result["models"]:
        for rows in model["price_evidence"].values():
            for row in rows:
                text = f"{row['usage_type']} {row['service_tier']}".casefold()
                assert not any(word in text for word in ("global", "batch", "cache", "priority", "flex"))


def test_runner_has_810_repeat_major_interleaved_calls():
    rows = runner.plan_rows()
    assert len(rows) == 810
    assert [row["repeat"] for row in rows[:270]] == [0] * 270
    assert [row["repeat"] for row in rows[270:540]] == [1] * 270
    assert [row["repeat"] for row in rows[540:]] == [2] * 270
    assert [row["model"] for row in rows[:6]] == [
        "sonnet_4_6", "kimi_k3", "glm_5", "sonnet_4_6", "kimi_k3", "glm_5"
    ]
    assert len({row["run_id"] for row in rows}) == 810
    plan = runner.build_plan()
    assert plan["evaluation"]["calls_per_repeat"] == 270
    assert plan["evaluation"]["cost_checkpoint_after_repeat_1"] is True


def test_historical_pilot_is_immutable_and_repilot_is_exactly_six_calls():
    calls = runner.initial_pilot_calls()
    benchmark_ids = {
        case["case_id"] for task in ("a1", "a2", "a3") for case in runner.load_cases(task)
    }
    assert len(calls) == 9
    assert all(call["status"] == "completed_or_skipped_as_recorded" and call["quality_review_forbidden"] for call in calls)
    assert all(call["synthetic_case_id"] not in benchmark_ids for call in calls)
    assert {call["task"] for call in calls} == {"a1", "a2", "a3"}
    assert all(call["maxTokens"] == 16_384 and call["temperature"] == 0 for call in calls)
    repilot = runner.repilot_calls()
    assert [(row["task"], row["model_alias"]) for row in repilot] == [
        (task, alias)
        for task in ("a1", "a2", "a3")
        for alias in ("kimi_k3", "glm_5")
    ]
    assert all(row["temperature"] is None for row in repilot if row["model_alias"] == "kimi_k3")
    assert all(row["temperature"] == 0 for row in repilot if row["model_alias"] == "glm_5")
    assert all(row["status"] == "completed_success_as_recorded" for row in repilot)


def test_registry_omits_temperature_only_for_kimi():
    registry = runner._registry()
    assert registry.get("kimi_k3").inference.temperature is None
    assert registry.get("sonnet_4_6").inference.temperature == 0
    assert registry.get("glm_5").inference.temperature == 0


def test_budget_reports_static_and_realistic_views_with_runtime_cap():
    # The machine plan is the frozen pre-main budget artifact. build_plan() also
    # exposes live ledger state and therefore changes after paid execution starts.
    budget = json.loads(runner.PLAN_OUT.read_text())["budget"]
    assert budget["static_worst_case"]["maximum_api_attempts"] == 13 + 810 * 5
    assert budget["static_worst_case"]["sunk_pilot_actual_priced_usd"] == pytest.approx(0.671384)
    assert budget["static_worst_case"]["total_usd"] == pytest.approx(841.39187)
    assert budget["realistic_estimate"]["total_usd"] == pytest.approx(24.2449148)
    assert budget["hard_cap_usd"] == 100
    assert budget["runtime_enforcement"]["reserve_then_settle"] is True
    assert budget["runtime_enforcement"]["cost_checkpoint_after_repeat"] == 1


def test_paid_path_refuses_before_client_without_future_freeze_tag(monkeypatch, capsys):
    monkeypatch.setattr(runner, "_current_tags", lambda: set())
    with pytest.raises(SystemExit, match="paid execution requires HEAD"):
        runner.main(["--execute"])


def test_completed_reads_only_task_records_when_invocation_log_exists(tmp_path, monkeypatch):
    raw = tmp_path / "price_matched_v2"
    raw.mkdir()
    (raw / "invocations.jsonl").write_text(
        '{"context":{"run_id":"nested-invocation-id"},"status":"success"}\n'
    )
    (raw / "price_matched_v2_a1.jsonl").write_text(
        '{"run_id":"completed-a1"}\n'
    )
    (raw / "price_matched_v2_a2.jsonl").write_text(
        '{"run_id":"completed-a2"}\n'
    )
    monkeypatch.setattr(runner, "RAW", raw)
    assert runner._completed() == {"completed-a1", "completed-a2"}


def test_frozen_protocol_verifies_when_exact_tag_is_present(monkeypatch):
    monkeypatch.setattr(runner, "_current_tags", lambda: {runner.FUTURE_TAG})
    manifest = runner.verify_frozen_protocol()
    assert manifest["status"] == "protocol_frozen_paid_execution_approved"
    assert manifest["user_approval"]["wording"] == "Approve main run"
    assert manifest["hard_cap_usd"] == 100


def test_old_freeze_tag_alone_is_rejected_after_resume_amendment(monkeypatch):
    monkeypatch.setattr(runner, "_current_tags", lambda: {"price-matched-v2-frozen-v1"})
    with pytest.raises(SystemExit, match="price-matched-v2-frozen-v1.1"):
        runner.verify_frozen_protocol()


def test_reasoning_token_usage_extraction_is_additive_and_optional():
    assert runner.reasoning_tokens_from_usage({"reasoningTokens": 12, "outputTokens": 20}) == 12
    assert runner.reasoning_tokens_from_usage({
        "outputTokens": 20, "outputTokenDetails": {"reasoningTokens": 7}
    }) == 7
    assert runner.reasoning_tokens_from_usage({"outputTokens": 20}) is None


def _record(alias, task, *, quality, success, inp, out, reasoning=None, ranking_valid=None):
    metric = {"a1": "functional_correct", "a2": "content_correct", "a3": "ndcg_at_5"}[task]
    return {
        "model_alias": alias,
        "task": task,
        "input_tokens": inp,
        "output_tokens": out,
        "reasoning_tokens": reasoning,
        "scores": {
            metric: quality,
            "operational_success": success,
            **({"ranking_valid": ranking_valid} if ranking_valid is not None else {}),
        },
        "generation_ms": 100,
        "truncated": False,
        "parse_ok": True,
    }


def test_cost_metrics_and_pareto_frontier_are_token_based():
    prices = {
        "quality": {"input_per_mtok": 1.0, "output_per_mtok": 10.0},
        "cheap": {"input_per_mtok": 1.0, "output_per_mtok": 10.0},
        "dominated": {"input_per_mtok": 1.0, "output_per_mtok": 10.0},
    }
    records = [
        _record("quality", "a1", quality=1, success=True, inp=1000, out=100, reasoning=20),
        _record("cheap", "a1", quality=0, success=False, inp=500, out=50),
        _record("dominated", "a1", quality=0.5, success=True, inp=2000, out=200),
    ]
    result = analyze(records, prices)
    cells = {row["model_alias"]: row for row in result["cells"]}
    assert cells["quality"]["actual_cost_usd"] == pytest.approx(0.002)
    assert cells["quality"]["primary_success_metric"] == "functional_correct"
    assert cells["quality"]["cost_per_primary_success_usd"] == pytest.approx(0.002)
    assert cells["cheap"]["cost_per_primary_success_usd"] is None
    assert cells["quality"]["reasoning_tokens_reported"] == 20
    assert result["pareto_frontier_by_task"]["a1"]["model_aliases"] == ["cheap", "quality"]


def test_a3_cost_uses_valid_responses_and_strict_ndcg_points():
    prices = {"m": {"input_per_mtok": 1.0, "output_per_mtok": 10.0}}
    records = [
        _record("m", "a3", quality=0.5, success=True, ranking_valid=True, inp=1000, out=100),
        _record("m", "a3", quality=0.0, success=False, ranking_valid=False, inp=500, out=50),
    ]
    cell = analyze(records, prices)["cells"][0]
    assert cell["actual_cost_usd"] == pytest.approx(0.003)
    assert cell["valid_responses"] == 1
    assert cell["cost_per_valid_response_usd"] == pytest.approx(0.003)
    assert cell["strict_ndcg_points"] == pytest.approx(0.5)
    assert cell["cost_per_strict_ndcg_point_usd"] == pytest.approx(0.006)
    assert cell["cost_per_operational_success_usd_secondary"] == pytest.approx(0.003)


def test_a2_cost_uses_content_correct_not_operational_success():
    prices = {"m": {"input_per_mtok": 1.0, "output_per_mtok": 10.0}}
    record = _record("m", "a2", quality=1, success=False, inp=1000, out=100)
    cell = analyze([record], prices)["cells"][0]
    assert cell["primary_success_metric"] == "content_correct"
    assert cell["primary_successes"] == 1
    assert cell["cost_per_primary_success_usd"] == pytest.approx(0.002)
    assert cell["cost_per_operational_success_usd_secondary"] is None


def test_a3_pareto_quality_axis_ignores_secondary_deduplicated_score():
    prices = {
        "invalid": {"input_per_mtok": 1.0, "output_per_mtok": 10.0},
        "valid": {"input_per_mtok": 1.0, "output_per_mtok": 10.0},
    }
    invalid = _record(
        "invalid", "a3", quality=0, success=False, ranking_valid=False, inp=500, out=50
    )
    invalid["scores"]["deduplicated_ndcg_at_5"] = 1.0
    valid = _record(
        "valid", "a3", quality=0.5, success=True, ranking_valid=True, inp=1000, out=100
    )
    result = analyze([invalid, valid], prices)
    cells = {row["model_alias"]: row for row in result["cells"]}
    assert cells["invalid"]["quality_mean"] == 0
    assert result["pareto_frontier_by_task"]["a3"]["quality_axis"] == "ndcg_at_5"
    assert result["pareto_frontier_by_task"]["a3"]["model_aliases"] == ["invalid", "valid"]


def test_reasoning_tokens_must_be_within_billed_output_tokens():
    bad = _record("m", "a3", quality=1, success=True, inp=1, out=4, reasoning=5)
    with pytest.raises(ValueError, match="reasoning_tokens"):
        analyze([bad], {"m": {"input_per_mtok": 1, "output_per_mtok": 1}})


def test_cp3e_manifest_is_reproducible_frozen_and_paid_approved():
    rebuilt = build_manifest()
    assert rebuilt == json.loads(MANIFEST_OUT.read_text())
    assert rebuilt["status"] == "protocol_frozen_paid_execution_approved"
    assert rebuilt["freeze_tag_created"] is False
    assert rebuilt["network_requests_made_by_freeze_build"] == 0
    assert rebuilt["user_approval"]["wording"] == "Approve main run"
    assert rebuilt["compatibility_pilot_executed"] is True
    assert rebuilt["compatibility_pilot_approved"] is True
    assert rebuilt["compatibility_pilot_hard_cap_usd"] == 15
    assert rebuilt["compatibility_pilot_uses_shared_100_usd_ledger"] is True
    assert rebuilt["compatibility_repilot_approved"] is True
    assert rebuilt["compatibility_repilot_executed"] is True
    assert rebuilt["compatibility_repilot_max_calls"] == 6
    assert rebuilt["compatibility_repilot_successes"] == 6
    assert rebuilt["compatibility_repilot_schema_parses"] == 6
    assert rebuilt["evaluation_logical_calls"] == 810
    assert rebuilt["hard_cap_usd"] == 100
    assert rebuilt["required_tag"] == "price-matched-v2-frozen-v1.1"
    assert rebuilt["previous_tag_retained"] == "price-matched-v2-frozen-v1"
    assert rebuilt["amendments"][0]["scientific_protocol_changed"] is False
    assert rebuilt["amendments"][0]["timing"].startswith("before any")
    assert rebuilt["repeat1_execution_state"]["logical_calls"] == 270
    assert rebuilt["repeat1_execution_state"]["resume_crash_ledger_calls"] == 283
    assert rebuilt["pre_main_ledger_state"]["calls"] == 13
    assert rebuilt["pre_main_ledger_state"]["spent_usd_priced"] == pytest.approx(0.671384)
    assert rebuilt["hashes"] == runner.protocol_hashes()
