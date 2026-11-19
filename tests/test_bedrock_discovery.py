"""Offline tests for model discovery (fake control-plane client; SYNTHETIC_FIXTURE data)."""

from __future__ import annotations

import importlib.util
import json

import pytest

from src.bedrock.discovery import annotate_study_models, build_report, redact
from src.bedrock.models import REPO_ROOT, load_registry

FAKE_ACCT = "123456789012"  # SYNTHETIC_FIXTURE account number, used to test redaction


class FakeControl:
    """SYNTHETIC_FIXTURE: minimal ListFoundationModels / ListInferenceProfiles responses."""

    def __init__(self, c_status="ACTIVE", profile_page_size=1):
        self.c_status = c_status
        self.page = profile_page_size
        self.calls = []

    def list_foundation_models(self, **kw):
        self.calls.append(("fm", kw))
        def m(mid, types, status="ACTIVE"):
            return {"modelId": mid, "modelName": mid, "providerName": "x", "inputModalities": ["TEXT"],
                    "outputModalities": ["TEXT"], "inferenceTypesSupported": types,
                    "modelLifecycle": {"status": status}, "responseStreamingSupported": True}
        return {"modelSummaries": [
            m("anthropic.claude-sonnet-4-6", ["INFERENCE_PROFILE"]),
            m("amazon.nova-pro-v1:0", ["ON_DEMAND", "INFERENCE_PROFILE"]),
            m("openai.gpt-oss-120b-1:0", ["ON_DEMAND"], self.c_status),
            m("legacy.model-v1", ["ON_DEMAND"], "LEGACY"),
        ], "ResponseMetadata": {"RequestId": "r"}}

    def list_inference_profiles(self, **kw):
        self.calls.append(("ip", kw))
        def p(pid, base):
            return {"inferenceProfileId": pid, "inferenceProfileName": pid, "status": "ACTIVE",
                    "type": "SYSTEM_DEFINED",
                    "inferenceProfileArn": f"arn:aws:bedrock:us-east-1:{FAKE_ACCT}:inference-profile/{pid}",
                    "models": [{"modelArn": f"arn:aws:bedrock:{r}::foundation-model/{base}"}
                               for r in ("us-east-1", "us-west-2")]}
        allp = [p("us.anthropic.claude-sonnet-4-6", "anthropic.claude-sonnet-4-6"),
                p("us.amazon.nova-pro-v1:0", "amazon.nova-pro-v1:0")]
        start = int(kw.get("nextToken") or 0)
        out = {"inferenceProfileSummaries": allp[start:start + self.page]}
        if start + self.page < len(allp):
            out["nextToken"] = str(start + self.page)
        return out


def test_report_annotates_study_models_and_paginates():
    fake = FakeControl()
    rep = build_report(load_registry(), fake, generated_at="2026-01-01T00:00:00+00:00")
    assert [c[0] for c in fake.calls] == ["fm", "ip", "ip"]
    assert rep["counts"] == {"text_models": 4, "text_models_active": 3, "system_inference_profiles": 2}
    s = rep["study_models"]
    assert s["A"]["id_kind"] == "system_inference_profile" and s["A"]["callable_as_configured"]
    assert s["A"]["profile_includes_configured_region"] and s["A"]["profile_regions"] == ["us-east-1", "us-west-2"]
    assert s["C"]["id_kind"] == "foundation_model" and s["C"]["active"] and s["C"]["callable_as_configured"]
    assert rep["all_study_models_ok"] is True
    assert {m["model_id"] for m in rep["text_models"]} >= {"legacy.model-v1"}


def test_report_contains_no_account_id_or_arns():
    rep = build_report(load_registry(), FakeControl(), generated_at="t")
    blob = json.dumps(rep)
    assert FAKE_ACCT not in blob and "inferenceProfileArn" not in blob and "RequestId" not in blob


def test_inactive_or_missing_model_flagged():
    reg = load_registry()
    rep = build_report(reg, FakeControl(c_status="LEGACY"), generated_at="t")
    assert rep["study_models"]["C"]["active"] is False and rep["all_study_models_ok"] is False
    s = annotate_study_models(reg, [], [])
    assert all(e["id_kind"] == "not_found" and not e["present"] for e in s.values())


def test_redact():
    assert redact({"m": [f"arn:aws:iam::{FAKE_ACCT}:user/x"]}) == {"m": ["arn:aws:iam::<redacted-account>:user/x"]}
    assert redact("1234567890123") == "1234567890123"  # 13 digits: not an account id


def _load_script():
    spec = importlib.util.spec_from_file_location("discover_models", REPO_ROOT / "scripts" / "discover_models.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_probe_refuses_without_run_live(monkeypatch, capsys):
    mod = _load_script()
    monkeypatch.delenv("RUN_LIVE", raising=False)
    called = []
    monkeypatch.setattr(mod, "probe", lambda reg: called.append(1))
    assert mod.main(["--probe"]) == 2
    assert called == [] and "RUN_LIVE=1" in capsys.readouterr().err


def test_script_writes_report_with_fake_session(monkeypatch, tmp_path):
    mod = _load_script()
    import boto3

    class FakeSession:
        def __init__(self, **kw):
            pass

        def client(self, name):
            assert name == "bedrock"  # control plane only, never bedrock-runtime
            return FakeControl()
    monkeypatch.setattr(boto3, "Session", FakeSession)
    out = tmp_path / "disc.json"
    assert mod.main(["--out", str(out)]) == 0
    d = json.loads(out.read_text())
    assert d["region"] == "us-east-1" and "probe" not in d
