# retail_sales Two-Stage Pilot Result

- **Executed:** 2026-11-17 (America/New_York; raw records use UTC on 2026-11-18)
- **Scope:** Experiment B, `retail_sales`, 9 fresh two-stage paths, repeat 0
- **Frozen baseline:** `benchmark-v2-frozen` (`411fcd7`)
- **Hard limits:** 30 API attempts, 200,000 input tokens, 80,000 output tokens
- **Result:** 9 workflow records completed; 3 feasible and 6 infeasible
- **Next-phase status:** stopped after this phase; no three-stage grid or Experiment A calls were made

## Path outcomes

| Path | Outcome | Cleaning | Analysis | Main observation |
|---|---|---|---|---|
| A-A | feasible | passed | passed | All quality metrics 1.0 |
| A-B | feasible | passed | passed | All quality metrics 1.0 |
| A-C | feasible | passed | passed | All quality metrics 1.0; C reasoning logged separately |
| B-A | infeasible | execution error | blocked | Generated date parser called `strptime` on a float |
| B-B | infeasible | execution error | blocked | Generated code passed a list as pandas `to_datetime(format=...)` |
| B-C | infeasible | execution error | blocked | Generated date parser called `strptime` on a float |
| C-A | infeasible | truncated | blocked | Cleaning hit `maxTokens=4096`; truncated JSON could not be parsed |
| C-B | infeasible | validation failed | validation failed | Cleaning dropped/mismatched customer rows; analysis ran on the actual artifact |
| C-C | infeasible | truncated | blocked | Cleaning hit `maxTokens=4096`; truncated JSON could not be parsed |

Model A cleaning succeeded in all three fresh paths, and analysis models A, B and C all produced exact accepted findings from those artifacts. Model B cleaning produced executable-looking but failing Python in all three fresh paths. Model C cleaning hit the shared output limit in two paths; its one parseable cleaning result was structurally consumable but semantically wrong.

For C-B, cleaning quality was `0.974573` correctness, `0.976923` data integrity and `0.972973` schema compliance. The downstream analysis had ground-truth numerical accuracy `0.208333`, while conditional numerical accuracy against the actual upstream artifact was `0.791667`. This is an observed propagation case, not a causal claim.

## Accounting and provenance checks

| Check | Result |
|---|---|
| Workflow records validate against contracts v1.2 | 9/9 passed |
| Unique run IDs and expected paths | 9/9 |
| Paid logical calls / API attempts | 13 / 13 |
| Failed attempts or retries | 0 |
| Input tokens | 28,976 |
| Output tokens | 31,058 |
| Cache hits | 0 invocation and 0 stage cache hits |
| Ledger reconciliation | calls and both token totals match invocation log exactly |
| Pending ledger reservations | 0 |
| Cost handling | all 13 calls `unavailable`; no non-null incurred cost |
| Docker executions | 11, all on the verified image |
| Verified image ID | `sha256:d8af82a587873badf2aa309699d72086b56c5e8a1f525d13ccba0b69c329b8c9` |
| Resume check | all 9 runs skipped; 0 calls planned |

Only 13 of the maximum 18 planned model calls were made because five analysis stages were correctly blocked after unusable cleaning artifacts. The run stayed well below every approved hard limit.

The invocation log contains 15 records: 13 paid model-call records plus 2 zero-usage parse-error events linked to the two truncated C cleaning calls. gpt-oss reasoning was recorded separately on four invocations, including the successful A-C analysis call and all three C cleaning calls.

## Stored evidence

- Workflow records: `results/raw/workflow_runs/expB_paths.jsonl`
- Invocation log: `results/raw/invocations.jsonl`
- Usage ledger: `results/raw/ledgers/expB_paths_20261118T022656Z.json`
- Per-run prompts, responses, code, executions and validations: `results/raw/runs/expB_paths-*`
- Sandbox verification: `results/raw/sandbox_verification.json`

## Decision gate

This phase is complete and should not be rerun: resume planning reports all 9 records as completed. The three-stage pilot and Experiment A remain unexecuted and require separate explicit approval. The observed C truncations are real pilot outcomes under the frozen shared `maxTokens=4096` protocol; do not change prompts, inference settings or the frozen benchmark without recording a post-freeze design decision.
