# Codex CP8a — Corrections Design

## Scope

Created additive post-hoc rules for a five-column corrected stage view and an exact continuation
protocol. Frozen records, replays, validators, scores, tags, and conclusions are untouched. The
corrected-view JSON is alias-only; model names are restricted to its future rendered report.

## Eligible Inventory

After resolving the five Docker reruns, 40 Part B cells meet all three criteria: exact int64
serialization failure, pinned replay passes the frozen validator, and every downstream stage never
ran. All are analysis recoveries with one reporting call remaining: original group Nova Pro 9 and
gpt-oss-120b 2; price-matched group GLM 5 29. The 40 reporting calls split as original A/B/C =
4/5/2 and price-matched A/B/C = 7/7/15. Eleven recovered cleaning stages are excluded because their
downstream stages already ran.

## Budget

| Group / reporting model | Calls | Five-attempt static | Observed-mean realistic |
|---|---:|---:|---:|
| Original / A | 4 | $2.2776 | $0.1780 |
| Original / B | 5 | $0.6101 | $0.0411 |
| Original / C | 2 | $0.0457 | $0.0043 |
| Price-matched / A | 7 | $11.0759 | $0.3138 |
| Price-matched / B | 7 | $11.0873 | $0.7592 |
| Price-matched / C | 15 | $4.9898 | $0.1129 |
| **Total** | **40** | **$30.0864** | **$1.4093** |

The proposed separate reserve-then-settle cap is $15. It is deliberately below the all-five-retries
exposure and well above the one-attempt observed-token estimate; budget refusal stops execution
rather than increasing it. No compatibility smoke test is proposed because all six exact
model/parameter combinations already completed the source experiments.

## Implementation and Verification

Added the plan-by-default `experiments/run_continuations.py`. Paid execution requires a future
explicit approval manifest plus exact `continuation-v1` tag and matching protocol/inventory hashes;
this turn creates neither. The runner reconstructs the standard handoff from saved original code
and recovered pinned-image findings, calls only the missing reporting model, writes new append-only
records linked by `continued_from`, and resumes only from its dedicated record file. Offline mock
tests cover the gate, inventory, budget, handoff provenance, infrastructure labeling, and
idempotency. Full suite: **546 passed, 23 skipped in 52.57s**. No model/network call or corrected
outcome computation occurred in CP8a.
