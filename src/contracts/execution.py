"""Sandbox execution and validation interfaces (implemented by Benchmark)."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from .ids import StageId


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    TEST_FAILURE = "test_failure"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    INVALID_OUTPUT = "invalid_output"
    SECURITY_VIOLATION = "security_violation"
    SANDBOX_UNAVAILABLE = "sandbox_unavailable"   # infra problem, not a model failure


class ResourceLimits(BaseModel):
    timeout_s: int = 120
    memory_mb: int = 1024
    cpus: float = 1.0
    network: bool = False          # must stay False for model-generated code


class ExecutionResult(BaseModel):
    status: ExecutionStatus
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    runtime_ms: float | None = None
    output_files: list[str] = Field(default_factory=list)   # paths on host after copy-out
    sandbox_image: str | None = None                       # image digest for provenance


class Executor(Protocol):
    def execute(self, code: str, inputs: dict[str, str], output_dir: str,
                limits: ResourceLimits | None = None) -> ExecutionResult:
        """Run untrusted code in isolation. `inputs` maps in-sandbox filename -> host path
        (mounted read-only). Writes only to `output_dir`. No credentials, no network."""
        ...


class CheckResult(BaseModel):
    name: str
    passed: bool
    mandatory: bool                 # mandatory checks gate feasibility
    detail: str = ""
    value: float | None = None


class ValidationResult(BaseModel):
    stage: StageId
    hard_pass: bool                 # all mandatory checks passed
    checks: list[CheckResult]
    quality: dict[str, float] = Field(default_factory=dict)  # stage quality metrics (see records.QUALITY_METRICS)
    # v1.1: what the quality was measured against.
    #   ground_truth          - the project's fixed reference (used for Experiment A and headline quality)
    #   conditional_reference - the reference recomputed from the ACTUAL upstream artifact this stage
    #                           received; separates "this stage did its job" from "upstream error propagated"
    quality_basis: Literal["ground_truth", "conditional_reference"] = "ground_truth"
    validator_version: str = "1.0"
