"""Workflow stages: prompt -> model call -> parse -> sandboxed execution -> validation -> record.

run_cleaning / run_analysis / run_reporting each take a HandoffPackage (built by
src.workflow.handoff from the ACTUAL upstream artifacts) and return a StageResult holding a
contracts-v1.1 StageRunRecord plus the StageArtifacts for the next stage.

Prompts
-------
Templates live in prompts/<PROMPT_VERSION>/{cleaning,analysis,reporting}.txt and are IDENTICAL for
every model. They are rendered from the ProjectSpec and the HandoffPackage only. Model-written text
and data excerpts inserted into a prompt are capped by bytes (src.workflow.handoff caps), so every
prompt has a computable upper size (`prompt_input_token_upper_bound`). The structured-output
instruction is appended by BedrockClient.converse_structured (CleaningOutput / AnalysisOutput /
ReportOutput from src.contracts).
`StageRunRecord.prompt_hash` = sha256 of the exact full prompt sent (rendered template + schema
instruction); the full prompt is saved as <stage_dir>/prompt.txt. Template hashes
(`template_hashes()`) go into the run's config_hash.

Inference settings / retries
----------------------------
One `max_tokens` setting (default: the registry's value) and the client's RetryPolicy (transport
and throttling retries only) are used for every model, stage and path. There is NO
orchestration-level retry, re-prompt or output repair: one model call per stage.

Failure classification (StageStatus / FailureType)
--------------------------------------------------
Model-attributable -> StageStatus.FAILED (run outcome "infeasible"):
  structured output unparseable                         PARSE_ERROR
  unparseable AND the call hit maxTokens                TRUNCATED
  ExecutionStatus.RUNTIME_ERROR (non-zero exit, OOM)    EXECUTION_ERROR
  ExecutionStatus.TIMEOUT                               TIMEOUT
  ExecutionStatus.INVALID_OUTPUT / unsafe output name   INVALID_OUTPUT
  ExecutionStatus.SECURITY_VIOLATION                    SECURITY_VIOLATION
  ExecutionStatus.TEST_FAILURE, or a mandatory
    validator check failed (ground-truth basis)         VALIDATION_FAILED
Infrastructure -> StageStatus.INFRA_ERROR (run outcome "void_infra", kept but not counted as
model infeasibility):
  sandbox gate refused (no/invalid verification record, image mismatch)   INFRA
  ExecutionStatus.SANDBOX_UNAVAILABLE, or executed image != verified image INFRA
  client budget_refused (hard call/token limit)                           INFRA
  client throttled_exhausted (throttling/transport retries exhausted)     API_ERROR
  client api_error (non-retryable ClientError: AccessDenied, Validation,
    ResourceNotFound, ...) and client_error (other client-side exception)  API_ERROR
  unexpected harness exception                                            INFRA
Upstream attribution (orchestrator, continue_with_actual_artifact policy) -> BLOCKED_BY_INVALID_ARTIFACT:
  the upstream artifact is missing or fails the structural checks (StageRunRecord.structural_ok:
  CLEANING_STRUCTURAL_CHECKS / ANALYSIS_STRUCTURAL_CHECKS); no model call is made.
Note: a non-retryable ValidationException (e.g. prompt too long for a model's context) is also
classed as infrastructure. Prompt sizes are capped, so this is not expected; any occurrence is
visible in failure_detail and in results/raw/invocations.jsonl.

Sandbox gate
------------
Model-generated code is executed only through an Executor and only after `SandboxGate.check`
passes: results/verification/sandbox_verification.json must exist with "all_controls_verified": true and
an "image_id" equal to the executor's current local image ID (DockerExecutor.availability()).
After execution the ExecutionResult.sandbox_image must equal the same ID. Otherwise the stage is
INFRA_ERROR with the reason; the gate is checked BEFORE the model call, so no paid call is made
for code that could not be run. `SandboxGate.unverified_test_bypass()` exists for offline tests
with fake executors only.

Quality bases
-------------
`validation` is always against ground truth. `conditional_validation`:
  analysis   trusted reference analysis recomputed on the ACTUAL upstream cleaned CSV
             (src.evaluation.analysis.conditional_reference_metrics); None if not computable.
  reporting  the ACTUAL verified upstream findings.json.
Failed outputs are never replaced by ground truth.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from src.bedrock.client import ModelInvocationError, estimate_input_tokens_upper
from src.bedrock.models import REPO_ROOT
from src.bedrock.provenance import hash_file
from src.bedrock.structured import schema_instruction
from src.bedrock.usage import InvocationContext
from src.contracts import (
    AnalysisOutput,
    CleaningOutput,
    ExecutionResult,
    ExecutionStatus,
    FailureType,
    HandoffPackage,
    ProjectSpec,
    ReportOutput,
    ResourceLimits,
    StageId,
    StageRunRecord,
    StageStatus,
    StageTimings,
    ValidationResult,
)
from src.evaluation.analysis import conditional_reference_metrics, validate_analysis
from src.evaluation.cleaning import validate_cleaning
from src.evaluation.reporting import validate_reporting
from src.evaluation.reporting_v3 import validate_reporting_v3

from .handoff import (
    MAX_HEAD_BYTES,
    MAX_STATUS_BYTES,
    MAX_TEXT_BYTES,
    StageArtifacts,
    file_head,
    status_string,
    truncate_bytes,
)

PROMPT_VERSION = "v2"   # frozen-v2 default; experiments select a protocol explicitly

# Experiment protocols (user decision 2026-11-18: prospective v3 is PRIMARY; frozen v2 is retained as pilot).
# A protocol fixes the prompt version and the reporting validator for EVERY path of an experiment.
PROTOCOLS: dict[str, dict[str, str]] = {
    "v2": {"prompt_version": "v2", "reporting_validator": "v2"},
    "v3": {"prompt_version": "v3", "reporting_validator": "v3"},
}


def protocol_prompt_version(protocol: str) -> str:
    if protocol not in PROTOCOLS:
        raise ValueError(f"unknown protocol {protocol!r}; known: {sorted(PROTOCOLS)}")
    return PROTOCOLS[protocol]["prompt_version"]
PROMPTS_DIR = REPO_ROOT / "prompts"
DEFAULT_VERIFICATION_PATH = REPO_ROOT / "results" / "verification" / "sandbox_verification.json"
SCHEMAS: dict[StageId, type[BaseModel]] = {
    StageId.CLEANING: CleaningOutput,
    StageId.ANALYSIS: AnalysisOutput,
    StageId.REPORTING: ReportOutput,
}
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MAX_SUMMARY_FILE = 100_000
_FLOAT_BOUND = -2.2250738585072014e-308   # longest float repr: used for prompt size bounds


# ============================================================================ prompts
def template_path(stage: StageId, version: str = PROMPT_VERSION) -> Path:
    return PROMPTS_DIR / version / f"{stage.value}.txt"


def load_template(stage: StageId, version: str = PROMPT_VERSION) -> str:
    return template_path(stage, version).read_text(encoding="utf-8")


def template_hashes(version: str = PROMPT_VERSION) -> dict[str, str]:
    return {s.value: hashlib.sha256(load_template(s, version).encode()).hexdigest() for s in SCHEMAS}


_VAR = re.compile(r"\{\{(\w+)\}\}")


def render(template: str, variables: dict[str, Any]) -> str:
    """Single-pass substitution of {{name}}; unknown names raise KeyError."""
    return _VAR.sub(lambda m: str(variables[m.group(1)]), template)


def _fmt_schema(view: dict) -> str:
    lines = []
    for c in view["cleaned_schema"]:
        parts = [c["dtype"], "nullable" if c.get("nullable") else "not nullable"]
        if c.get("allowed_values") is not None:
            parts.append("allowed values: " + ", ".join(repr(v) for v in c["allowed_values"]))
        if c.get("min_value") is not None:
            parts.append(f"min {c['min_value']:g}")
        if c.get("max_value") is not None:
            parts.append(f"max {c['max_value']:g}")
        lines.append(f"- {c['name']}: " + "; ".join(parts))
    return "\n".join(lines)


def _fmt_questions(view: dict) -> str:
    return "\n".join(f"- {q['question_id']}: {q['question']}\n  metric_keys: {', '.join(q['metric_keys'])}"
                     for q in view["analysis_questions"])


def required_metric_keys(spec: ProjectSpec) -> list[str]:
    return [k for q in spec.model_view()["analysis_questions"] for k in q["metric_keys"]]


def _base_vars(spec: ProjectSpec) -> dict[str, Any]:
    """ONLY ProjectSpec.model_view() is rendered (contracts v1.2): never notes, tolerances,
    canonical/ground-truth paths or validator-only metadata."""
    view = spec.model_view()
    rep = view["reporting"]
    return {
        "project_id": view["project_id"],
        "objective": view["objective"],
        "cleaned_filename": view["cleaned_data_filename"],
        "findings_filename": view["findings_filename"],
        "cleaned_schema": _fmt_schema(view),
        "analysis_questions": _fmt_questions(view),
        "metric_keys": ", ".join(k for q in view["analysis_questions"] for k in q["metric_keys"]),
        "required_finding_ids": ", ".join(rep["required_finding_ids"]),
        "max_words": rep.get("max_words") or "no limit",
        "audience": rep["audience"],
    }


def model_input_files(spec: ProjectSpec, project_dir: str | Path) -> dict[str, str]:
    """Cleaning-stage sandbox inputs: ONLY ProjectSpec.model_input_files() (in-sandbox name -> host
    path). The contract rejects canonical/ground-truth files in that list."""
    return {f.name: str(Path(project_dir) / f.path) for f in spec.model_input_files()}


def _handoff_vars(handoff: HandoffPackage) -> dict[str, Any]:
    return {
        "completed_stages": ", ".join(s.value for s in handoff.completed_stages) or "none",
        "validation_status": json.dumps(handoff.validation_status, ensure_ascii=False),
    }


def cleaning_prompt(spec: ProjectSpec, project_dir: str | Path, version: str = PROMPT_VERSION) -> str:
    view = spec.model_view()
    blocks = []
    for f, desc in zip(spec.model_input_files(), view["input_files"]):
        head, total = file_head(Path(project_dir) / f.path, max_lines=15)
        blocks.append(f"### {desc['name']} ({desc['description'] or 'input file'}; {total} lines in total)\n"
                      f"First lines:\n```\n{head}\n```")
    v = _base_vars(spec) | {
        "input_files": "\n\n".join(blocks),
        "input_names": ", ".join(f'"{d["name"]}"' for d in view["input_files"]),
        "cleaning_requirements": "\n".join(view["cleaning_requirements"]),
    }
    return render(load_template(StageId.CLEANING, version), v)


def _analysis_vars(spec: ProjectSpec, handoff: HandoffPackage, cleaned_csv: str | Path | None) -> dict[str, Any]:
    cl_out = handoff.stage_outputs.get(StageId.CLEANING.value, {}) or {}
    cl_res = handoff.verified_results.get(StageId.CLEANING.value, {}) or {}
    summary = cl_res.get("cleaning_summary")
    head, total = file_head(cleaned_csv) if cleaned_csv else ("", 0)
    return _base_vars(spec) | _handoff_vars(handoff) | {
        "cleaning_logic": truncate_bytes(str(cl_out.get("cleaning_logic") or "(none provided)"), MAX_TEXT_BYTES),
        "cleaning_summary": truncate_bytes(json.dumps(summary, ensure_ascii=False) if summary is not None
                                           else "(not available)", MAX_TEXT_BYTES),
        "cleaned_head": head,
        "cleaned_total_lines": total,
    }


def analysis_prompt(spec: ProjectSpec, handoff: HandoffPackage, cleaned_csv: str | Path,
                    version: str = PROMPT_VERSION) -> str:
    return render(load_template(StageId.ANALYSIS, version), _analysis_vars(spec, handoff, cleaned_csv))


def _findings_block(spec: ProjectSpec, findings: dict) -> str:
    out = {}
    for k in required_metric_keys(spec):
        v = findings.get(k)
        ok = isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        out[k] = float(v) if ok else "MISSING_OR_NON_NUMERIC"
    return json.dumps(out, indent=2)


def _reporting_vars(spec: ProjectSpec, handoff: HandoffPackage, findings: dict) -> dict[str, Any]:
    an_out = handoff.stage_outputs.get(StageId.ANALYSIS.value, {}) or {}
    return _base_vars(spec) | _handoff_vars(handoff) | {
        "methods_description": truncate_bytes(str(an_out.get("methods_description") or "(none provided)"),
                                              MAX_TEXT_BYTES),
        "verified_findings": _findings_block(spec, findings),
    }


def reporting_prompt(spec: ProjectSpec, handoff: HandoffPackage, findings: dict, version: str = PROMPT_VERSION) -> str:
    if version == "v3":
        return reporting_prompt_v3(spec, handoff, findings)
    return render(load_template(StageId.REPORTING, version), _reporting_vars(spec, handoff, findings))


def reporting_prompt_v3(spec: ProjectSpec, handoff: HandoffPackage, findings: dict) -> str:
    """Render the post-freeze v3 reporting prompt without changing the active v2 workflow."""
    requirements = {}
    for question in spec.analysis_questions:
        requirements[question.question_id] = {
            "direction_required": question.direction_key is not None,
            "direction_metric_key": question.direction_key,
            "ranking_required": question.ranking_labels is not None,
            "ranking_metric_key_to_label": question.ranking_labels,
        }
    variables = _reporting_vars(spec, handoff, findings) | {
        "structured_claim_requirements": json.dumps(requirements, indent=2, ensure_ascii=False),
    }
    return render(load_template(StageId.REPORTING, version="v3"), variables)


def full_prompt(prompt: str, stage: StageId) -> str:
    """Exactly what converse_structured sends."""
    return f"{prompt}\n\n{schema_instruction(SCHEMAS[stage])}"


def prompt_input_token_upper_bound(stage: StageId, spec: ProjectSpec, project_dir: str | Path,
                                   version: str = PROMPT_VERSION) -> int:
    """Upper bound of the input-token estimate the client's ledger reserves for this stage's call
    (BedrockClient.estimate_input_tokens_upper: 1 token per UTF-8 byte + overhead). Variable parts
    are filled with maximal-size placeholders at their byte caps, so this bounds every real prompt."""
    if stage == StageId.CLEANING:
        text = cleaning_prompt(spec, project_dir, version)
    else:
        filler_status = json.dumps({s.value: "x" * MAX_STATUS_BYTES for s in SCHEMAS if s != StageId.REPORTING}
                                   if stage == StageId.REPORTING else {StageId.CLEANING.value: "x" * MAX_STATUS_BYTES})
        common = {"completed_stages": "cleaning, analysis", "validation_status": filler_status}
        if stage == StageId.ANALYSIS:
            v = _base_vars(spec) | common | {
                "cleaning_logic": "x" * MAX_TEXT_BYTES, "cleaning_summary": "x" * MAX_TEXT_BYTES,
                "cleaned_head": "x" * MAX_HEAD_BYTES, "cleaned_total_lines": 9_999_999_999,
            }
        else:
            v = _base_vars(spec) | common | {
                "methods_description": "x" * MAX_TEXT_BYTES,
                "verified_findings": json.dumps({k: _FLOAT_BOUND for k in required_metric_keys(spec)}, indent=2),
            }
            if version == "v3":
                v["structured_claim_requirements"] = json.dumps({
                    q.question_id: {"direction_required": q.direction_key is not None,
                                    "direction_metric_key": q.direction_key,
                                    "ranking_required": q.ranking_labels is not None,
                                    "ranking_metric_key_to_label": q.ranking_labels}
                    for q in spec.analysis_questions}, indent=2, ensure_ascii=False)
        text = render(load_template(stage, version), v)
    return estimate_input_tokens_upper([{"role": "user", "content": [{"text": full_prompt(text, stage)}]}], None)


# ============================================================================ sandbox gate
@dataclass
class GateDecision:
    ok: bool
    reason: str
    image_id: str | None = None
    bypassed: bool = False


class SandboxGate:
    """Refuses execution of model-generated code unless the sandbox has been verified.

    The verification record is written by the LEAD after the isolation tests pass; this class
    only reads it. Required keys: "all_controls_verified" (true) and "image_id" (must equal the
    executor's current local image ID). Optional "image" (tag) must equal executor.image if both
    are present.
    """

    def __init__(self, verification_path: str | Path = DEFAULT_VERIFICATION_PATH, *,
                 _unverified_test_bypass: bool = False):
        self.verification_path = Path(verification_path)
        self._bypass = _unverified_test_bypass

    @classmethod
    def unverified_test_bypass(cls) -> "SandboxGate":
        """OFFLINE TESTS ONLY (fake executors that never run model-generated code)."""
        return cls(_unverified_test_bypass=True)

    @property
    def bypassed(self) -> bool:
        return self._bypass

    def check(self, executor: Any) -> GateDecision:
        if self._bypass:
            return GateDecision(True, "UNVERIFIED test bypass (fake executor)", None, bypassed=True)
        p = self.verification_path
        if not p.is_file():
            return GateDecision(False, f"sandbox not verified: {p} does not exist")
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            return GateDecision(False, f"sandbox verification record unreadable: {e}")
        if not isinstance(rec, dict) or rec.get("all_controls_verified") is not True:
            return GateDecision(False, "sandbox verification record does not have all_controls_verified=true")
        want = rec.get("image_id")
        if not isinstance(want, str) or not want:
            return GateDecision(False, "sandbox verification record has no image_id")
        tag = rec.get("image")
        if tag and getattr(executor, "image", None) and tag != executor.image:
            return GateDecision(False, f"executor image tag {executor.image!r} != verified image {tag!r}")
        if hasattr(executor, "availability"):
            ok, info = executor.availability()
            if not ok:
                return GateDecision(False, f"sandbox unavailable: {info}")
            have = info
        elif getattr(executor, "image_id", None):
            have = executor.image_id
        else:
            return GateDecision(False, "cannot determine the executor's image ID")
        if have != want:
            return GateDecision(False, f"executor image ID {have!r} != verified image_id {want!r}")
        return GateDecision(True, "verified", image_id=want)


# ============================================================================ context / results
@dataclass
class StageContext:
    """Everything a stage needs. Identical settings are used for every path of an experiment."""

    client: Any                                # BedrockClient (or a test double with the same API)
    executor: Any                              # src.contracts.Executor
    gate: SandboxGate
    spec: ProjectSpec
    project_dir: Path
    ground_truth: dict
    experiment_id: str
    run_id: str
    path_id: str
    repeat_index: int = 0
    use_cache: bool = False                    # primary experiment: False (fresh calls)
    cache_namespace: str | None = None         # shared-prefix mode only
    max_tokens: int | None = None              # None = registry default (same for all models)
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    reproducibility_rerun: bool = True         # analysis code executed a 2nd time (no model call)
    protocol: str = "v2"                       # "v2" (frozen pilot) | "v3" (prospective primary)

    @property
    def prompt_version(self) -> str:
        return protocol_prompt_version(self.protocol)

    def model_id(self, alias: str) -> str:
        try:
            return self.client.registry.get(alias).model_id
        except Exception:  # noqa: BLE001
            return alias


@dataclass
class StageResult:
    record: StageRunRecord
    artifacts: StageArtifacts | None

    @property
    def passed(self) -> bool:
        return self.record.status == StageStatus.PASSED


def display_path(p: str | Path) -> str:
    """Repo-relative POSIX path when under the repo, else absolute."""
    p = Path(p).resolve()
    try:
        return p.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def _hashes(paths: list[str | Path]) -> dict[str, str]:
    return {display_path(p): hash_file(p) for p in paths if Path(p).is_file()}


class _Rec:
    """Accumulates StageRunRecord fields."""

    def __init__(self, ctx: StageContext, stage: StageId, model_alias: str, handoff_info: tuple[str, int, float]):
        self.ctx = ctx
        self.f: dict[str, Any] = dict(
            stage=stage, model_alias=model_alias, model_id=ctx.model_id(model_alias),
            prompt_version=ctx.prompt_version, invocation_ids=[],
            handoff_in_path=display_path(handoff_info[0]), handoff_size_bytes=handoff_info[1],
            cost_usd=None, cost_status="not_incurred",
        )
        self.timings = StageTimings(handoff_ms=handoff_info[2])
        self.inputs: list[Path] = []
        self.outputs: list[Path] = []

    def done(self, status: StageStatus, ftype: FailureType | None = None, detail: str | None = None) -> StageRunRecord:
        self.f.update(
            status=status, failure_type=ftype,
            failure_detail=truncate_bytes(detail, 4000) if detail else None,
            input_artifacts=[display_path(p) for p in self.inputs],
            input_artifact_hashes=_hashes(self.inputs),
            output_artifacts=[display_path(p) for p in self.outputs if Path(p).is_file()],
            output_artifact_hashes=_hashes(self.outputs),
            timings=self.timings,
        )
        return StageRunRecord(**self.f)


def not_run_record(stage: StageId, model_alias: str, model_id: str, prompt_version: str = PROMPT_VERSION) -> StageRunRecord:
    return StageRunRecord(stage=stage, model_alias=model_alias, model_id=model_id, prompt_version=prompt_version,
                          invocation_ids=[], status=StageStatus.NOT_RUN_UPSTREAM_FAILURE,
                          cost_usd=None, cost_status="not_incurred")


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _dump(path: Path, obj: Any) -> Path:
    return _write(path, json.dumps(obj, indent=2, ensure_ascii=False, default=str))


_EXEC_FAIL = {
    ExecutionStatus.RUNTIME_ERROR: FailureType.EXECUTION_ERROR,
    ExecutionStatus.TIMEOUT: FailureType.TIMEOUT,
    ExecutionStatus.INVALID_OUTPUT: FailureType.INVALID_OUTPUT,
    ExecutionStatus.SECURITY_VIOLATION: FailureType.SECURITY_VIOLATION,
    ExecutionStatus.TEST_FAILURE: FailureType.VALIDATION_FAILED,
}


class _Stop(Exception):
    """Internal: stage ends with (status, failure_type, detail)."""

    def __init__(self, status: StageStatus, ftype: FailureType, detail: str):
        super().__init__(detail)
        self.status, self.ftype, self.detail = status, ftype, detail


def _gate(ctx: StageContext) -> GateDecision:
    d = ctx.gate.check(ctx.executor)
    if not d.ok:
        raise _Stop(StageStatus.INFRA_ERROR, FailureType.INFRA, f"sandbox gate refused execution: {d.reason}")
    return d


def _generate(ctx: StageContext, r: _Rec, stage: StageId, model_alias: str, prompt: str, stage_dir: Path) -> Any:
    """One model call. Returns the parsed structured output or raises _Stop."""
    sent = full_prompt(prompt, stage)
    r.outputs.append(_write(stage_dir / "prompt.txt", sent))
    r.f["prompt_hash"] = hashlib.sha256(sent.encode()).hexdigest()
    inv_ctx = InvocationContext(
        experiment_id=ctx.experiment_id, run_id=ctx.run_id, project_id=ctx.spec.project_id, path_id=ctx.path_id,
        stage_id=stage.value, prompt_version=ctx.prompt_version,
        # Fresh-call mode records the repeat index (the client then refuses any cache use).
        repeat_index=None if ctx.use_cache else ctx.repeat_index,
        input_artifacts=[display_path(p) for p in r.inputs],
    )
    try:
        sres = ctx.client.converse_structured(model_alias, prompt, SCHEMAS[stage], context=inv_ctx,
                                              use_cache=ctx.use_cache, max_tokens=ctx.max_tokens,
                                              cache_namespace=ctx.cache_namespace)
    except ModelInvocationError as e:
        rec = e.record
        r.f["invocation_ids"] = [rec.invocation_id]
        r.f["cost_usd"], r.f["cost_status"] = rec.incurred_cost_usd, rec.cost_status
        r.timings.generation_ms = rec.latency_ms
        ftype = FailureType.INFRA if rec.status == "budget_refused" else FailureType.API_ERROR
        raise _Stop(StageStatus.INFRA_ERROR, ftype, f"model call failed ({rec.status}): {rec.error}") from e
    rec = sres.result.record
    r.f["invocation_ids"] = [rec.invocation_id]
    r.f["cache_hit"] = bool(rec.from_cache)
    r.f["input_tokens"], r.f["output_tokens"] = rec.input_tokens, rec.output_tokens
    r.f["cost_usd"], r.f["cost_status"] = rec.incurred_cost_usd, rec.cost_status
    r.timings.generation_ms = None if rec.from_cache else rec.latency_ms
    r.outputs.append(_write(stage_dir / "response.txt", sres.result.text))
    if sres.result.reasoning:
        r.outputs.append(_write(stage_dir / "reasoning.txt", sres.result.reasoning))
    if sres.parsed is None:
        r.f["parse_ok"] = False
        r.f["structural_ok"] = False
        r.f["invocation_ids"].append(rec.invocation_id + ":parse")
        kind = getattr(sres.parse_error, "kind", "unknown")
        if sres.truncated:
            raise _Stop(StageStatus.FAILED, FailureType.TRUNCATED,
                        f"output hit maxTokens and could not be parsed ({kind})")
        raise _Stop(StageStatus.FAILED, FailureType.PARSE_ERROR, f"structured output not parseable ({kind}): "
                    f"{sres.parse_error}")
    r.f["parse_ok"] = True
    r.outputs.append(_dump(stage_dir / "parsed.json", sres.parsed.model_dump(mode="json")))
    return sres.parsed


def _execute(ctx: StageContext, r: _Rec, gate: GateDecision, code: str, inputs: dict[str, str],
             out_dir: Path, record_timing: bool = True) -> ExecutionResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    res = ctx.executor.execute(code, inputs, str(out_dir), ctx.resource_limits)
    if record_timing:
        r.f["execution"] = res
        r.timings.execution_ms = res.runtime_ms
    if res.status == ExecutionStatus.SANDBOX_UNAVAILABLE:
        raise _Stop(StageStatus.INFRA_ERROR, FailureType.INFRA, f"sandbox unavailable: {res.stderr[-1000:]}")
    if not gate.bypassed and res.sandbox_image != gate.image_id:
        raise _Stop(StageStatus.INFRA_ERROR, FailureType.INFRA,
                    f"executed image {res.sandbox_image!r} != verified image {gate.image_id!r}")
    return res


def _exec_failure(res: ExecutionResult) -> _Stop | None:
    if res.status == ExecutionStatus.SUCCESS:
        return None
    return _Stop(StageStatus.FAILED, _EXEC_FAIL.get(res.status, FailureType.EXECUTION_ERROR),
                 f"execution {res.status.value} (exit {res.exit_code}): {res.stderr[-1500:]}")


# Minimum structural requirements for a downstream stage to consume an artifact (contracts v1.2,
# continue_with_actual_artifact). Taken from the validators' own check names (no reference values).
CLEANING_STRUCTURAL_CHECKS = ("output_exists", "output_parses", "required_columns_present")
ANALYSIS_STRUCTURAL_CHECKS = ("findings_exists", "findings_parses", "required_keys_present")


def _structural(v: ValidationResult, names: tuple[str, ...]) -> bool:
    by = {c.name: c.passed for c in v.checks}
    return all(by.get(n) is True for n in names)


def _failed_checks(v: ValidationResult) -> str:
    return "; ".join(f"{c.name}: {c.detail}" for c in v.checks if c.mandatory and not c.passed)


def _run_guarded(r: _Rec, body) -> tuple[StageRunRecord, StageArtifacts | None]:
    try:
        return body()
    except _Stop as s:
        return r.done(s.status, s.ftype, s.detail), getattr(r, "artifacts", None)
    except Exception as e:  # noqa: BLE001 - harness failure: visible, void, never a model failure
        tb = traceback.format_exc(limit=5)
        return r.done(StageStatus.INFRA_ERROR, FailureType.INFRA, f"harness exception: {e!r}\n{tb}"), None


# ============================================================================ stages
def run_cleaning(ctx: StageContext, model_alias: str, handoff: HandoffPackage,
                 handoff_info: tuple[str, int, float], stage_dir: Path) -> StageResult:
    spec, pdir = ctx.spec, ctx.project_dir
    r = _Rec(ctx, StageId.CLEANING, model_alias, handoff_info)
    inputs = model_input_files(spec, pdir)          # allow-list: nothing else is mounted
    r.inputs += [Path(p) for p in inputs.values()]

    def body():
        gate = _gate(ctx)
        parsed: CleaningOutput = _generate(ctx, r, StageId.CLEANING, model_alias, cleaning_prompt(spec, pdir, ctx.prompt_version),
                                           stage_dir)
        r.outputs.append(_write(stage_dir / "code.py", parsed.python_code))
        out_dir = stage_dir / "output"
        res = _execute(ctx, r, gate, parsed.python_code, inputs, out_dir)
        r.outputs += sorted(Path(p) for p in res.output_files)
        _dump(stage_dir / "execution.json", res.model_dump(mode="json"))
        name = parsed.output_filename.strip()
        cleaned = out_dir / name if _SAFE_NAME.match(name) else None
        summary, limitations = None, []
        sp = out_dir / "cleaning_summary.json"
        if sp.is_file() and sp.stat().st_size <= _MAX_SUMMARY_FILE:
            try:
                summary = json.loads(sp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                limitations.append("cleaning_summary.json is not valid JSON")
        else:
            limitations.append("cleaning_summary.json missing or too large")
        t0 = time.perf_counter()
        v = validate_cleaning(cleaned, pdir)
        r.timings.validation_ms = (time.perf_counter() - t0) * 1000
        r.f["validation"] = v
        r.f["structural_ok"] = cleaned is not None and _structural(v, CLEANING_STRUCTURAL_CHECKS)
        _dump(stage_dir / "validation.json", v.model_dump(mode="json"))
        stop = _exec_failure(res)
        if stop is None and cleaned is None:
            stop = _Stop(StageStatus.FAILED, FailureType.INVALID_OUTPUT, f"unsafe output_filename {name!r}")
        if stop is None and not v.hard_pass:
            stop = _Stop(StageStatus.FAILED, FailureType.VALIDATION_FAILED, _failed_checks(v))
        r.artifacts = StageArtifacts(
            stage=StageId.CLEANING, model_alias=model_alias, parsed_output=parsed.model_dump(mode="json"),
            executed_code=parsed.python_code,
            files={k: str(p) for k, p in (("cleaned_csv", cleaned), ("cleaning_summary", sp))
                   if p is not None and p.is_file()},
            verified_results={"cleaning_summary": summary,
                              "cleaned_csv_sha256": hash_file(cleaned) if cleaned and cleaned.is_file() else None},
            validation_status=status_string(stop is None),
            limitations=limitations)
        if stop:
            raise stop
        return r.done(StageStatus.PASSED), r.artifacts

    rec, art = _run_guarded(r, body)
    return StageResult(rec, art)


def run_analysis(ctx: StageContext, model_alias: str, handoff: HandoffPackage,
                 handoff_info: tuple[str, int, float], stage_dir: Path, cleaned_csv: str | Path) -> StageResult:
    """`cleaned_csv` is the ACTUAL upstream cleaned file (or, in Experiment A, the canonical one)."""
    spec, pdir = ctx.spec, ctx.project_dir
    r = _Rec(ctx, StageId.ANALYSIS, model_alias, handoff_info)
    cleaned_csv = Path(cleaned_csv)
    r.inputs.append(cleaned_csv)

    def body():
        gate = _gate(ctx)
        parsed: AnalysisOutput = _generate(ctx, r, StageId.ANALYSIS, model_alias,
                                           analysis_prompt(spec, handoff, cleaned_csv, ctx.prompt_version), stage_dir)
        r.outputs.append(_write(stage_dir / "code.py", parsed.python_code))
        out_dir = stage_dir / "output"
        inputs = {spec.cleaned_data_filename: str(cleaned_csv)}
        res = _execute(ctx, r, gate, parsed.python_code, inputs, out_dir)
        r.outputs += sorted(Path(p) for p in res.output_files)
        _dump(stage_dir / "execution.json", res.model_dump(mode="json"))
        findings_path = out_dir / spec.findings_filename
        second = None
        if ctx.reproducibility_rerun and res.status == ExecutionStatus.SUCCESS:
            rerun_dir = stage_dir / "output_rerun"
            res2 = _execute(ctx, r, gate, parsed.python_code, inputs, rerun_dir, record_timing=False)
            _dump(stage_dir / "execution_rerun.json", res2.model_dump(mode="json"))
            second = rerun_dir / spec.findings_filename
        t0 = time.perf_counter()
        v = validate_analysis(findings_path, pdir, second_findings=second)
        cond_ref = conditional_reference_metrics(pdir, cleaned_csv)
        cv = (validate_analysis(findings_path, pdir, second_findings=second, reference_metrics=cond_ref)
              if cond_ref is not None else None)
        r.timings.validation_ms = (time.perf_counter() - t0) * 1000
        r.f["validation"], r.f["conditional_validation"] = v, cv
        r.f["structural_ok"] = _structural(v, ANALYSIS_STRUCTURAL_CHECKS)
        _dump(stage_dir / "validation.json", v.model_dump(mode="json"))
        if cv is not None:
            _dump(stage_dir / "conditional_validation.json", cv.model_dump(mode="json"))
            _dump(stage_dir / "conditional_reference_metrics.json", cond_ref)
        findings = None
        if findings_path.is_file():
            try:
                obj = json.loads(findings_path.read_text(encoding="utf-8"))
                findings = obj if isinstance(obj, dict) else None
            except (json.JSONDecodeError, UnicodeDecodeError):
                findings = None
        stop = _exec_failure(res)
        if stop is None and not v.hard_pass:
            stop = _Stop(StageStatus.FAILED, FailureType.VALIDATION_FAILED, _failed_checks(v))
        r.artifacts = StageArtifacts(
            stage=StageId.ANALYSIS, model_alias=model_alias, parsed_output=parsed.model_dump(mode="json"),
            executed_code=parsed.python_code,
            files={"findings": str(findings_path)} if findings_path.is_file() else {},
            verified_results={"findings": findings} if findings is not None else {},
            validation_status=status_string(stop is None),
            limitations=[])
        if stop:
            raise stop
        return r.done(StageStatus.PASSED), r.artifacts

    rec, art = _run_guarded(r, body)
    return StageResult(rec, art)


def render_report_text(rep: ReportOutput) -> str:
    lines = [f"# {rep.title}", "", rep.executive_summary, "", "## Key findings"]
    for kf in rep.key_findings:
        lines.append(f"- [{kf.finding_id}] {kf.statement}")
        values = ", ".join(f"{key}={value}" for key, value in kf.reported_values.items())
        lines.append(f"  - Reported values: {values}")
        if kf.direction is not None:
            lines.append(f"  - Direction: {kf.direction}")
        if kf.ranking is not None:
            lines.append(f"  - Ranking: {', '.join(kf.ranking)}")
        for dv in kf.derived_values:
            lines.append(f"  - Derived {dv.kind}({', '.join(dv.operands)}): {dv.value}")
    lines += ["", "## Limitations"] + [f"- {l}" for l in rep.limitations] + ["", "## Conclusion", rep.conclusion]
    return "\n".join(lines) + "\n"


def run_reporting(ctx: StageContext, model_alias: str, handoff: HandoffPackage,
                  handoff_info: tuple[str, int, float], stage_dir: Path, findings_path: str | Path,
                  *, conditional_basis: bool = True) -> StageResult:
    """`findings_path` is the ACTUAL upstream findings.json (Experiment A: canonical findings)."""
    spec, pdir = ctx.spec, ctx.project_dir
    r = _Rec(ctx, StageId.REPORTING, model_alias, handoff_info)
    findings_path = Path(findings_path)
    r.inputs.append(findings_path)

    def body():
        upstream = json.loads(findings_path.read_text(encoding="utf-8"))
        parsed: ReportOutput = _generate(ctx, r, StageId.REPORTING, model_alias,
                                         reporting_prompt(spec, handoff, upstream, ctx.prompt_version), stage_dir)
        out_dir = stage_dir / "output"
        r.f["structural_ok"] = True          # parsed as ReportOutput
        r.outputs.append(_dump(out_dir / "report.json", parsed.model_dump(mode="json")))
        r.outputs.append(_write(out_dir / "report.md", render_report_text(parsed)))
        t0 = time.perf_counter()
        cleaning_counts = ctx.ground_truth["cleaning"]["rule_log"]
        validator = validate_reporting_v3 if PROTOCOLS[ctx.protocol]["reporting_validator"] == "v3" else validate_reporting
        v = validator(parsed, ctx.ground_truth["analysis"]["metrics"], spec,
                      quality_basis="ground_truth", cleaning_counts=cleaning_counts)
        cv = (validator(parsed, upstream, spec, quality_basis="conditional_reference")
              if conditional_basis else None)
        r.timings.validation_ms = (time.perf_counter() - t0) * 1000
        r.f["validation"], r.f["conditional_validation"] = v, cv
        _dump(stage_dir / "validation.json", v.model_dump(mode="json"))
        if cv is not None:
            _dump(stage_dir / "conditional_validation.json", cv.model_dump(mode="json"))
        stop = None if v.hard_pass else _Stop(StageStatus.FAILED, FailureType.VALIDATION_FAILED, _failed_checks(v))
        r.artifacts = StageArtifacts(
            stage=StageId.REPORTING, model_alias=model_alias, parsed_output=parsed.model_dump(mode="json"),
            executed_code=None, files={"report_json": str(out_dir / "report.json"),
                                       "report_md": str(out_dir / "report.md")},
            verified_results={}, validation_status=status_string(stop is None))
        if stop:
            raise stop
        return r.done(StageStatus.PASSED), r.artifacts

    rec, art = _run_guarded(r, body)
    return StageResult(rec, art)
