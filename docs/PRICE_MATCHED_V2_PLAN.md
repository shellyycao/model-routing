# Price-Matched v2 — Frozen protocol

**Status:** `protocol_frozen_paid_execution_approved`. The initial pilot, candidate access probe and
six-call re-pilot are complete. The re-pilot succeeded 6/6 with every schema parsed. On 2026-11-18
the user explicitly approved the 810-call benchmark with the exact wording **“Approve main run”**.
Paid resume now requires HEAD to carry the amended tag `price-matched-v2-frozen-v1.1`. The original
`price-matched-v2-frozen-v1` tag is retained as the exact repeat-1 protocol provenance.

**Supersedes:** `docs/TIER_MATCHED_PLAN_DRAFT.md`. Four of its five selected models were unavailable
on this account. **Naming:** the new experiment is `price-matched-v2`; existing results remain
`original-v1`. No frozen v2 raw record, scorer, tag, Part B/C result, or XAI result is changed.

## Final models and selection disclosure

| Model | Call ID | US regional standard $/M (in / out) | Blended (3:1) |
|---|---|---:|---:|
| Claude Sonnet 4.6 | `us.anthropic.claude-sonnet-4-6` | 3.30 / 16.50 | 6.60 |
| Kimi K3 | `us.moonshotai.kimi-k3` | 3.30 / 16.50 | 6.60 |
| GLM 5 | `zai.glm-5` | 1.00 / 3.20 | 1.55 |

Prices are mechanically extracted from the official saved AWS Price List snapshots in
`results/raw/pricing/`. They are us-east-1 regional standard on-demand prices; global, batch, cache,
priority, flex, latency, custom, provisioned and long-context SKUs are excluded.

The original third model, Grok 4.7 (`us.xai.grok-4.7`), is **removed**. Although
`GetFoundationModelAvailability` reported AVAILABLE/AUTHORIZED, all three real pilot Converse calls
returned `AccessDeniedException` (`results/raw/price_matched_v2_pilot/records.jsonl`). A later
user-approved tiny probe also found Grok 4.6 denied, while GLM 5 and Mistral Large (24.02) were
callable (`results/raw/model_probe_2026-11-18.json`). GLM 5 replaces Grok by the user's final decision:
as in the earlier Grok-over-Mistral decision, generation match takes priority over price match.

This choice weakens the experiment's price matching. The maximum/minimum blended-price ratio grows
from **2.00×** in the Sonnet/Kimi/Grok plan to **4.26×** in the Sonnet/Kimi/GLM plan. This is a
disclosed user selection, not the output of an unobserved selection rule.

### Access eligibility rule

Control-plane availability is insufficient. Every final model must have saved evidence from a real
Converse invocation. Sonnet has three successful structured pilot calls. Kimi returned a
model-specific temperature ValidationException rather than AccessDenied, proving that the invocation
reached the model. The re-pilot then verified Kimi without temperature on all three schemas. GLM 5
succeeded in the tiny real invoke probe and then succeeded with temperature 0 on all three structured
re-pilot schemas. Both final parameter configurations are therefore eligible for the main run.

## Benchmark protocol

- **Scope:** all three models run the same new protocol. Sonnet's previous results are not reused.
- **Data and prompts:** frozen `datasets/independent_v2`; unchanged A1/A2 prompts; the v2.2 A3 prompt
  and schema with the seven-value attribute enum.
- **Scorer:** additive scorer v2.2. Frozen `src/independent/v2.py` is untouched.
- **Generation:** `maxTokens=16384`; vendor-default reasoning with no reasoning-control field.
  Sonnet 4.6 and GLM 5 send `temperature=0`. Kimi K3 omits the temperature field, the sole
  model-specific deviation, because the initial pilot returned: “This model doesn't support the
  temperature field. Remove temperature and try again.” No other parameter changes.
- **Size:** 3 models × 90 cases × 3 repeats = 810 logical calls.
- **Order:** repeat-major, then task/case/model, with models interleaved within every case. Stop after
  repeat 1 for the cost checkpoint.

### A3 and cost decisions

- Strict nDCG@5 (invalid ranking = 0) is primary; deduplicated nDCG is secondary.
- `citation_validity` checks cited-ID existence. Primary grounding is all-citations R1; R2 is
  secondary. The A3 Pareto frontier uses strict nDCG.
- Actual cost uses recorded input and billed output tokens, including reasoning.
- A1 cost per success uses `functional_correct`; A2 uses `content_correct`; A3 reports cost per valid
  response and per strict-nDCG point. Operational-success cost is labelled secondary.
- Report per-task quality–cost Pareto frontiers plus token usage, latency, truncation and format
  failures. Grok is excluded from all final analysis.

## Completed initial pilot and access probe

The initial nine-slot synthetic pilot ran under the shared `$15` reserve-then-settle ledger:

- Sonnet 4.6: 3/3 successful and schema-parsed.
- Kimi K3: its first call rejected the temperature field; the remaining two were skipped as designed.
- Grok 4.7: three AccessDenied errors; it was removed.

Seven calls were actually attempted. The shared ledger conservatively records **$0.63371**, including
worst-case reservations for failed attempts whose provider usage is unknown. The later three-call
candidate probe was separately user-approved and is retained as access evidence. Neither activity
inspected answer quality or changed prompts/scoring.

## Completed six-call compatibility re-pilot

`experiments/run_price_matched_v2_pilot.py` is now plan/audit-only and exposes no paid flag. The
completed fixed task-major order was:

1. Kimi K3 (temperature omitted), then GLM 5 (temperature 0) on synthetic A1;
2. the same two models on synthetic A2;
3. the same two models on synthetic A3.

These were the only six approved logical calls. They reused the initial synthetic cases, existing
Bedrock client, unchanged transient-only retry policy (maximum five attempts), shared ledger and
overall pilot cap of `$15`. All 6/6 calls succeeded and parsed. The shared ledger now records
**$0.671384** across 13 pilot/re-pilot attempts; this remains counted toward the future `$100` total.
Records are in dedicated `repilot_*.jsonl/json` files under
`results/raw/price_matched_v2_pilot/` so initial evidence stays append-only. Each attempted call
records status/error, raw input/output/reasoning usage, effective parameters, stop reason,
schema-parse status, latency and cost. Answer quality is forbidden. A parameter failure stops that
model's remaining re-pilot slots; no such failure occurred.

## Offline verification and implementation

`experiments/verify_price_matched_models.py` reproduces prices and eligibility solely from saved
pricing, control-plane, pilot and real-probe evidence. Its output is
`results/processed/independent_v2/price_matched_model_verification.json`, including snapshot hashes,
SKUs, invocation evidence, and the Grok removal record.

`experiments/run_price_matched_v2.py` builds the exact 810-row plan and a registry where only Kimi has
`temperature=None`. Execution is approved but remains locked behind the exact tag and frozen manifest.
The first paid command is:

```bash
.venv/bin/python -m experiments.run_price_matched_v2 --execute
```

It runs repeat 1 only, then writes the checkpoint and stops. After manual cost review, the explicit
resume command is:

```bash
.venv/bin/python -m experiments.run_price_matched_v2 --execute --continue-after-repeat-1
```

Continuation requires a ledger audit and the checkpoint projection below to pass:

```text
pilot actual cost + 3 × repeat-1 evaluation actual cost <= $100
```

The `$100` reserve-then-settle guard remains authoritative even if the projection passes.
`experiments/analyze_price_matched_v2.py` restricts final reporting to Sonnet, Kimi and GLM and uses
the v2.2 metric/cost definitions above.

Task records and the repeat-1 checkpoint are written under `results/raw/price_matched_v2/`; invocation
records go to `results/raw/price_matched_v2/invocations.jsonl`; per-run prompts, responses, usage,
parsed output and A1 harness artifacts go under `results/raw/runs/<run_id>/`; the shared ledger is
`results/raw/ledgers/price_matched_v2.json`.

## Budget

The regenerated machine plan reports two views:

- **Static worst case:** the completed pilot/re-pilot ledger amount `$0.671384` plus all 810 evaluation
  calls, with five attempts per future logical call, the conservative input bound,
  and 16,384 output tokens on every future attempt. This exposure exceeds `$100`; the runtime cap
  stops rather than overspends. The frozen calculation is **$841.39**.
- **Realistic estimate:** completed pilot/re-pilot actual plus no retries; rendered input estimated as UTF-8 bytes / 4
  plus 256 tokens; billed output including reasoning averages 3,500 tokens for A1, 1,000 for A2 and
  2,000 for A3. The frozen estimate is **$24.24**.

Both totals are regenerated from the final verified prices. The hard cap is unchanged at **$100**,
and pilot/re-pilot spend shares the same ledger.

## CP3e freeze condition

The manifest records the exact approval wording, `$100` cap, 810 calls, repeat-1 stop, complete
immutable protocol hashes, and the pre-main ledger baseline. Re-pilot records and summary are frozen
inputs. This CP3e preparation performs no network/model call and creates no tag; Claude will commit,
tag, verify and execute only after review.

## Execution-bug amendment — 2026-11-18

After repeat 1 completed (270 calls, 0 `void_infra`, `$6.8974832` evaluation cost), the approved
resume command crashed before any new model call with `KeyError: 'run_id'`. The ledger stayed at 283
total calls with no pending reservation. The repeat-1 checkpoint remains valid and projects
`$21.3638336 <= $100`.

Cause: `_completed()` scanned every `*.jsonl` file in `results/raw/price_matched_v2/`, including
`invocations.jsonl`, whose run ID is nested under `context` rather than stored at top level. That file
did not exist when repeat 1 started, so the fault appeared only on resume.

Amendment: `_completed()` now reads only the three task record files
`price_matched_v2_a1.jsonl`, `price_matched_v2_a2.jsonl`, and
`price_matched_v2_a3.jsonl`. No raw repeat-1 record is modified, deleted or rewritten. The scientific
protocol—data, prompts, scorer, models, parameters, repeat-major order, 810-call scope, `$100` cap and
mandatory repeat-1 checkpoint—is unchanged. The amended runner and manifest require the new tag
`price-matched-v2-frozen-v1.1`; the old tag is not deleted.
