"""M1 live smoke test: 2 small calls per study model (6 total), hard-capped.

Call 1: plain text. Call 2: structured JSON output with a deterministic numeric check.
Usage: .venv/bin/python -m experiments.m1_smoke
"""

from __future__ import annotations

import json
import sys

from pydantic import BaseModel

from src.bedrock.client import BedrockClient, ModelInvocationError
from src.bedrock.models import REPO_ROOT
from src.bedrock.usage import InvocationContext, UsageLimits

EXPERIMENT_ID = "m1_smoke"
MAX_TOKENS = 1024


class MeanResult(BaseModel):
    count: int
    mean: float


def main() -> int:
    client = BedrockClient(
        log_path=REPO_ROOT / "results" / "raw" / "invocations.jsonl",
        ledger_path=REPO_ROOT / "results" / "raw" / "m1_smoke_ledger.json",
        limits=UsageLimits(max_calls=8, max_input_tokens=20_000, max_output_tokens=8 * MAX_TOKENS),
    )
    rows = []
    for alias in client.registry.aliases:
        spec = client.registry.get(alias)
        ctx = InvocationContext(experiment_id=EXPERIMENT_ID, stage_id="smoke_text", prompt_version="m1.v1")
        try:
            r = client.converse(alias, "Reply with exactly: OK", context=ctx, use_cache=False, max_tokens=MAX_TOKENS)
            rows.append((alias, "text", r.record.status, r.text.strip()[:20] == "OK", r.record))
        except ModelInvocationError as e:
            rows.append((alias, "text", e.record.status, False, e.record))

        ctx = InvocationContext(experiment_id=EXPERIMENT_ID, stage_id="smoke_structured", prompt_version="m1.v1")
        try:
            sr = client.converse_structured(
                alias, "Compute the count and arithmetic mean of these numbers: 3, 5, 10.", MeanResult,
                context=ctx, use_cache=False, max_tokens=MAX_TOKENS)
            correct = sr.parsed is not None and sr.parsed.count == 3 and abs(sr.parsed.mean - 6.0) < 1e-9
            status = sr.result.record.status if sr.parsed else f"parse_error:{sr.parse_error.kind}"
            rows.append((alias, "structured", status, correct, sr.result.record))
        except ModelInvocationError as e:
            rows.append((alias, "structured", e.record.status, False, e.record))

    print(f"{'model':4} {'name':22} {'call':10} {'status':22} {'check':5} {'in':>5} {'out':>5} {'lat_ms':>8} {'cost':>12}")
    for alias, kind, status, ok, rec in rows:
        cost = f"${rec.cost_usd:.6f}" if rec.cost_usd is not None else rec.cost_status
        print(f"{alias:4} {client.registry.get(alias).name:22} {kind:10} {status:22} {str(ok):5} "
              f"{rec.input_tokens or 0:>5} {rec.output_tokens or 0:>5} {rec.latency_ms or 0:>8.0f} {cost:>12}")
    led = json.loads((REPO_ROOT / "results" / "raw" / "m1_smoke_ledger.json").read_text())
    print("ledger:", json.dumps({k: led[k] for k in ("calls", "input_tokens", "output_tokens", "unpriced_calls", "dollar_guard_active")}))
    return 0 if all(ok for *_, ok, _ in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
