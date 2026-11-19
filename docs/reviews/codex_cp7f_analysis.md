# Codex CP7f — Price-matched workflow analysis

## Scope

Completed the offline CP7f replication analysis using only
`expA_price_matched_workflow_v3` and the rerun-resolved
`expB_price_matched_workflow_v3`. Generated the schema-compatible v3 tables, both v3.1 reporting
rescores, a new prospective LOPO S1–S4 routing directory and hash chains, the separate post-hoc
cost-aware Router, the processed CP7f summary, and the reader-facing report. No frozen or raw file
was modified and no model, Docker, or network call was made.

## Integrity and rerun resolution

Audit status is **PASS**. All 470 main invocations map exactly to Part A/B records; all 479 paid
attempts including the pilot reconcile to the ledger ($25.887525, 1,096,569 input and 1,607,032
output tokens, zero failed attempts, pending empty). Protocol hashes, model IDs, maxTokens 16384,
Kimi's omitted temperature, other-model temperature 0, prompt/data/config hashes and the immutable
sandbox image pass. The 161 raw Part B records resolve to 156 effective cells: all five originals
remain, and the five append-only reruns replace them only for analysis.

## Main results

The main grid is 41/108 feasible under primary v3 and 53/108 under post-hoc v3.1; single-model
paths are 3/12 versus 38/96 cross-model under v3. Outcomes were repeat-consistent in 20/24
project/path cells under both label views. Effective Part B spend is $23.2235 across 156 runs;
cost per feasible completion is $0.3807 (v3) and $0.3016 (v3.1).

## Routing and cost

The prospective Router produced 20 traces and 64 predictions with no held-out evidence reference;
both prediction and validation chains verify. Faithfulness is 451/451 claims and 20/20 replay
matches, while feasibility-direction accuracy is 31/64 (48.4%), compared descriptively with the
original group's 22/50 (44.0%). The post-hoc cost-aware variant is 444/444 faithful, changes 7/8
selectable traces at the cost-preference step (0 Pareto-set changes), and records 64/64 cost-direction
matches versus 56/64 for naive unit-price ordering; its feasibility direction is 41/64.

## Verification

New tests cover integrity reconciliation, rerun resolution, frozen parameters, Part A/B summaries,
cost denominators/Pareto sets, LOPO leakage, both hash chains, cost-aware faithfulness, separation
from raw data, and required disclosures. Full suite: **529 passed, 23 skipped**.
