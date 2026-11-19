"""LIVE Bedrock tests. Skipped unless RUN_LIVE=1. Inference tests here are PAID.

Run only by the lead after user approval:
  RUN_LIVE=1 .venv/bin/python -m pytest -q -m live tests/test_bedrock_live.py

Hard caps: 7 planned inference calls, at most 10 API attempts in total (shared ledger below), small maxTokens,
no cache. Every call is logged to results/raw/live_test_invocations.jsonl (kept, never hidden).
"""

from __future__ import annotations

import os

import pytest
from pydantic import BaseModel

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("RUN_LIVE") != "1", reason="live Bedrock tests need RUN_LIVE=1"),
]

LIVE_MAX_CALLS = 10  # 7 planned calls + 3 attempts of retry headroom (max_calls counts attempts)
MAX_TOKENS = 512  # gpt-oss spends output tokens on reasoning before answering


@pytest.fixture(scope="module")
def registry():
    from src.bedrock.models import load_registry
    return load_registry()


@pytest.fixture(scope="module")
def client(registry):
    from src.bedrock.client import BedrockClient
    from src.bedrock.models import REPO_ROOT
    from src.bedrock.usage import UsageLimits
    raw = REPO_ROOT / "results" / "raw"
    return BedrockClient(
        registry,
        log_path=raw / "live_test_invocations.jsonl",
        ledger_path=raw / "live_test_ledger.json",
        cache_dir=None,
        limits=UsageLimits(max_calls=LIVE_MAX_CALLS, max_input_tokens=20_000,
                           max_output_tokens=LIVE_MAX_CALLS * MAX_TOKENS),
    )


def _ctx(stage):
    from src.bedrock.usage import InvocationContext
    return InvocationContext(experiment_id="live_tests", stage_id=stage, prompt_version="live.v1")


def test_live_control_plane_discovery(registry):
    """Free control-plane calls: every configured study model is callable as configured."""
    import boto3
    from src.bedrock.discovery import build_report
    session = boto3.Session(profile_name=registry.aws_profile, region_name=registry.region)
    rep = build_report(registry, session.client("bedrock"), generated_at="live-test")
    bad = {a: e for a, e in rep["study_models"].items() if not e["callable_as_configured"]}
    assert not bad, bad


@pytest.mark.parametrize("alias", ["A", "B", "C"])
def test_live_plain_call(client, alias):
    r = client.converse(alias, "Reply with exactly: OK", context=_ctx("live_text"),
                        use_cache=False, max_tokens=MAX_TOKENS)
    assert r.record.status == "success" and r.record.model_id == client.registry.get(alias).model_id
    assert r.record.input_tokens and r.record.output_tokens
    assert r.record.cost_status in ("unavailable", "estimated")  # never a guessed $0


class MeanResult(BaseModel):
    count: int
    mean: float


@pytest.mark.parametrize("alias", ["A", "B", "C"])
def test_live_structured_call(client, alias):
    sr = client.converse_structured(alias, "Compute the count and arithmetic mean of: 3, 5, 10.", MeanResult,
                                    context=_ctx("live_structured"), use_cache=False, max_tokens=MAX_TOKENS)
    # Report, do not repair: a parse failure is a legitimate observation, but must be logged.
    assert sr.result.record.validation_status is not None
    if sr.parsed is not None:
        assert sr.parsed.count == 3


def test_live_truncation_is_flagged(client):
    r = client.converse("A", "Count from 1 to 200, separated by commas.", context=_ctx("live_truncation"),
                        use_cache=False, max_tokens=16)
    assert r.record.stop_reason == "max_tokens" and r.record.truncated
