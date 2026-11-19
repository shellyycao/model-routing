# Post-freeze reporting audit and offline repair

- **Date:** 2026-11-18 UTC
- **Frozen reference:** `benchmark-v2-frozen` (`411fcd7`)
- **Scope:** offline diagnosis only; no Bedrock calls
- **Evidence preserved:** frozen prompt/validator v2 and every existing raw record are unchanged

## Executive result

The ten reporting failures are not one homogeneous model failure. Frozen v2 conflates three things:

1. **Prompt/schema contract ambiguity.** `ProjectSpec.model_view()` exposes metric keys but hides
   `ranking_labels` and `direction_key`; `KeyFinding.ranking` is optional; and the v2 reporting prompt
   asks for a ranking for group comparisons while q3 is worded as a trend. Nevertheless, the v2
   validator requires a q3 ranking using hidden display labels.
2. **Validator/interface mismatch.** Three otherwise interpretable q2 rankings use the metric keys
   that the model actually received. V2 rejects those tokens even when their order is correct. V2
   also treats an omitted explicit ranking as semantic incorrectness even when all reported values
   are present and determine the order unambiguously.
3. **Genuine output errors.** A-B-B states the wrong q2 order; A-A-C has a wrong derived value; and
   C-B-A contains propagated wrong values and multiple dependent reporting errors. These remain
   failures under the post-freeze audit.

All ten reports omitted q3's explicit ranking. Seven gave q2 rankings as display labels and three
used metric keys. Of the three metric-key rankings, two have the correct order and one is genuinely
wrong.

## Additive v3 policy

V3 is explicitly post-freeze and does not replace v2:

- `src/evaluation/reporting.py` and `prompts/v2/` remain untouched and authoritative for frozen v2.
- `src/evaluation/reporting_v3.py` separates semantic ranking correctness from explicit structured
  compliance.
- Metric keys and declared display labels are accepted as aliases for the same ranking item.
- If an explicit ranking is absent, semantics can be recovered only when every finite
  `reported_values` entry required for that ranking exists. The omission remains visible as the
  non-mandatory `rankings_explicit` check.
- A wrong explicit ranking remains a mandatory failure.
- `prompts/v3/` exposes the exact metric-key-to-label contract and explicitly requires rankings for
  every flagged finding, including trend questions. The active workflow still uses v2.

This changes the measurement interpretation. V2 is strict contract compliance under an ambiguous
interface; v3 separately measures semantic correctness and explicit-structure compliance. Scores
must therefore be reported side by side and never pooled or substituted.

## Offline saved-output rescore

`experiments/rescore_reporting_v3.py` imports no model client, hashes every source artifact and
writes only to `results/processed/pilot_v3_rescore/retail_sales_reporting.json`. It is deterministic
and does not mutate source records.

| Outcome | Count |
|---|---:|
| Saved reports rescored | 10 |
| Frozen v2 ground-truth pass | 0 |
| Post-freeze v3 ground-truth pass | 7 |
| Remain failed under v3 | 3 |

The remaining failures are:

| Path | Run | Reason retained by v3 |
|---|---|---|
| A-A-C | `expB_paths-7b41ea130a1b83a4` | q7 derived value 2006.53 does not recompute (2005.968783783784) |
| A-B-B | `expB_paths-16296ffeb287a694` | explicit q2 order East, West, North, South is not descending |
| C-B-A | `expB_paths-9752d7ddbebd5874` | propagated wrong reported values, inferred q3 order, derived values, substantive statements and prose |

Every v3 record retains its original v2 score, validation details, report hash and upstream findings
hash. The seven transitions are secondary post-hoc results, not evidence that the original v2 paths
passed the frozen benchmark.

## Docker root cause and repair

Repository code never removes or prunes Docker images. The pilot evidence proves that the verified
tag existed for 28 sandbox executions and later disappeared between a paid response and code
execution. Docker retained no deletion event identifying the actor. The narrowest supportable root
cause is therefore **external Docker daemon state loss or cleanup**, not Bedrock and not generated
model code. The exact external actor cannot be recovered from the available logs.

The repair is fail-closed and offline:

- both paid runners check `SandboxGate` before constructing `BedrockClient`;
- after verification, a restricted holder container pins the exact image for the whole run;
- the holder has no network, mounts or forwarded environment, uses a read-only root filesystem,
  non-root UID, dropped capabilities and tight CPU/memory/PID limits;
- the tag is rechecked after lease acquisition, and the holder is removed on exit;
- there is no auto-build, auto-pull or fallback to host execution.

The lease protects against ordinary image pruning. It cannot make a Docker Desktop VM reset
impossible, so the existing per-stage gate and image-ID checks remain necessary. The unchanged
Dockerfile was rebuilt with `--pull=false` and verified as
`sha256:feb2b26b9e232d36de89459d43cd986db4e7efa6dab5119b76d68842097a0eb3`.
The new verification is stored outside `results/raw/` so the historical raw record remains intact.

## Predefined retry policy (not approved or executed)

If frozen-v2 completion is approved, retry **all five and only the five** `void_infra` paths once
through `--retry-void-infra`. The runner creates new run IDs and retains the original five records.
Do not select only favorable paths and do not retry any model-attributable failure. Use the original
ledger and aggregate caps. The plan-only bound is 15 logical model calls, 170,010 input tokens and
61,440 output tokens. Dollar cost remains unavailable because model prices are unverified.

No paid retry should occur until the user separately chooses whether v2 remains the primary design
or a separately named v3 experiment is required. V2 and v3 runs must not be mixed into one primary
comparison.
