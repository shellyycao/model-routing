# Human Spot-check Results

**Status:** completed and unblinded after all 18 judgments were locked

**Scope:** purposive, stratified review of two outputs per task-model cell; descriptive validation, not a performance estimate

## Completion and integrity

- Completed rows: 18/18.
- Anonymous IDs match the sampling key exactly.
- Every required human field is populated with a protocol-allowed value.
- Imported completed-file SHA-256: `6e07ec073b740984bbfcd229c1bd7b74f4904c6667b7dd7e88754e993d2d7f2d`.
- Model identities and automatic scores were joined only after completion.

## Human judgments

| Task | n | Correct | Mostly correct | Incorrect |
|---|---:|---:|---:|---:|
| A1 | 6 | 5 | 0 | 1 |
| A2 | 6 | 3 | 3 | 0 |
| A3 | 6 | 0 | 5 | 1 |
| **Total** | **18** | **8** | **8** | **2** |

The sample intentionally over-represents failures, borderline cases, and scorer disagreements. These counts must not be reported as model accuracy rates.

## Automatic–human agreement

| Comparison | Agreement | Interpretation |
|---|---:|---|
| A1 functional correctness | 6/6 | Hidden-test functional labels agreed with the human judgment. |
| A2 strict content correctness | 5/6 | The mismatch is a content-correct response rejected for its missing wrapper. |
| A2 recovered content correctness | 6/6 | Separating recoverable content resolves the disagreement. |
| A2 schema compliance | 6/6 | Wrapper/parse compliance agreed. |
| A2 operational usability | 6/6 | Immediate pipeline usability agreed. |
| A3 operational usability | 5/6 | One four-ID parsed response was human-usable but failed the exact-five automatic rule. |

## A3 detailed comparison

| Sample | Model | Case | Status | nDCG@5 | Human ranking | Grounding v1 | Grounding v1.1 | Human grounding | Structural citation | Human citation |
|---|---|---|---|---:|---:|---:|---:|---:|---|---:|
| HR-002 | B | a3_08 | passed | 1.000 | 2 | 0.889 | 0.889 | 2 | True | 2 |
| HR-004 | A | a3_09 | passed | 0.952 | 1 | 0.800 | 1.000 | 2 | True | 3 |
| HR-008 | C | a3_05 | failed | — | 2 | — | — | 2 | — | 3 |
| HR-011 | C | a3_06 | failed | 0.952 | 2 | 0.952 | 1.000 | 2 | True | 2 |
| HR-013 | B | a3_03 | passed | 0.668 | 1 | 1.000 | 1.000 | 1 | True | 2 |
| HR-014 | A | a3_01 | passed | 1.000 | 2 | 0.800 | 1.000 | 3 | True | 3 |

## Confirmed and new findings

1. **A1 functional scoring is credible on the reviewed items, but localization is not.** `a1_09_top_k` correctly identifies `rank_key`, the actual mutated helper, while the scorer searches only for `top_k` and marks localization false.
2. **A2 must retain separate content and operational scores.** The reviewer confirmed the bare-object response is fully content-correct but not schema-compliant or directly usable.
3. **A3 ranking metrics understate some qualitative errors.** nDCG 0.952 can still omit the required fifth relevant study, and nDCG 1.0 does not guarantee that the synthesis frames a grade-1 paper appropriately.
4. **Grounding needs both accepted paraphrases and prose coverage.** v1 rejects faithful abstract wording; structured-claim scoring can also miss unsupported prose when the response omits that prose assertion from its claim list.
5. **Citation structure is not citation accuracy.** All 5 parsed reviewed A3 outputs passed `citation_consistent`, but only 2/5 received a perfect human citation score.

## Consequences

- Frozen v1 scores remain unchanged and primary.
- Human results validate the A2 post-hoc content/schema decomposition and A3 v1.1 paraphrase repair, while identifying additional A1-localization and A3-prose/citation limitations.
- These results should inform v2 scorer design before freeze, without using future evaluated-model outputs.
- This v1 spot-check does not adjudicate the candidate v2 A3 relevance labels; that remains a separate pre-freeze task.

Reproduce with:

```bash
.venv/bin/python -m experiments.analyze_human_review --completed <completed_worksheet.csv>
```
