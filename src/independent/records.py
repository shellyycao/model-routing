"""IndependentTaskRecord: the result record for A1-A3 (NOT a src.contracts type; never read by routing)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from . import INDEPENDENT_SCHEMA_VERSION


class IndependentTaskRecord(BaseModel):
    schema_version: str = INDEPENDENT_SCHEMA_VERSION
    record_kind: Literal["independent_task"] = "independent_task"
    run_id: str
    experiment_id: str
    task: Literal["a1", "a2", "a3"]
    case_id: str
    model_alias: str
    model_id: str
    repeat_index: int = 0
    prompt_version: str
    prompt_hash: str
    dataset_version: str
    case_hash: str
    config_hash: str
    invocation_ids: list[str] = Field(default_factory=list)
    status: Literal["passed", "failed", "void_infra"]
    failure_type: str | None = None          # parse_error | truncated | execution_error | timeout | validation_failed | infra
    failure_detail: str | None = None
    parse_ok: bool | None = None
    truncated: bool | None = None
    execution: dict | None = None            # A1 sandbox ExecutionResult (status, runtime_ms, sandbox_image)
    scores: dict = Field(default_factory=dict)
    generation_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None       # provider-reported subset of billed outputTokens, when available
    reasoning_chars: int | None = None
    cost_usd: float | None = None
    cost_status: str = "unavailable"
    artifacts: list[str] = Field(default_factory=list)
    started_at: str
    finished_at: str | None = None
