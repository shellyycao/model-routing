# Post-hoc reporting validator v3.1 (2026-11-18)

- **Status:** POST-HOC secondary analysis, approved by the user ("Post-hoc rescore too").
- **Primary scores:** frozen v3 (tag `benchmark-v3-frozen`) stays the primary, authoritative score. v3.1 is reported beside it and is never pooled with it or substituted for it.
- **What is unchanged:** `src/evaluation/reporting_v3.py`, `prompts/v3`, every raw record, and the running Experiment B.

## Trigger
The Phase 1 analysis found an identical reporting failure for two models on customer_churn q7:
- the check that failed was `prose_claims_consistent`;
- Claude wrote "Premium LTV is 292.0% higher than Basic", and gpt-oss wrote "Premium LTV is 292.0% higher than Basic" as well.

Both sentences are correct: `premium_vs_basic_ltv_change_pct` = 292.005. The frozen check, however, attributes the number written after "<alias> is" to that alias (`ltv_premium` = 1,816.78).

## Rule
v3.1 is v3 with one change. A `prose_claims_consistent` entry is cleared only when ALL of the following hold:
1. the relation is "after" (`<alias> is/was/=/:` followed by the number);
2. the number is immediately followed by a comparative word (higher, lower, more, less, greater, larger, smaller, above, below, up, down, than);
3. the number matches ANOTHER verified metric of the same finding;
4. the frozen detail list is not truncated (fewer than 10 entries).

All other checks are unchanged. The implementation is `src/evaluation/reporting_v3_1.py`, which post-processes the v3 result deterministically.

## Evidence
- **Regression tests:** `tests/test_eval_reporting_v3_1.py`, 5/5 pass.
  - The real Phase 1 report is cleared under v3.1.
  - Swapped values, a wrong comparative number and a plain mis-attribution still fail.
  - v3.1 never fails a report that v3 passes.
- **Experiment A rescore:** `python -m experiments.rescore_reporting_v3_1 --records results/raw/stage_benchmark/expA_stage_v3.jsonl` writes `results/processed/v3_1_rescore/expA_stage_v3_reporting.json`.

  | Basis | v3 passed | v3.1 passed |
  |---|---|---|
  | Ground truth | 7/12 | 9/12 |
  | Conditional | 6/12 | 8/12 |

  - Exactly 2 reports changed from false to true, the two churn q7 cases.
  - No report changed from true to false.
  - The v3 recompute equals the stored record for all 12.
- **Experiment B:** to be rescored after it finishes, the same way.

## Limits
- The rule was designed after the false reject was seen, so its effect on Experiment A is not an independent test.
- Other false-reject patterns may exist.
- A wording-dependent rule can only be checked against the patterns in the tests above.
