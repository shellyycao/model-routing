"""Execute the approved price-matched-v2 compatibility pilot or re-pilot.

Safe default (no client, no call):
  .venv/bin/python -m experiments.run_price_matched_v2_pilot

The original nine-slot pilot and six-slot re-pilot have both completed. This
entry point is now plan/audit-only; it exposes no paid execution flag.

The exact six-call re-pilot uses the existing shared ledger and its $15 hard cap.
The later benchmark opens that same ledger with its $100 cap, so all pilot spend is
included. BedrockClient's default retry policy is unchanged: at most five attempts,
retrying transient errors only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from experiments import run_price_matched_v2 as protocol
from src.bedrock.client import BedrockClient, estimate_input_tokens_upper
from src.bedrock.usage import InvocationContext, UsageLimits


REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "results/raw/price_matched_v2_pilot"
RECORDS = OUT_DIR / "records.jsonl"
INVOCATIONS = OUT_DIR / "invocations.jsonl"
REPILOT_RECORDS = OUT_DIR / "repilot_records.jsonl"
REPILOT_INVOCATIONS = OUT_DIR / "repilot_invocations.jsonl"
REPILOT_SUMMARY = OUT_DIR / "repilot_summary.json"
SHARED_LEDGER = protocol.LEDGER
PILOT_CAP_USD = 15.0
TOTAL_CAP_USD = protocol.HARD_CAP_USD
INITIAL_LOGICAL_CALLS = 9
REPILOT_LOGICAL_CALLS = 6
TOTAL_APPROVED_LOGICAL_CALLS = INITIAL_LOGICAL_CALLS + REPILOT_LOGICAL_CALLS
RETRY_MAX_ATTEMPTS = 5  # unchanged BedrockClient default

ClientFactory = Callable[[UsageLimits, Path, Path], Any]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _with_ids(raw_calls: list[dict[str, Any]], *, protocol_name: str) -> list[dict[str, Any]]:
    calls = []
    for index, call in enumerate(raw_calls):
        identity = {
            "protocol": protocol_name,
            "index": index,
            "task": call["task"],
            "case_id": call["synthetic_case_id"],
            "model_alias": call["model_alias"],
        }
        calls.append({
            **call,
            "plan_index": index,
            "run_id": hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest(),
        })
    return calls


def _common_plan(protocol_name: str, calls: list[dict[str, Any]], status: str, order: str) -> dict[str, Any]:
    return {
        "protocol": protocol_name,
        "status": status,
        "logical_call_cap": len(calls),
        "retry_policy": {
            "source": "BedrockClient default",
            "max_attempts": RETRY_MAX_ATTEMPTS,
            "parameter_errors_retryable": False,
        },
        "budget": {
            "pilot_hard_cap_usd": PILOT_CAP_USD,
            "overall_hard_cap_usd": TOTAL_CAP_USD,
            "shared_ledger": str(SHARED_LEDGER.relative_to(REPO)),
            "pilot_spend_counts_toward_overall": True,
            "ledger_spent_usd_before_repilot": 0.6337099999999999,
        },
        "order": order,
        "calls": calls,
    }


def plan() -> dict[str, Any]:
    """Immutable historical plan used by the already-completed initial pilot."""
    calls = _with_ids(
        protocol.initial_pilot_calls(), protocol_name="price-matched-v2-compatibility-pilot"
    )
    if len(calls) != INITIAL_LOGICAL_CALLS:
        raise ValueError("initial pilot must contain exactly nine approved logical calls")
    return _common_plan(
        "price-matched-v2-compatibility-pilot",
        calls,
        "executed_2026-11-18",
        "task a1/a2/a3, then model sonnet_4_6/kimi_k3/grok_4_7",
    )


def repilot_plan() -> dict[str, Any]:
    calls = _with_ids(
        protocol.repilot_calls(), protocol_name="price-matched-v2-compatibility-repilot"
    )
    expected = [
        (task, alias)
        for task in ("a1", "a2", "a3")
        for alias in ("kimi_k3", "glm_5")
    ]
    if len(calls) != REPILOT_LOGICAL_CALLS or [
        (row["task"], row["model_alias"]) for row in calls
    ] != expected:
        raise ValueError("re-pilot must contain only the six approved Kimi K3 / GLM 5 calls")
    return _common_plan(
        "price-matched-v2-compatibility-repilot",
        calls,
        "executed_2026-11-18_6_of_6_success",
        "task a1/a2/a3, then model kimi_k3/glm_5",
    )


def usage_limits() -> UsageLimits:
    config = json.loads(protocol.PILOT.read_text())
    input_per_sweep = 0
    for task in ("a1", "a2", "a3"):
        prompt = protocol.full_prompt(task, config["cases"][task])
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        input_per_sweep += estimate_input_tokens_upper(messages, None)
    # Original three-model sweep plus the approved two-model re-pilot sweep.
    return UsageLimits(
        max_calls=TOTAL_APPROVED_LOGICAL_CALLS * RETRY_MAX_ATTEMPTS,
        max_input_tokens=input_per_sweep * 5 * RETRY_MAX_ATTEMPTS,
        max_output_tokens=TOTAL_APPROVED_LOGICAL_CALLS * RETRY_MAX_ATTEMPTS * protocol.MAX_TOKENS,
        max_budget_usd=PILOT_CAP_USD,
    )


def _default_client_factory(limits: UsageLimits, ledger: Path, log: Path) -> BedrockClient:
    return BedrockClient(
        registry=protocol._registry(),
        limits=limits,
        ledger_path=ledger,
        log_path=log,
        cache_dir=None,
        # Do not pass RetryPolicy: this intentionally reuses the existing default.
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _effective_parameters(call: dict[str, Any]) -> dict[str, Any]:
    parameters: dict[str, Any] = {"maxTokens": protocol.MAX_TOKENS}
    if call.get("temperature") is not None:
        parameters["temperature"] = call["temperature"]
    return parameters


def _is_parameter_failure(error: dict[str, Any] | None) -> bool:
    if not error:
        return False
    code = str(error.get("code") or error.get("type") or "").casefold()
    message = str(error.get("message") or "").casefold()
    if code == "paramvalidationerror":
        return True
    parameter_words = ("parameter", "inferenceconfig", "temperature", "maxtokens")
    return code == "validationexception" and any(word in message for word in parameter_words)


def _record_base(protocol_name: str, call: dict[str, Any]) -> dict[str, Any]:
    return {
        "protocol": protocol_name,
        "plan_index": call["plan_index"],
        "run_id": call["run_id"],
        "task": call["task"],
        "synthetic_case_id": call["synthetic_case_id"],
        "model_alias": call["model_alias"],
        "model_id": call["callable_model_id"],
        "quality_inspected": False,
    }


def _error_record(protocol_name: str, call: dict[str, Any], error: Exception) -> tuple[dict[str, Any], bool]:
    invocation = getattr(error, "record", None)
    raw_error = getattr(invocation, "error", None) or {
        "type": type(error).__name__, "message": str(error)[:2000]
    }
    parameter_failure = _is_parameter_failure(raw_error)
    return ({
        **_record_base(protocol_name, call),
        "status": "parameter_error" if parameter_failure else "error",
        "success": False,
        "error": raw_error,
        "raw_usage": None,
        "input_tokens": getattr(invocation, "input_tokens", None),
        "output_tokens": getattr(invocation, "output_tokens", None),
        "reasoning_tokens": None,
        "effective_parameters": (
            getattr(invocation, "inference_settings", None) or _effective_parameters(call)
        ),
        "stopReason": getattr(invocation, "stop_reason", None),
        "schema_parsed": False,
        "latency_ms": getattr(invocation, "latency_ms", None),
        "cost_usd": getattr(invocation, "incurred_cost_usd", None),
        "invocation_id": getattr(invocation, "invocation_id", None),
        "parameter_failure": parameter_failure,
        "recorded_at": now(),
    }, parameter_failure)


def _success_record(protocol_name: str, call: dict[str, Any], structured: Any) -> dict[str, Any]:
    result, invocation = structured.result, structured.result.record
    usage = result.raw_response.get("usage") or {}
    parsed = structured.parsed is not None
    return {
        **_record_base(protocol_name, call),
        "status": "success" if parsed else "parse_error",
        "success": True,
        "error": (
            {"type": "StructuredOutputError", "message": str(structured.parse_error)}
            if structured.parse_error else None
        ),
        "raw_usage": usage,
        "input_tokens": usage.get("inputTokens", invocation.input_tokens),
        "output_tokens": usage.get("outputTokens", invocation.output_tokens),
        "reasoning_tokens": protocol.reasoning_tokens_from_usage(usage),
        "effective_parameters": invocation.inference_settings,
        "stopReason": result.raw_response.get("stopReason", invocation.stop_reason),
        "schema_parsed": parsed,
        "latency_ms": invocation.latency_ms,
        "cost_usd": invocation.incurred_cost_usd,
        "invocation_id": invocation.invocation_id,
        "parameter_failure": False,
        "response_sha256": hashlib.sha256((result.text or "").encode()).hexdigest(),
        "recorded_at": now(),
    }


def _summary(
    *, protocol_name: str, planned_slots: int, attempted: int,
    rows: list[dict[str, Any]], blocked_models: dict[str, dict[str, Any]],
    ledger_path: Path, records_path: Path,
) -> dict[str, Any]:
    return {
        "protocol": protocol_name,
        "status": "complete" if len(rows) == planned_slots else "partial",
        "planned_slots": planned_slots,
        "logical_calls_attempted_this_run": attempted,
        "total_attempted_records": sum(row["status"] != "skipped_model_parameter_failure" for row in rows),
        "successes": sum(row["status"] == "success" for row in rows),
        "parse_errors": sum(row["status"] == "parse_error" for row in rows),
        "errors": sum(row["status"] in {"error", "parameter_error"} for row in rows),
        "skipped_after_parameter_failure": sum(
            row["status"] == "skipped_model_parameter_failure" for row in rows
        ),
        "blocked_models": blocked_models,
        "quality_inspected": False,
        "pilot_hard_cap_usd": PILOT_CAP_USD,
        "overall_hard_cap_usd": TOTAL_CAP_USD,
        "shared_ledger": str(ledger_path),
        "records": str(records_path),
    }


def _execute(
    approved_plan: dict[str, Any], *, client_factory: ClientFactory,
    records_path: Path, invocations_path: Path, summary_path: Path, ledger_path: Path,
) -> dict[str, Any]:
    calls = approved_plan["calls"]
    cap = approved_plan["logical_call_cap"]
    existing = _read_jsonl(records_path)
    by_index = {int(row["plan_index"]): row for row in existing}
    if set(by_index) - set(range(cap)):
        raise RuntimeError("record file contains a slot outside the approved plan")

    recorded_run_ids = {row["run_id"] for row in existing}
    orphaned = {
        ((row.get("context") or {}).get("run_id"))
        for row in _read_jsonl(invocations_path)
        if row.get("status") != "parse_error"
    } - recorded_run_ids - {None}
    if orphaned:
        raise RuntimeError(f"unreconciled pilot invocation(s); refusing repeats: {sorted(orphaned)}")

    blocked_models = {
        row["model_alias"]: row["error"]
        for row in existing
        if row.get("status") == "parameter_error" and row.get("parameter_failure")
    }
    attempted = 0
    client = None
    config = json.loads(protocol.PILOT.read_text())
    for call in calls:
        if call["plan_index"] in by_index:
            continue
        if call["model_alias"] in blocked_models:
            row = {
                **_record_base(approved_plan["protocol"], call),
                "status": "skipped_model_parameter_failure",
                "success": False,
                "error": blocked_models[call["model_alias"]],
                "raw_usage": None,
                "input_tokens": None,
                "output_tokens": None,
                "reasoning_tokens": None,
                "effective_parameters": _effective_parameters(call),
                "stopReason": None,
                "schema_parsed": False,
                "latency_ms": None,
                "cost_usd": 0.0,
                "invocation_id": None,
                "parameter_failure": True,
                "recorded_at": now(),
            }
            _append(records_path, row)
            by_index[call["plan_index"]] = row
            continue

        if attempted >= cap:
            raise RuntimeError("pilot logical-call cap reached")
        if client is None:
            limits = usage_limits()
            if limits.max_budget_usd != PILOT_CAP_USD:
                raise AssertionError("pilot dollar cap changed")
            client = client_factory(limits, ledger_path, invocations_path)
        context = InvocationContext(
            experiment_id=approved_plan["protocol"],
            run_id=call["run_id"],
            stage_id=call["task"],
            prompt_version="independent_v2_2_pilot",
            repeat_index=0,
        )
        prompt = protocol.render(call["task"], config["cases"][call["task"]])
        attempted += 1
        try:
            structured = client.converse_structured(
                call["model_alias"], prompt, protocol.SCHEMAS[call["task"]],
                context=context, use_cache=False, max_tokens=protocol.MAX_TOKENS,
            )
            row = _success_record(approved_plan["protocol"], call, structured)
        except Exception as error:
            row, parameter_failure = _error_record(approved_plan["protocol"], call, error)
            if parameter_failure:
                blocked_models[call["model_alias"]] = row["error"]
        _append(records_path, row)
        by_index[call["plan_index"]] = row

    rows = [by_index[index] for index in sorted(by_index)]
    summary = _summary(
        protocol_name=approved_plan["protocol"], planned_slots=cap, attempted=attempted,
        rows=rows, blocked_models=blocked_models, ledger_path=ledger_path,
        records_path=records_path,
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def execute_repilot(
    *, client_factory: ClientFactory = _default_client_factory,
    output_dir: Path = OUT_DIR, ledger_path: Path = SHARED_LEDGER,
) -> dict[str, Any]:
    """Run or safely resume only the six user-approved re-pilot slots."""
    return _execute(
        repilot_plan(), client_factory=client_factory,
        records_path=output_dir / "repilot_records.jsonl",
        invocations_path=output_dir / "repilot_invocations.jsonl",
        summary_path=output_dir / "repilot_summary.json",
        ledger_path=ledger_path,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args(argv)
    planned = {"initial_pilot": plan(), "completed_repilot": repilot_plan()}
    print(json.dumps(planned, indent=2, sort_keys=True))
    print("PLAN/AUDIT ONLY: both pilots are complete; no AWS client created and no model call made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
