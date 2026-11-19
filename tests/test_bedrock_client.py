"""Offline unit tests for the Bedrock client (no AWS calls)."""

from __future__ import annotations

import pytest
from botocore.exceptions import ClientError
from pydantic import BaseModel

from src.bedrock.client import BedrockClient, ModelInvocationError, RetryPolicy
from src.bedrock.models import load_registry, Pricing
from src.bedrock.structured import StructuredOutputError, parse_structured
from src.bedrock.usage import InvocationContext, UsageLimits, estimate_cost


def ok_response(text="OK", reasoning=None, inp=10, out=5):
    content = []
    if reasoning is not None:
        content.append({"reasoningContent": {"reasoningText": {"text": reasoning}}})
    content.append({"text": text})
    return {
        "output": {"message": {"role": "assistant", "content": content}},
        "usage": {"inputTokens": inp, "outputTokens": out, "totalTokens": inp + out},
        "metrics": {"latencyMs": 123},
        "stopReason": "end_turn",
    }


# SYNTHETIC_FIXTURE: fake prices for tests only; not real Bedrock prices.
def fake_price(inp=3.0, out=15.0):
    return Pricing(input_per_mtok=inp, output_per_mtok=out, source="SYNTHETIC_FIXTURE", retrieved="2026-01-01")


def client_error(code, msg="boom"):
    return ClientError({"Error": {"Code": code, "Message": msg}}, "Converse")


class FakeRuntime:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture
def registry():
    return load_registry()


def make_client(tmp_path, registry, script, **kw):
    rt = FakeRuntime(script)
    c = BedrockClient(
        registry,
        runtime_client=rt,
        log_path=tmp_path / "inv.jsonl",
        ledger_path=tmp_path / "ledger.json",
        cache_dir=tmp_path / "cache",
        retry=RetryPolicy(max_attempts=3, base_delay_s=0.01),
        sleep=lambda s: None,
        **kw,
    )
    return c, rt


def test_registry_has_three_distinct_families(registry):
    fams = {m.family for m in registry.models.values()}
    assert registry.aliases == ["A", "B", "C"]
    assert len(fams) == 3


def test_success_logs_record_and_uses_requested_model(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [ok_response("hello")])
    ctx = InvocationContext(experiment_id="e1", project_id="p1", path_id="AAB", stage_id="cleaning")
    res = c.converse("B", "hi", context=ctx)
    assert res.text == "hello"
    assert rt.calls[0]["modelId"] == registry.get("B").model_id
    recs = c.logger.read_all()
    assert len(recs) == 1
    r = recs[0]
    assert r.status == "success" and r.input_tokens == 10 and r.output_tokens == 5
    assert r.context.path_id == "AAB" and r.server_latency_ms == 123
    assert r.inference_settings == {"maxTokens": 4096, "temperature": 0.0}


def test_reasoning_separated_from_text(tmp_path, registry):
    c, _ = make_client(tmp_path, registry, [ok_response("OK", reasoning="thinking...")])
    res = c.converse("C", "hi")
    assert res.text == "OK" and res.reasoning == "thinking..."
    assert res.record.reasoning_chars == len("thinking...")


def test_throttling_is_retried_then_succeeds(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [client_error("ThrottlingException"), ok_response()])
    res = c.converse("A", "hi")
    assert res.record.retry_count == 1 and len(rt.calls) == 2


def test_retries_are_bounded(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [client_error("ThrottlingException")] * 3)
    with pytest.raises(ModelInvocationError) as ei:
        c.converse("A", "hi")
    assert len(rt.calls) == 3
    assert ei.value.record.status == "throttled_exhausted"
    assert c.logger.read_all()[-1].status == "throttled_exhausted"


def test_non_retryable_error_fails_fast_without_substitution(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [client_error("AccessDeniedException")])
    with pytest.raises(ModelInvocationError) as ei:
        c.converse("A", "hi")
    assert len(rt.calls) == 1  # no retry, no fallback model
    assert {call["modelId"] for call in rt.calls} == {registry.get("A").model_id}
    assert ei.value.record.status == "api_error"
    assert ei.value.record.error["code"] == "AccessDeniedException"


def test_unverified_pricing_reports_unavailable_not_zero(tmp_path, registry):
    for alias in registry.aliases:
        registry.models[alias].pricing = Pricing()
    c, _ = make_client(tmp_path, registry, [ok_response()], limits=UsageLimits(max_budget_usd=1.0))
    res = c.converse("A", "hi")
    assert res.record.cost_usd is None and res.record.cost_status == "unavailable"
    assert c.costs.unpriced_calls == 1 and c.costs.spent_usd_priced == 0
    assert c.costs.dollar_guard_active is False  # never reported as functional with unknown prices
    assert c.costs.input_tokens == 10 and c.costs.output_tokens == 5  # tokens still counted


def test_call_limit_enforced_without_prices(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [ok_response(), ok_response()], limits=UsageLimits(max_calls=1))
    c.converse("A", "one")
    with pytest.raises(ModelInvocationError) as ei:
        c.converse("A", "two")
    assert ei.value.record.status == "budget_refused" and len(rt.calls) == 1


def test_output_token_limit_enforced_without_prices(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [ok_response()], limits=UsageLimits(max_output_tokens=1000))
    with pytest.raises(ModelInvocationError):
        c.converse("A", "hi")  # default maxTokens 4096 > 1000 worst case
    assert len(rt.calls) == 0
    c.converse("A", "hi", max_tokens=500)
    assert len(rt.calls) == 1


def test_dollar_limit_enforced_when_priced(tmp_path, registry):
    for alias in registry.aliases:  # guard reports active only when every model is priced
        registry.models[alias].pricing = fake_price()
    assert estimate_cost(registry.models["A"].pricing, 1_000_000, 1_000_000) == pytest.approx(18.0)
    c, rt = make_client(tmp_path, registry, [ok_response(inp=1000, out=1000)],
                        limits=UsageLimits(max_budget_usd=0.05))
    res = c.converse("A", "hi", max_tokens=100)
    assert res.record.cost_usd == pytest.approx(0.018)
    assert c.costs.dollar_guard_active is True
    with pytest.raises(ModelInvocationError) as ei:
        c.converse("A", "another prompt")  # worst case 4096*$15/M = $0.061 > remaining
    assert ei.value.record.status == "budget_refused"
    assert len(rt.calls) == 1


def test_ledger_persists_across_clients(tmp_path, registry):
    registry.models["A"].pricing = fake_price()
    c, _ = make_client(tmp_path, registry, [ok_response(inp=1000, out=1000)])
    c.converse("A", "hi", max_tokens=10)
    c2, _ = make_client(tmp_path, registry, [])
    assert c2.costs.spent_usd_priced == pytest.approx(0.018) and c2.costs.calls == 1


def test_repeats_bypass_cache(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [ok_response("r0"), ok_response("r1")])
    for i in range(2):
        c.converse("A", "same", use_cache=False, context=InvocationContext(repeat_index=i))
    assert len(rt.calls) == 2
    recs = c.logger.read_all()
    assert [r.context.repeat_index for r in recs] == [0, 1] and not any(r.from_cache for r in recs)


def test_cache_prevents_repeat_paid_call(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [ok_response("first")])
    c.converse("A", "same prompt")
    res2 = c.converse("A", "same prompt")
    assert len(rt.calls) == 1
    assert res2.text == "first" and res2.record.from_cache and res2.record.cost_status == "not_incurred"
    assert res2.record.cached_from == c.logger.read_all()[0].invocation_id


def test_cache_key_distinguishes_models_and_prompts(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [ok_response("a"), ok_response("b"), ok_response("c")])
    c.converse("A", "p1")
    c.converse("B", "p1")
    c.converse("A", "p2")
    assert len(rt.calls) == 3


class Demo(BaseModel):
    code: str
    filename: str


def test_parse_structured_fenced_and_bare():
    assert parse_structured('Sure:\n```json\n{"code": "x", "filename": "a.csv"}\n```', Demo).filename == "a.csv"
    assert parse_structured('{"code": "x", "filename": "b.csv"}', Demo).filename == "b.csv"


@pytest.mark.parametrize("text,kind", [
    ("no json here", "no_json"),
    ("```json\n{bad json}\n```", "invalid_json"),
    ('```json\n{"code": "x"}\n```', "schema_mismatch"),
])
def test_parse_structured_failures(text, kind):
    with pytest.raises(StructuredOutputError) as ei:
        parse_structured(text, Demo)
    assert ei.value.kind == kind


def test_structured_parse_failure_is_returned_not_repaired(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [ok_response("I refuse to output JSON")])
    sr = c.converse_structured("B", "give json", Demo)
    assert sr.parsed is None and sr.parse_error.kind == "no_json"
    assert len(rt.calls) == 1  # no automatic re-prompt
    statuses = [r.status for r in c.logger.read_all()]
    assert statuses == ["success", "parse_error"]


# ---------------------------------------------------------------- truncation (task 5)
def truncated_response(text, inp=10, out=4096):
    r = ok_response(text, inp=inp, out=out)
    r["stopReason"] = "max_tokens"
    return r


def test_truncation_flagged_on_record(tmp_path, registry):
    c, _ = make_client(tmp_path, registry, [truncated_response("partial"), ok_response("full")])
    r1 = c.converse("A", "long", use_cache=False)
    r2 = c.converse("A", "short", use_cache=False)
    assert r1.truncated and r1.record.truncated and r1.record.stop_reason == "max_tokens"
    assert not r2.truncated
    assert [r.truncated for r in c.logger.read_all()] == [True, False]


def test_truncated_parse_failure_distinguishable_in_log(tmp_path, registry):
    c, _ = make_client(tmp_path, registry, [
        truncated_response('```json\n{"code": "x", "filen'),   # cut off mid-JSON
        ok_response("I refuse"),                                 # genuine format failure
    ])
    s1 = c.converse_structured("C", "give json", Demo, use_cache=False)
    s2 = c.converse_structured("C", "give json again", Demo, use_cache=False)
    assert s1.truncated and not s2.truncated
    events = [r for r in c.logger.read_all() if r.status == "parse_error"]
    assert [e.error["cause"] for e in events] == ["truncated_max_tokens", "model_output"]
    assert [e.truncated for e in events] == [True, False]


def test_truncation_preserved_on_cache_hit(tmp_path, registry):
    c, _ = make_client(tmp_path, registry, [truncated_response("partial")])
    c.converse("A", "long")
    assert c.converse("A", "long").record.truncated


# ------------------------------------------------- reviewer findings (B2, M1-M5, minor)
def test_B2_repeat_with_cache_raises(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [ok_response()])
    with pytest.raises(ValueError, match="use_cache=False"):
        c.converse("A", "x", context=InvocationContext(repeat_index=0))
    assert rt.calls == [] and c.logger.read_all() == []


def test_B2_cache_is_namespaced_per_experiment(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [ok_response("e1"), ok_response("e2")])
    c.converse("A", "same", context=InvocationContext(experiment_id="exp1"))
    r2 = c.converse("A", "same", context=InvocationContext(experiment_id="exp2"))
    assert len(rt.calls) == 2 and not r2.record.from_cache
    r3 = c.converse("A", "same", context=InvocationContext(experiment_id="exp1"))
    assert r3.record.from_cache and r3.text == "e1" and r3.record.cache_namespace == "exp1"
    # An explicit shared namespace reuses across experiments.
    r4 = c.converse("A", "same", context=InvocationContext(experiment_id="exp3"), cache_namespace="exp1")
    assert r4.record.from_cache and len(rt.calls) == 2


def test_M1_unexpected_client_exception_is_logged(tmp_path, registry):
    from botocore.exceptions import ParamValidationError
    c, rt = make_client(tmp_path, registry, [ParamValidationError(report="bad param")])
    with pytest.raises(ModelInvocationError) as ei:
        c.converse("A", "hi")
    assert isinstance(ei.value.__cause__, ParamValidationError)
    rec = c.logger.read_all()[-1]
    assert rec.status == "client_error" and rec.error["code"] == "ParamValidationError"
    assert len(rt.calls) == 1  # not retried


def test_M1_transient_transport_errors_are_retried(tmp_path, registry):
    from botocore.exceptions import ConnectTimeoutError, ConnectionClosedError
    c, rt = make_client(tmp_path, registry, [
        ConnectTimeoutError(endpoint_url="x"), ConnectionClosedError(endpoint_url="x"), ok_response()])
    res = c.converse("A", "hi")
    assert res.record.retry_count == 2
    assert [a.code for a in res.record.attempts] == ["ConnectTimeoutError", "ConnectionClosedError"]


def test_M2_attempts_count_toward_calls_and_are_logged(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [client_error("ThrottlingException"), ok_response()])
    res = c.converse("A", "hi")
    assert c.costs.calls == 2 and c.costs.failed_attempts == 1
    a = res.record.attempts
    assert len(a) == 1 and a[0].code == "ThrottlingException" and a[0].backoff_ms is not None
    assert res.record.backoff_ms == pytest.approx(a[0].backoff_ms)


def test_M2_failed_calls_are_counted(tmp_path, registry):
    for alias in registry.aliases:
        registry.models[alias].pricing = Pricing()
    c, rt = make_client(tmp_path, registry, [client_error("ThrottlingException")] * 3)
    with pytest.raises(ModelInvocationError):
        c.converse("A", "hi")
    assert c.costs.calls == 3 and c.costs.failed_attempts == 3
    assert c.costs.input_tokens > 0
    assert c.costs.output_tokens == 3 * 4096
    assert c.costs.unknown_usage_calls == 3
    assert c.costs.unpriced_calls == 3
    assert len(c.logger.read_all()[-1].attempts) == 3


def test_M2_retries_stop_at_call_limit(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [client_error("ThrottlingException")] * 3,
                        limits=UsageLimits(max_calls=2))
    with pytest.raises(ModelInvocationError) as ei:
        c.converse("A", "hi")
    assert len(rt.calls) == 2 and ei.value.record.status == "budget_refused"
    assert ei.value.record.error["after_attempts"] == 2
    assert c.costs.calls == 2


def test_M2_retry_reserves_full_token_budget(tmp_path, registry):
    c, rt = make_client(
        tmp_path,
        registry,
        [client_error("ThrottlingException"), ok_response()],
        limits=UsageLimits(max_output_tokens=150),
    )
    with pytest.raises(ModelInvocationError) as ei:
        c.converse("A", "hi", max_tokens=100)
    assert len(rt.calls) == 1
    assert ei.value.record.status == "budget_refused"
    assert c.costs.output_tokens == 100
    assert c.costs.unknown_usage_calls == 1


def test_M2_retry_reserves_full_dollar_budget(tmp_path, registry):
    for alias in registry.aliases:
        registry.models[alias].pricing = fake_price()
    c, rt = make_client(
        tmp_path,
        registry,
        [client_error("ThrottlingException"), ok_response()],
        limits=UsageLimits(max_budget_usd=0.004),
    )
    with pytest.raises(ModelInvocationError) as ei:
        c.converse("A", "hi", max_tokens=100)
    assert len(rt.calls) == 1
    assert ei.value.record.status == "budget_refused"
    assert c.costs.dollar_guard_active is True
    assert 0 < c.costs.spent_usd_priced <= 0.004


def test_M3_cache_hit_cost_and_latency_fields(tmp_path, registry):
    registry.models["A"].pricing = fake_price()
    c, _ = make_client(tmp_path, registry, [ok_response(inp=1000, out=1000)])
    r1 = c.converse("A", "p", max_tokens=100)
    r2 = c.converse("A", "p", max_tokens=100)
    assert r1.record.incurred_cost_usd == pytest.approx(0.018)
    assert r2.record.from_cache and r2.record.cost_usd == pytest.approx(0.018)  # original generation cost
    assert r2.record.incurred_cost_usd == 0.0 and r2.record.cost_status == "not_incurred"
    assert r2.record.original_latency_ms == r1.record.latency_ms
    assert r2.record.server_latency_ms is None and r2.record.final_attempt_latency_ms is None
    assert sum(r.incurred_cost_usd for r in c.logger.read_all()) == pytest.approx(0.018)


def test_M4_structured_single_record_with_validation_status(tmp_path, registry):
    c, _ = make_client(tmp_path, registry, [ok_response('{"code": "x", "filename": "a.csv"}'),
                                            ok_response("no json")])
    ok = c.converse_structured("A", "give json", Demo, use_cache=False)
    bad = c.converse_structured("A", "give json 2", Demo, use_cache=False)
    recs = c.logger.read_all()
    assert ok.parsed.filename == "a.csv"
    assert [r.status for r in recs] == ["success", "success", "parse_error"]
    assert recs[0].validation_status == "schema_valid"          # written with the record
    assert recs[1].validation_status == "parse_error:no_json"
    ev = recs[2]
    assert ev.parent_invocation_id == recs[1].invocation_id == bad.result.record.invocation_id
    assert ev.input_tokens is None and ev.output_tokens is None and ev.latency_ms is None
    assert sum(r.output_tokens or 0 for r in recs) == 10           # no double counting


def test_M4_cache_hit_revalidates(tmp_path, registry):
    c, rt = make_client(tmp_path, registry, [ok_response('{"code": "x", "filename": "a.csv"}')])
    c.converse_structured("A", "give json", Demo)
    s2 = c.converse_structured("A", "give json", Demo)
    assert len(rt.calls) == 1 and s2.parsed.filename == "a.csv"
    assert c.logger.read_all()[-1].validation_status == "schema_valid"


def test_M5_missing_usage_is_unavailable_not_zero(tmp_path, registry):
    registry.models["A"].pricing = fake_price()
    resp = ok_response()
    del resp["usage"]
    c, _ = make_client(tmp_path, registry, [resp])
    res = c.converse("A", "hi", max_tokens=100)
    assert res.record.cost_usd is None and res.record.cost_status == "unavailable"
    assert res.record.error["type"] == "MissingUsage"
    assert c.costs.unknown_usage_calls == 1 and c.costs.output_tokens == 100  # charged worst case
    assert estimate_cost(fake_price(), None, 5) is None


def test_minor_input_estimate_is_conservative_for_numeric_prompts():
    from src.bedrock.client import estimate_input_tokens_upper
    csv = "\n".join(",".join(str(i * j) for j in range(10)) for i in range(100))
    est = estimate_input_tokens_upper([{"role": "user", "content": [{"text": csv}]}], None)
    assert est >= len(csv)  # >= 1 token per char even for digit-dense text


def test_minor_dollar_guard_inactive_when_any_model_unpriced(tmp_path, registry):
    registry.models["A"].pricing = fake_price()
    registry.models["B"].pricing = Pricing()
    c, _ = make_client(tmp_path, registry, [], limits=UsageLimits(max_budget_usd=1.0))
    assert c.costs.dollar_guard_active is False


def test_minor_pricing_verified_requires_provenance():
    assert not Pricing(input_per_mtok=1.0, output_per_mtok=2.0).verified
    assert not Pricing(input_per_mtok=1.0, output_per_mtok=2.0, source="x", retrieved="yesterday").verified
    assert fake_price().verified


def test_minor_registry_rejects_duplicate_model_ids(registry):
    from src.bedrock.models import ModelRegistry
    models = dict(registry.models)
    models["D"] = models["A"].model_copy(update={"alias": "D"})
    with pytest.raises(ValueError, match="Duplicate model_id"):
        ModelRegistry(region="us-east-1", models=models)


def test_minor_cache_writes_are_atomic(tmp_path, registry):
    c, _ = make_client(tmp_path, registry, [ok_response()])
    c.converse("A", "hi")
    files = list((tmp_path / "cache").iterdir())
    assert len(files) == 1 and files[0].suffix == ".json"  # no leftover temp files


def test_minor_context_run_id(tmp_path, registry):
    c, _ = make_client(tmp_path, registry, [ok_response()])
    c.converse("A", "hi", context=InvocationContext(run_id="exp-abc"))
    assert c.logger.read_all()[0].context.run_id == "exp-abc"
