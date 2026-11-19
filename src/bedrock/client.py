"""Unified Bedrock client over the Converse API.

Guarantees:
- The requested model is the model that is called. A failed call raises; it is never
  silently substituted with another model.
- Throttling and transient transport errors are retried with bounded exponential backoff
  and jitter; every failed attempt (error code, backoff) is logged on the record.
- Every call writes exactly one InvocationRecord, whatever the outcome (success, API
  error, exhausted retries, budget refusal, or any other client-side exception).
- Completed identical requests can be served from a content-addressed cache, so
  expensive experiments are not silently repeated. The cache is scoped per
  `cache_namespace` (default: context.experiment_id). Repeats (context.repeat_index set)
  must pass use_cache=False; otherwise a ValueError is raised.
- Hard limits use reserve-then-settle in a file-locked ledger, so concurrent threads and
  processes sharing a ledger cannot jointly overshoot them. `max_calls` counts attempts.
- Per-model pacing from configs/models.yaml (`concurrency:`) applies to every attempt.
- Truncation (stopReason == "max_tokens") is recorded as `truncated=True`.
- Credentials come only from the AWS profile/environment, never from code.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, TypeVar

import boto3
from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)
from pydantic import BaseModel

from .concurrency import ModelRateLimiter
from .models import ModelRegistry, ModelSpec, load_registry, REPO_ROOT
from .structured import StructuredOutputError, parse_structured, schema_instruction
from .usage import (
    AttemptLog,
    BudgetExceeded,
    CostTracker,
    UsageLimits,
    InvocationContext,
    InvocationRecord,
    Reservation,
    UsageLogger,
    estimate_cost,
    utc_now,
)

T = TypeVar("T", bound=BaseModel)

RETRYABLE_CODES = {
    "ThrottlingException",
    "TooManyRequestsException",
    "ServiceUnavailableException",
    "InternalServerException",
    "ModelNotReadyException",
}
# Transport errors that are transient and retried.
RETRYABLE_TRANSPORT = (ReadTimeoutError, EndpointConnectionError, ConnectTimeoutError, ConnectionClosedError)

# Conservative per-request input-token upper bound: one token per UTF-8 byte of text
# (BPE tokens are >= 1 byte; digits/CSV can approach 1 token per char) plus a fixed
# allowance for chat-template/system tokens.
PROMPT_TOKEN_OVERHEAD = 256


def estimate_input_tokens_upper(messages: list[dict], system: str | None) -> int:
    texts = [c.get("text", "") for m in messages for c in m["content"]] + [system or ""]
    return sum(len(t.encode("utf-8")) for t in texts) + PROMPT_TOKEN_OVERHEAD


class ModelInvocationError(RuntimeError):
    def __init__(self, record: InvocationRecord):
        super().__init__(f"{record.model_alias} ({record.model_id}) failed: {record.status} {record.error}")
        self.record = record


@dataclass
class InvocationResult:
    text: str
    reasoning: str | None
    record: InvocationRecord
    raw_response: dict = field(repr=False, default_factory=dict)

    @property
    def truncated(self) -> bool:
        return self.record.truncated


@dataclass
class StructuredResult:
    parsed: BaseModel | None
    result: InvocationResult
    parse_error: StructuredOutputError | None = None

    @property
    def truncated(self) -> bool:
        """True if the output hit maxTokens (a parse failure is then likely caused by truncation)."""
        return self.result.record.truncated


@dataclass
class RetryPolicy:
    max_attempts: int = 5
    base_delay_s: float = 1.0
    max_delay_s: float = 30.0

    def delay(self, attempt: int) -> float:
        # Full jitter, bounded.
        return random.uniform(0, min(self.max_delay_s, self.base_delay_s * 2 ** attempt))


def request_hash(model_id: str, system: str | None, messages: list[dict], inference: dict) -> str:
    payload = json.dumps(
        {"model_id": model_id, "system": system, "messages": messages, "inference": inference},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def cache_key(namespace: str, rhash: str) -> str:
    return hashlib.sha256(json.dumps({"ns": namespace, "req": rhash}, sort_keys=True).encode()).hexdigest()


Validator = Callable[[str], "str | None"]


class BedrockClient:
    def __init__(
        self,
        registry: ModelRegistry | None = None,
        *,
        runtime_client: Any | None = None,
        log_path: str | Path = REPO_ROOT / "results" / "raw" / "invocations.jsonl",
        ledger_path: str | Path = REPO_ROOT / "results" / "raw" / "cost_ledger.json",
        cache_dir: str | Path | None = REPO_ROOT / "results" / "cache",
        limits: UsageLimits | None = None,
        retry: RetryPolicy | None = None,
        sleep: Callable[[float], None] = time.sleep,
        rate_limiter: ModelRateLimiter | None = None,
    ):
        self.registry = registry or load_registry()
        if runtime_client is None:
            session = boto3.Session(profile_name=self.registry.aws_profile, region_name=self.registry.region)
            runtime_client = session.client(
                "bedrock-runtime",
                config=Config(retries={"max_attempts": 1, "mode": "standard"}, read_timeout=300),
            )
        self.rt = runtime_client
        self.logger = UsageLogger(log_path)
        self.costs = CostTracker(ledger_path, limits or UsageLimits(),
                                 all_models_priced=self.registry.pricing_status()["all_priced"])
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.retry = retry or RetryPolicy()
        self._sleep = sleep
        # Default pacing comes from configs/models.yaml `concurrency:`.
        self.rate_limiter = rate_limiter or ModelRateLimiter.from_settings(
            self.registry.concurrency, self.registry.aliases, sleep=sleep)
        self._inflight_lock = threading.Lock()
        self._inflight: dict[str, threading.Lock] = {}

    @property
    def max_workers(self) -> int:
        """Configured worker count for run_concurrent (configs/models.yaml)."""
        return self.registry.concurrency.max_workers

    # ------------------------------------------------------------------ core call
    def converse(
        self,
        model: str,
        prompt: str | list[dict],
        *,
        system: str | None = None,
        context: InvocationContext | None = None,
        use_cache: bool = True,
        max_tokens: int | None = None,
        cache_namespace: str | None = None,
    ) -> InvocationResult:
        """One logical call. `cache_namespace` scopes cache reuse (default:
        context.experiment_id); pass the same namespace explicitly to share a cache
        across experiments. Raises ValueError if a repeat (repeat_index set) would use the cache."""
        return self._converse(model, prompt, system=system, context=context, use_cache=use_cache,
                              max_tokens=max_tokens, cache_namespace=cache_namespace, validator=None)

    def _converse(self, model: str, prompt: str | list[dict], *, system: str | None,
                  context: InvocationContext | None, use_cache: bool, max_tokens: int | None,
                  cache_namespace: str | None, validator: Validator | None) -> InvocationResult:
        t_start = time.perf_counter()
        spec = self.registry.get(model)
        context = context or InvocationContext()
        if use_cache and context.repeat_index is not None:
            raise ValueError("Repeats (context.repeat_index set) must bypass the cache: pass use_cache=False")
        messages = [{"role": "user", "content": [{"text": prompt}]}] if isinstance(prompt, str) else prompt
        inference = self._inference_config(spec, max_tokens)
        rhash = request_hash(spec.model_id, system, messages, inference)
        ns = (cache_namespace or context.experiment_id) if use_cache else None

        if not use_cache:
            return self._converse_uncached(spec, messages, system, context, inference, rhash, None, validator)
        ckey = cache_key(ns, rhash)
        with self._request_lock(ckey):  # identical concurrent requests: one paid call
            if (cached := self._cache_get(ckey)) is not None:
                return self._from_cache(cached, context, ns, validator, t_start)
            return self._converse_uncached(spec, messages, system, context, inference, rhash, ns, validator)

    def _request_lock(self, key: str) -> threading.Lock:
        with self._inflight_lock:
            return self._inflight.setdefault(key, threading.Lock())

    def _converse_uncached(self, spec: ModelSpec, messages: list[dict], system: str | None,
                           context: InvocationContext, inference: dict, rhash: str,
                           ns: str | None, validator: Validator | None) -> InvocationResult:
        base = dict(
            invocation_id=str(uuid.uuid4()),
            request_hash=rhash,
            timestamp=utc_now(),
            context=context,
            model_alias=spec.alias,
            model_id=spec.model_id,
            base_model_id=spec.base_model_id,
            inference_settings=inference,
            cache_namespace=ns,
        )

        # Pre-call guard (worst case): input upper bound + full maxTokens, reserved atomically.
        est_in = estimate_input_tokens_upper(messages, system)
        worst = estimate_cost(spec.pricing, est_in, inference["maxTokens"])
        try:
            reservation = self.costs.reserve(est_input_tokens=est_in, max_output_tokens=inference["maxTokens"],
                                             worst_case_usd=worst)
        except BudgetExceeded as e:
            rec = InvocationRecord(**base, status="budget_refused", cost_status="not_incurred",
                                   incurred_cost_usd=0.0, error={"type": "BudgetExceeded", "message": str(e)})
            self.logger.write(rec)
            raise ModelInvocationError(rec) from e

        kwargs: dict[str, Any] = {"modelId": spec.model_id, "messages": messages, "inferenceConfig": inference}
        if system:
            kwargs["system"] = [{"text": system}]

        try:
            return self._call_with_retries(spec, kwargs, base, reservation, ns, validator)
        finally:
            # No-op after settle(); otherwise counts the attempts sent as failed calls.
            self.costs.release(reservation)

    def _call_with_retries(self, spec: ModelSpec, kwargs: dict, base: dict, reservation: Reservation,
                           ns: str | None, validator: Validator | None) -> InvocationResult:
        t0 = time.perf_counter()
        waited = backoff = 0.0
        attempts: list[AttemptLog] = []
        attempt = 0

        def fail(status: str, error: dict) -> InvocationRecord:
            rec = InvocationRecord(
                **base,
                latency_ms=(time.perf_counter() - t0) * 1000,
                rate_limit_wait_ms=waited * 1000,
                backoff_ms=backoff * 1000,
                retry_count=attempt,
                attempts=attempts,
                status=status,
                # A failed call may still be billed partially; not knowable here.
                cost_status="unavailable" if reservation.attempts_made else "not_incurred",
                incurred_cost_usd=None if reservation.attempts_made else 0.0,
                error=error,
            )
            self.logger.write(rec)
            return rec

        while True:
            if attempt > 0:
                try:
                    self.costs.reserve_attempt(reservation)
                except BudgetExceeded as e:
                    rec = fail("budget_refused", {"type": "BudgetExceeded", "message": str(e),
                                                  "after_attempts": reservation.attempts_made})
                    raise ModelInvocationError(rec) from e
            waited += self.rate_limiter.acquire(spec.alias)
            ta = time.perf_counter()
            reservation.attempts_made += 1
            try:
                resp = self.rt.converse(**kwargs)
                final_attempt_ms = (time.perf_counter() - ta) * 1000
                break
            except (ClientError, *RETRYABLE_TRANSPORT) as e:
                code = e.response["Error"]["Code"] if isinstance(e, ClientError) else type(e).__name__
                retryable = code in RETRYABLE_CODES or not isinstance(e, ClientError)
                if retryable and attempt + 1 < self.retry.max_attempts:
                    d = self.retry.delay(attempt)
                    attempts.append(AttemptLog(attempt=attempt, code=code, retryable=True, backoff_ms=d * 1000))
                    self._sleep(d)
                    backoff += d
                    attempt += 1
                    continue
                attempts.append(AttemptLog(attempt=attempt, code=code, retryable=retryable))
                msg = e.response["Error"].get("Message") if isinstance(e, ClientError) else str(e)
                rec = fail("throttled_exhausted" if retryable else "api_error", {"code": code, "message": msg})
                raise ModelInvocationError(rec) from e
            except Exception as e:  # anything else (ParamValidationError, bugs, ...): log, then raise
                code = type(e).__name__
                attempts.append(AttemptLog(attempt=attempt, code=code, retryable=False))
                rec = fail("client_error", {"code": code, "message": str(e)[:2000]})
                raise ModelInvocationError(rec) from e

        latency_ms = (time.perf_counter() - t0) * 1000
        text, reasoning = self._extract(resp)
        usage = resp.get("usage") or {}
        in_tok, out_tok = usage.get("inputTokens"), usage.get("outputTokens")
        cost = estimate_cost(spec.pricing, in_tok, out_tok)  # None if unpriced or usage missing
        self.costs.settle(reservation, input_tokens=in_tok, output_tokens=out_tok, cost_usd=cost)
        stop_reason = resp.get("stopReason")
        rec = InvocationRecord(
            **base,
            input_tokens=in_tok,
            output_tokens=out_tok,
            reasoning_chars=len(reasoning) if reasoning is not None else None,
            latency_ms=latency_ms,
            final_attempt_latency_ms=final_attempt_ms,
            rate_limit_wait_ms=waited * 1000,
            backoff_ms=backoff * 1000,
            server_latency_ms=(resp.get("metrics") or {}).get("latencyMs"),
            cost_usd=cost,
            incurred_cost_usd=cost,
            cost_status="estimated" if cost is not None else "unavailable",
            retry_count=attempt,
            attempts=attempts,
            status="success",
            stop_reason=stop_reason,
            truncated=stop_reason == "max_tokens",
            validation_status=validator(text) if validator else None,
            error=None if in_tok is not None and out_tok is not None else {
                "type": "MissingUsage", "message": "response had no token usage; ledger charged worst case"},
        )
        self.logger.write(rec)
        if ns is not None:  # repeats (use_cache=False) neither read nor overwrite the cache
            self._cache_put(cache_key(ns, rec.request_hash),
                            {"text": text, "reasoning": reasoning, "record": rec.model_dump()})
        return InvocationResult(text=text, reasoning=reasoning, record=rec, raw_response=resp)

    # ------------------------------------------------------------ structured call
    def converse_structured(
        self,
        model: str,
        prompt: str,
        schema: type[T],
        *,
        system: str | None = None,
        context: InvocationContext | None = None,
        use_cache: bool = True,
        max_tokens: int | None = None,
        cache_namespace: str | None = None,
    ) -> StructuredResult:
        """One call, one parse attempt. Parse failures are returned, not repaired.

        The call's record carries validation_status ("schema_valid" or
        "parse_error:<kind>") when it is written. A parse failure additionally writes a
        `parse_error` event (parent_invocation_id = the call; null tokens/latency/cost)
        whose error says whether the output was truncated at maxTokens."""
        full_prompt = f"{prompt}\n\n{schema_instruction(schema)}"
        outcome: dict[str, Any] = {}

        def validate(text: str) -> str:
            try:
                outcome["parsed"] = parse_structured(text, schema)
                return "schema_valid"
            except StructuredOutputError as e:
                outcome["error"] = e
                return f"parse_error:{e.kind}"

        result = self._converse(model, full_prompt, system=system, context=context, use_cache=use_cache,
                                max_tokens=max_tokens, cache_namespace=cache_namespace, validator=validate)
        if "error" not in outcome:
            return StructuredResult(parsed=outcome["parsed"], result=result)
        e: StructuredOutputError = outcome["error"]
        parent = result.record
        self.logger.write(parent.model_copy(update={
            "invocation_id": parent.invocation_id + ":parse",
            "parent_invocation_id": parent.invocation_id,
            "timestamp": utc_now(),
            "status": "parse_error",
            "input_tokens": None, "output_tokens": None, "reasoning_chars": None,
            "latency_ms": None, "server_latency_ms": None, "final_attempt_latency_ms": None,
            "original_latency_ms": None, "backoff_ms": None, "rate_limit_wait_ms": None,
            "attempts": [], "retry_count": 0,
            "cost_usd": None, "incurred_cost_usd": 0.0, "cost_status": "not_incurred",
            "error": {
                "kind": e.kind,
                "message": str(e)[:2000],
                "truncated": parent.truncated,
                # Distinguishes "output cut off at maxTokens" from a genuine format failure.
                "cause": "truncated_max_tokens" if parent.truncated else "model_output",
            },
        }))
        return StructuredResult(parsed=None, result=result, parse_error=e)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _inference_config(spec: ModelSpec, max_tokens: int | None) -> dict:
        cfg: dict[str, Any] = {"maxTokens": max_tokens or spec.inference.max_tokens}
        if spec.inference.temperature is not None:
            cfg["temperature"] = spec.inference.temperature
        return cfg

    @staticmethod
    def _extract(resp: dict) -> tuple[str, str | None]:
        texts, reasoning = [], []
        for block in resp.get("output", {}).get("message", {}).get("content", []):
            if "text" in block:
                texts.append(block["text"])
            elif "reasoningContent" in block:
                rt = block["reasoningContent"].get("reasoningText", {})
                reasoning.append(rt.get("text", ""))
        return "".join(texts), ("".join(reasoning) if reasoning else None)

    def _cache_get(self, key: str) -> dict | None:
        if not self.cache_dir:
            return None
        p = self.cache_dir / f"{key}.json"
        return json.loads(p.read_text()) if p.exists() else None

    def _cache_put(self, key: str, payload: dict) -> None:
        if not self.cache_dir:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        final = self.cache_dir / f"{key}.json"
        tmp = final.with_name(f"{final.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False))
        os.replace(tmp, final)  # atomic: readers never see a partial file

    def _from_cache(self, cached: dict, context: InvocationContext, ns: str,
                    validator: Validator | None, t_start: float) -> InvocationResult:
        orig = InvocationRecord.model_validate(cached["record"])
        rec = orig.model_copy(update={
            "invocation_id": str(uuid.uuid4()),
            "timestamp": utc_now(),
            "context": context,
            "from_cache": True,
            "cached_from": orig.invocation_id,
            "cache_namespace": ns,
            # cost_usd keeps the ORIGINAL generation cost for reference; nothing is incurred now.
            "cost_usd": orig.cost_usd,
            "incurred_cost_usd": 0.0,
            "cost_status": "not_incurred",
            "truncated": orig.stop_reason == "max_tokens",
            # Latency of THIS lookup; the original call's latency is kept separately.
            "latency_ms": (time.perf_counter() - t_start) * 1000,
            "original_latency_ms": orig.latency_ms,
            "server_latency_ms": None,
            "final_attempt_latency_ms": None,
            "backoff_ms": None,
            "rate_limit_wait_ms": None,
            "attempts": [],
            "retry_count": 0,
            "validation_status": validator(cached["text"]) if validator else None,
            "parent_invocation_id": None,
        })
        self.logger.write(rec)
        return InvocationResult(text=cached["text"], reasoning=cached.get("reasoning"), record=rec)
