"""Invocation records, cost estimation, and budget tracking.

Raw invocation records are append-only JSONL. Derived metrics must be computed from
these records, never stored in place of them.

Aggregating the log (read this before summing anything):
- Paid usage = records with from_cache == False and status != "parse_error".
- Sum `incurred_cost_usd` (None = unknown, never 0) — not `cost_usd`, which on a cache
  hit repeats the ORIGINAL generation cost for reference.
- Cache hits keep the original tokens for reference; `original_latency_ms` holds the
  original call's latency and `latency_ms` is the (near-zero) cache lookup time.
- `parse_error` records are events attached to a parent call (`parent_invocation_id`);
  their token/latency/cost fields are null so they never double count.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal

from pydantic import BaseModel, Field

from .models import Pricing

try:  # POSIX advisory file locks (macOS/Linux); absent on Windows
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

InvocationStatus = Literal[
    "success", "api_error", "throttled_exhausted", "budget_refused", "parse_error", "client_error",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def estimate_cost(pricing: Pricing, input_tokens: int | None, output_tokens: int | None) -> float | None:
    """Return USD cost, or None when pricing is unverified or a token count is unknown
    (never guessed, never $0)."""
    if not pricing.verified or input_tokens is None or output_tokens is None:
        return None
    return input_tokens / 1e6 * pricing.input_per_mtok + output_tokens / 1e6 * pricing.output_per_mtok


class InvocationContext(BaseModel):
    """Experimental provenance attached to every model call."""

    experiment_id: str = "adhoc"
    run_id: str | None = None          # e.g. from src.bedrock.provenance.make_run_id
    project_id: str | None = None
    path_id: str | None = None
    stage_id: str | None = None
    prompt_version: str | None = None
    repeat_index: int | None = None   # set for stochasticity repeats (which must bypass the cache)
    input_artifacts: list[str] = Field(default_factory=list)


class AttemptLog(BaseModel):
    """One failed API attempt (successful final attempts are described by the record)."""

    attempt: int                      # 0-based
    code: str
    retryable: bool
    backoff_ms: float | None = None   # sleep before the next attempt (None if no retry followed)


class InvocationRecord(BaseModel):
    invocation_id: str
    request_hash: str
    timestamp: str
    context: InvocationContext
    model_alias: str
    model_id: str
    base_model_id: str
    inference_settings: dict
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_chars: int | None = None
    latency_ms: float | None = None            # client wall clock, incl. pacing, retries and backoff
    server_latency_ms: float | None = None     # Bedrock-reported latency of final attempt
    cost_usd: float | None = None              # generation cost (on a cache hit: the ORIGINAL call's)
    cost_status: Literal["estimated", "unavailable", "not_incurred"] = "unavailable"
    retry_count: int = 0
    status: InvocationStatus
    stop_reason: str | None = None
    from_cache: bool = False
    cached_from: str | None = None              # invocation_id of the original paid call
    output_artifacts: list[str] = Field(default_factory=list)
    validation_status: str | None = None
    error: dict | None = None
    # ---- additive fields (M1.1) ----
    truncated: bool = False                     # stop_reason == "max_tokens": output was cut off
    incurred_cost_usd: float | None = None      # cost incurred by THIS record (0 for cache hits/events)
    attempts: list[AttemptLog] = Field(default_factory=list)  # failed attempts, in order
    backoff_ms: float | None = None             # total retry backoff sleep (part of latency_ms)
    rate_limit_wait_ms: float | None = None     # total client-side pacing wait (part of latency_ms)
    final_attempt_latency_ms: float | None = None  # client wall clock of the final API attempt only
    original_latency_ms: float | None = None    # cache hits: latency_ms of the original call
    cache_namespace: str | None = None          # cache scope (default: context.experiment_id)
    parent_invocation_id: str | None = None     # parse_error events: the call they belong to


class UsageLogger:
    """Thread-safe append-only JSONL writer for invocation records."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def write(self, record: InvocationRecord) -> None:
        line = record.model_dump_json()
        with self._lock, self.path.open("a") as f:
            f.write(line + "\n")

    def read_all(self) -> list[InvocationRecord]:
        if not self.path.exists():
            return []
        return [InvocationRecord.model_validate_json(l) for l in self.path.read_text().splitlines() if l.strip()]


class BudgetExceeded(RuntimeError):
    pass


class UsageLimits(BaseModel):
    """Hard limits. Call and token limits are ALWAYS enforced. `max_calls` counts API
    attempts (retries and failed attempts included). The dollar limit is enforced only
    for calls whose price is verified; while any model is unpriced the dollar guard is
    reported as inactive, never as functional."""

    max_calls: int = 50
    max_input_tokens: int = 200_000
    max_output_tokens: int = 100_000
    max_budget_usd: float | None = None


@dataclass
class Reservation:
    """Worst-case usage held in the ledger by an in-flight call until settled/released."""

    id: str
    calls: int                 # call slots held (1 + extra retry attempts admitted)
    input_tokens: int          # conservative amount reserved per API attempt
    output_tokens: int         # conservative amount reserved per API attempt
    usd: float                 # conservative amount reserved per API attempt
    priced: bool               # whether `usd` came from verified pricing
    attempts_made: int = 0     # API attempts actually sent (set by the caller)
    active: bool = True


_TOTAL_KEYS = ("calls", "input_tokens", "output_tokens", "spent_usd_priced", "unpriced_calls",
               "failed_attempts", "unknown_usage_calls")


def _pid_alive(pid: int) -> bool:
    if pid == os.getpid():
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class CostTracker:
    """Persistent usage ledger enforcing hard call/token limits and (when prices are
    verified) a dollar limit. Missing prices are never counted as $0: calls without a
    verified price are tallied in `unpriced_calls` and their tokens are still counted.

    Concurrency (threads AND processes sharing one ledger file):
    every operation is a read-modify-write of the ledger under a thread lock plus an
    exclusive `fcntl` lock on `<ledger>.lock`. A call first `reserve()`s its worst case
    (1 call, estimated input tokens, full maxTokens, worst-case USD) as a `pending` entry
    in the ledger; limits are checked against settled + pending usage, so concurrent
    callers cannot jointly overshoot. The call is then `settle()`d with actual usage or
    `release()`d. Pending entries of dead processes (same host) are dropped on the next
    operation.

    Accounting: `calls` counts API attempts (failed attempts included, also counted in
    `failed_attempts`). A successful response without a usage block is charged its
    reserved worst-case tokens (`unknown_usage_calls`). Failed attempts and successful
    responses with missing usage are conservatively charged their per-attempt token and
    dollar reservation so retries cannot bypass a hard budget.
    """

    def __init__(self, ledger_path: str | Path, limits: UsageLimits, *, all_models_priced: bool | None = None):
        self.ledger_path = Path(ledger_path)
        self.lock_path = self.ledger_path.with_name(self.ledger_path.name + ".lock")
        self.limits = limits
        # Registry-level pricing state; False keeps the dollar guard reported inactive.
        self.all_models_priced = all_models_priced
        self._lock = threading.RLock()
        self._state: dict = self._read()

    # ------------------------------------------------------------- persistence
    def _read(self) -> dict:
        d = json.loads(self.ledger_path.read_text()) if self.ledger_path.exists() else {}
        state = {k: d.get(k, 0) for k in _TOTAL_KEYS}
        state["spent_usd_priced"] = float(state["spent_usd_priced"])
        state["pending"] = dict(d.get("pending") or {})
        return state

    def _write(self) -> None:
        s = self._state
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {k: s[k] for k in _TOTAL_KEYS}
        payload.update({
            "pending": s["pending"],
            "dollar_guard_active": self.dollar_guard_active,
            "limits": self.limits.model_dump(),
            "note": "spent_usd_priced covers priced calls only; unpriced calls are NOT $0. "
                    "calls counts API attempts, including failed ones.",
            "updated": utc_now(),
        })
        tmp = self.ledger_path.with_name(f"{self.ledger_path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        os.replace(tmp, self.ledger_path)

    @contextmanager
    def _locked(self, write: bool = True) -> Iterator[dict]:
        with self._lock:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with self.lock_path.open("a+") as lf:
                if fcntl is not None:
                    fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
                try:
                    self._state = self._read()
                    pend = self._state["pending"]
                    stale = [k for k, v in pend.items() if not _pid_alive(int(v.get("pid", -1)))]
                    for k in stale:
                        del pend[k]
                    yield self._state
                    if write or stale:
                        self._write()
                finally:
                    if fcntl is not None:
                        fcntl.flock(lf.fileno(), fcntl.LOCK_UN)

    # ------------------------------------------------------------- views
    def _get(self, key: str):
        return self._state[key]

    calls = property(lambda self: self._get("calls"))
    input_tokens = property(lambda self: self._get("input_tokens"))
    output_tokens = property(lambda self: self._get("output_tokens"))
    spent_usd_priced = property(lambda self: self._get("spent_usd_priced"))
    unpriced_calls = property(lambda self: self._get("unpriced_calls"))
    failed_attempts = property(lambda self: self._get("failed_attempts"))
    unknown_usage_calls = property(lambda self: self._get("unknown_usage_calls"))

    def _pending_sum(self, field: str) -> float:
        return sum(v[field] for v in self._state["pending"].values())

    reserved_calls = property(lambda self: int(self._pending_sum("calls")))
    reserved_input_tokens = property(lambda self: int(self._pending_sum("input_tokens")))
    reserved_output_tokens = property(lambda self: int(self._pending_sum("output_tokens")))
    reserved_usd = property(lambda self: self._pending_sum("usd"))

    def refresh(self) -> None:
        """Reload the shared ledger (other clients/processes may have written to it)."""
        with self._locked(write=False):
            pass

    @property
    def dollar_guard_active(self) -> bool:
        return (self.limits.max_budget_usd is not None and self._state["unpriced_calls"] == 0
                and self.all_models_priced is not False)

    # ------------------------------------------------------------- limits
    def _check_locked(self, *, extra_calls: int, est_input_tokens: int, max_output_tokens: int,
                      worst_case_usd: float | None) -> None:
        L, s = self.limits, self._state
        calls = s["calls"] + self.reserved_calls
        inp = s["input_tokens"] + self.reserved_input_tokens
        out = s["output_tokens"] + self.reserved_output_tokens
        usd = s["spent_usd_priced"] + self.reserved_usd
        if calls + extra_calls > L.max_calls:
            raise BudgetExceeded(f"Call limit reached ({calls}/{L.max_calls}, incl. in-flight)")
        if inp + est_input_tokens > L.max_input_tokens:
            raise BudgetExceeded(f"Input-token limit: {inp}+~{est_input_tokens} > {L.max_input_tokens}")
        if out + max_output_tokens > L.max_output_tokens:
            raise BudgetExceeded(f"Output-token limit: {out}+{max_output_tokens} > {L.max_output_tokens}")
        if L.max_budget_usd is not None and worst_case_usd is not None:
            if usd + worst_case_usd > L.max_budget_usd:
                raise BudgetExceeded(f"Dollar limit: ${usd:.4f}+${worst_case_usd:.4f} > ${L.max_budget_usd}")

    def check(self, *, est_input_tokens: int, max_output_tokens: int, worst_case_usd: float | None) -> None:
        """Legacy check (no reservation). Prefer reserve()."""
        with self._locked(write=False):
            self._check_locked(extra_calls=1, est_input_tokens=est_input_tokens,
                               max_output_tokens=max_output_tokens, worst_case_usd=worst_case_usd)

    def reserve(self, *, est_input_tokens: int, max_output_tokens: int,
                worst_case_usd: float | None) -> Reservation:
        """Atomically check limits and hold the worst case. Raises BudgetExceeded."""
        with self._locked() as s:
            self._check_locked(extra_calls=1, est_input_tokens=est_input_tokens,
                               max_output_tokens=max_output_tokens, worst_case_usd=worst_case_usd)
            r = Reservation(
                id=uuid.uuid4().hex,
                calls=1,
                input_tokens=est_input_tokens,
                output_tokens=max_output_tokens,
                usd=worst_case_usd or 0.0,
                priced=worst_case_usd is not None,
            )
            s["pending"][r.id] = {"calls": 1, "input_tokens": r.input_tokens, "output_tokens": r.output_tokens,
                                  "usd": r.usd, "pid": os.getpid(), "created": utc_now()}
            return r

    def reserve_attempt(self, reservation: Reservation) -> None:
        """Reserve the full per-attempt worst case for one retry, or refuse it."""
        with self._locked() as s:
            self._check_locked(
                extra_calls=1,
                est_input_tokens=reservation.input_tokens,
                max_output_tokens=reservation.output_tokens,
                worst_case_usd=reservation.usd if reservation.priced else None,
            )
            reservation.calls += 1
            if reservation.id in s["pending"]:
                pending = s["pending"][reservation.id]
                pending["calls"] = reservation.calls
                pending["input_tokens"] += reservation.input_tokens
                pending["output_tokens"] += reservation.output_tokens
                pending["usd"] += reservation.usd

    @staticmethod
    def _charge_unknown_attempts_locked(state: dict, reservation: Reservation, count: int) -> None:
        """Conservatively settle attempts whose provider-side usage is unknowable."""
        if count <= 0:
            return
        state["calls"] += count
        state["failed_attempts"] += count
        state["unknown_usage_calls"] += count
        state["input_tokens"] += reservation.input_tokens * count
        state["output_tokens"] += reservation.output_tokens * count
        if reservation.priced:
            state["spent_usd_priced"] += reservation.usd * count
        else:
            state["unpriced_calls"] += count

    def release(self, reservation: Reservation) -> None:
        """End a reservation without a usable response. Every attempt actually sent
        (`reservation.attempts_made`) is counted as a failed call with unknown tokens.
        Idempotent."""
        with self._locked() as s:
            if not reservation.active:
                return
            reservation.active = False
            s["pending"].pop(reservation.id, None)
            self._charge_unknown_attempts_locked(s, reservation, reservation.attempts_made)

    def settle(self, reservation: Reservation, *, input_tokens: int | None, output_tokens: int | None,
               cost_usd: float | None) -> None:
        """Replace a reservation with the actual usage of a completed call. Unknown token
        counts are charged at the reserved worst case."""
        with self._locked() as s:
            if not reservation.active:
                raise RuntimeError("reservation already settled or released")
            reservation.active = False
            s["pending"].pop(reservation.id, None)
            attempts = max(reservation.attempts_made, 1)
            self._charge_unknown_attempts_locked(s, reservation, attempts - 1)
            unknown = input_tokens is None or output_tokens is None
            if unknown:
                s["unknown_usage_calls"] += 1
            self._add_locked(
                input_tokens=reservation.input_tokens if input_tokens is None else input_tokens,
                output_tokens=reservation.output_tokens if output_tokens is None else output_tokens,
                cost_usd=(reservation.usd if reservation.priced else None) if unknown else cost_usd,
            )

    def _add_locked(self, *, input_tokens: int, output_tokens: int, cost_usd: float | None) -> None:
        s = self._state
        s["calls"] += 1
        s["input_tokens"] += input_tokens
        s["output_tokens"] += output_tokens
        if cost_usd is None:
            s["unpriced_calls"] += 1
        else:
            s["spent_usd_priced"] += cost_usd

    def add(self, *, input_tokens: int, output_tokens: int, cost_usd: float | None) -> None:
        """Legacy: record one completed call without a reservation."""
        with self._locked():
            self._add_locked(input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost_usd)
