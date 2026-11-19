# Independent v2 A3 Targeted Rereview Protocol

**Query worksheet:** `results/review/a3_v2_query_rereview_worksheet.csv`

**Candidate-label worksheet:** `results/review/a3_v2_label_rereview_worksheet.csv`

**Locked key:** `results/review/a3_v2_label_rereview_key.csv`

**Scope:** three corrected hate-speech queries and 18 candidate-query pairs.

**Status:** completed and locked on 2026-11-18; all three query rules and all 18 labels were accepted with no remaining disagreement.

## Why this supplemental review is required

The locked first-pass review agreed with 167 of 180 proposed grades. All 13 disagreements came from the same wording defect: the query asked for `hate speech detection`, while candidate documents used the broader phrase `detecting abusive online content`.

Candidate version 0.2 replaces that phrase with `detecting hate speech`. The relevance construction, document IDs, methods, datasets, metrics, candidate selection, and proposed label structure are unchanged. This supplemental review checks only the three affected query sets against the corrected evidence.

## Procedure

1. Do not open `a3_v2_label_rereview_key.csv` before completing both worksheets.
2. Review all three query rows and all 18 candidate rows independently.
3. Apply the same relevance rule as the first pass: grade `2` matches topic and method, grade `1` matches exactly one axis, and grade `0` matches neither.
4. Use only `yes` or `no`, grade `0`, `1`, or `2`, and confidence `high`, `medium`, or `low`.
5. Save and return both completed worksheets. Do not revise them after opening the key unless a clerical correction is logged.

The original completed worksheets remain the locked record for all unaffected items. The dataset cannot be frozen until this supplemental review is validated.
