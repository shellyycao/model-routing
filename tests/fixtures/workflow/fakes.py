# SYNTHETIC_FIXTURE - offline test doubles. Not model outputs, not results; never written to results/.
"""Fakes for offline workflow tests.

FakeBedrockRuntime  stands in for the boto3 bedrock-runtime client inside a REAL BedrockClient, so
                    invocation logging, cache semantics and the usage ledger are exercised for real.
                    It answers with scripted structured outputs chosen by (model alias, stage):
                      "ok"            valid output (cleaning/analysis: a Benchmark reference solution script)
                      "bug:<name>"    valid output whose script injects that solution's deliberate bug
                      "garbage"       text with no JSON (parse_error)
                      "truncated"     cut-off JSON with stopReason=max_tokens (truncated)
                      "throttle"      ThrottlingException on every attempt (throttled_exhausted -> infra)
                      "access_denied" AccessDeniedException (api_error -> infra)
FixtureExecutor     stands in for the sandbox. It runs ONLY the trusted Benchmark solution scripts in
                    tests/fixtures/benchmark/solutions/: the submitted code must be byte-identical to one
                    of them (optionally preceded by one "# FIXTURE_ARGV: <bug>" line); anything else is
                    refused without running. Model-generated code is never executed here.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from botocore.exceptions import ClientError

from src.bedrock.client import BedrockClient, RetryPolicy
from src.bedrock.concurrency import ModelRateLimiter
from src.bedrock.models import Pricing, load_registry
from src.bedrock.usage import UsageLimits
from src.contracts import ExecutionResult, ExecutionStatus, ProjectSpec

REPO = Path(__file__).resolve().parents[3]
SOLUTIONS = REPO / "tests" / "fixtures" / "benchmark" / "solutions"
PROJECTS = REPO / "datasets" / "projects"
FAKE_IMAGE = "UNVERIFIED-TEST-FIXTURE"
_ARGV = re.compile(r"^# FIXTURE_ARGV: ([A-Za-z0-9_]+)\n")


def solution_code(project_id: str, stage: str, bug: str | None = None) -> str:
    kind = "clean" if stage == "cleaning" else "analysis"
    code = (SOLUTIONS / f"{project_id}_{kind}.py").read_text()
    return (f"# FIXTURE_ARGV: {bug}\n" if bug else "") + code


def _wrap(obj: dict) -> str:
    return "SYNTHETIC_FIXTURE response\n```json\n" + json.dumps(obj) + "\n```"


def _report(project_id: str, prompt: str) -> dict:
    spec = ProjectSpec.model_validate_json((PROJECTS / project_id / "project.json").read_text())
    block = prompt.split("VERIFIED_FINDINGS_JSON", 1)[1].split("```json\n", 1)[1].split("\n```", 1)[0]
    findings = json.loads(block)
    kfs = []
    for q in spec.analysis_questions:
        vals = {k: findings[k] for k in q.metric_keys if isinstance(findings.get(k), (int, float))}
        direction = None
        if q.direction_key and isinstance(findings.get(q.direction_key), (int, float)):
            direction = ("increase" if findings[q.direction_key] > 0 else
                         "decrease" if findings[q.direction_key] < 0 else "no_change")
        ranking = None
        if q.ranking_labels and all(isinstance(findings.get(k), (int, float)) for k in q.ranking_labels):
            ranking = [q.ranking_labels[k] for k in sorted(
                q.ranking_labels, key=lambda k: (-findings[k], q.ranking_labels[k]))]
        statement = "; ".join(f"{k.replace('_', ' ')}: {vals[k]}" for k in q.metric_keys)
        if direction:
            statement += f"; direction: {direction}"
        kfs.append({"finding_id": q.question_id,
                    "statement": statement + ".",
                    "evidence_refs": list(q.metric_keys), "reported_values": vals,
                    "direction": direction, "ranking": ranking})
    return {"title": "SYNTHETIC_FIXTURE report", "executive_summary": "Summary of the verified findings.",
            "key_findings": kfs, "limitations": ["Synthetic data."], "conclusion": "See the key findings."}


class FakeBedrockRuntime:
    def __init__(self, behaviours: dict[tuple[str, str], str] | None = None, registry=None):
        self.behaviours = behaviours or {}
        self.registry = registry or load_registry()
        if registry is None:
            # Workflow fixtures intentionally exercise the unpriced accounting path.
            for spec in self.registry.models.values():
                spec.pricing = Pricing()
        self.calls: list[dict] = []

    def _alias(self, model_id: str) -> str:
        return self.registry.get(model_id).alias

    def converse(self, **kwargs):
        prompt = kwargs["messages"][0]["content"][0]["text"]
        stage = re.search(r"^STAGE: (\w+)", prompt, re.M).group(1)
        project = re.search(r"^PROJECT: (\w+)", prompt, re.M).group(1)
        alias = self._alias(kwargs["modelId"])
        self.calls.append({"alias": alias, "stage": stage, "project": project, "prompt": prompt})
        b = self.behaviours.get((alias, stage), "ok")
        if b == "throttle":
            raise ClientError({"Error": {"Code": "ThrottlingException", "Message": "SYNTHETIC"}}, "Converse")
        if b == "access_denied":
            raise ClientError({"Error": {"Code": "AccessDeniedException", "Message": "SYNTHETIC"}}, "Converse")
        stop = "end_turn"
        if b == "garbage":
            text = "SYNTHETIC_FIXTURE: I cannot produce JSON."
        elif b == "truncated":
            text, stop = '```json\n{"python_code": "import pa', "max_tokens"
        else:
            bug = b.split(":", 1)[1] if b.startswith("bug:") else None
            if stage == "cleaning":
                text = _wrap({"python_code": solution_code(project, stage, bug), "output_filename": "cleaned.csv",
                              "cleaning_logic": "SYNTHETIC_FIXTURE cleaning logic."})
            elif stage == "analysis":
                text = _wrap({"python_code": solution_code(project, stage, bug),
                              "expected_artifacts": ["findings.json"],
                              "methods_description": "SYNTHETIC_FIXTURE methods."})
            else:
                text = _wrap(_report(project, prompt))
        return {"output": {"message": {"role": "assistant", "content": [{"text": text}]}},
                "usage": {"inputTokens": len(prompt) // 4, "outputTokens": len(text) // 4},
                "metrics": {"latencyMs": 5}, "stopReason": stop}


def make_client(tmp: Path, runtime: FakeBedrockRuntime, limits: UsageLimits | None = None) -> BedrockClient:
    return BedrockClient(
        runtime.registry, runtime_client=runtime,
        log_path=tmp / "invocations.jsonl", ledger_path=tmp / "ledger.json", cache_dir=tmp / "cache",
        limits=limits or UsageLimits(max_calls=100_000, max_input_tokens=10**10, max_output_tokens=10**10),
        retry=RetryPolicy(max_attempts=2, base_delay_s=0.0), sleep=lambda s: None,
        rate_limiter=ModelRateLimiter({}))


class FixtureExecutor:
    """Runs trusted fixture scripts only. Results are memoised by (script, argv, input hashes) to keep
    the 27-path tests fast; outputs are always copied into the requested (fresh) output_dir."""

    image = FAKE_IMAGE

    def __init__(self, status_override: ExecutionStatus | None = None):
        self.status_override = status_override
        self.calls: list[dict] = []
        self._memo: dict[str, Path] = {}
        self._memo_root = Path(tempfile.mkdtemp(prefix="fixture-exec-"))
        self._known = {hashlib.sha256(p.read_bytes()).hexdigest(): p for p in SOLUTIONS.glob("*.py")}

    def execute(self, code, inputs, output_dir, limits=None) -> ExecutionResult:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        self.calls.append({"inputs": dict(inputs), "output_dir": str(out)})
        if self.status_override is not None:
            return ExecutionResult(status=self.status_override, stderr="SYNTHETIC override", sandbox_image=FAKE_IMAGE)
        argv = []
        m = _ARGV.match(code)
        if m:
            argv, code = [m.group(1)], code[m.end():]
        script = self._known.get(hashlib.sha256(code.encode()).hexdigest())
        if script is None:
            return ExecutionResult(status=ExecutionStatus.SECURITY_VIOLATION, exit_code=None,
                                   stderr="FixtureExecutor refuses code that is not a trusted fixture script",
                                   sandbox_image=FAKE_IMAGE)
        key = hashlib.sha256(json.dumps([script.name, argv, sorted(
            (n, hashlib.sha256(Path(p).read_bytes()).hexdigest()) for n, p in inputs.items())]).encode()).hexdigest()
        t0 = time.monotonic()
        if key not in self._memo:
            res_dir = self._memo_root / key
            res_dir.mkdir()
            with tempfile.TemporaryDirectory() as ind:
                for name, host in inputs.items():
                    shutil.copy(host, Path(ind) / name)
                proc = subprocess.run([sys.executable, str(script), *argv], cwd=res_dir, capture_output=True,
                                      text=True, timeout=120,
                                      env={"PATH": os.environ.get("PATH", ""), "INPUT_DIR": ind, "OUTPUT_DIR": str(res_dir)})
            (self._memo_root / f"{key}.rc").write_text(f"{proc.returncode}\n{proc.stderr[-2000:]}")
            self._memo[key] = res_dir
        rc, _, err = (self._memo_root / f"{key}.rc").read_text().partition("\n")
        files = []
        for f in sorted(self._memo[key].iterdir()):
            shutil.copy(f, out / f.name)
            files.append(str(out / f.name))
        status = ExecutionStatus.SUCCESS if rc == "0" else ExecutionStatus.RUNTIME_ERROR
        return ExecutionResult(status=status, exit_code=int(rc), stderr=err, runtime_ms=(time.monotonic() - t0) * 1000,
                               output_files=files, sandbox_image=FAKE_IMAGE)
