# Independent v2 A3 Label Review Protocol

**Query worksheet:** `results/review/a3_v2_query_review_worksheet.csv`

**Candidate-label worksheet:** `results/review/a3_v2_label_review_worksheet.csv`

**Locked key:** `results/review/a3_v2_label_review_key.csv`

**Sampling manifest:** `results/review/a3_v2_label_review_manifest.json`

**Scope:** 30 query rules and 180 candidate-query pairs, divided into three balanced batches.

**Status:** completed and locked on 2026-11-18. The first pass found a systematic topic-surface defect in three hate-speech queries. The targeted rereview subsequently accepted all three corrected query rules and all 18 reviewed labels, completing adjudication.

## Purpose

This review independently checks the candidate relevance rules and labels before the Independent v2 dataset is frozen. It is a dataset-label audit, not an evaluation of any model output. No evaluated-model response appears in the packet.

## Blinding

Do not open `a3_v2_label_review_key.csv` until both worksheets are complete and the judgments are locked. The worksheets omit case IDs, document IDs, difficulty tiers, proposed relevance grades, proposed topic/method flags, and sampling strata.

Review every row from the supplied query and candidate text. Do not try to reconstruct the generator's intended label.

## Relevance rule

Assign one relevance grade to each candidate-query pair:

- `2`: the study's own main contribution directly applies the requested method to the requested topic;
- `1`: the study's own main contribution matches exactly one of the requested topic or method;
- `0`: the study's own main contribution matches neither dimension.

A sentence that only mentions the requested topic and method as prior work remains grade `0` when the study itself addresses a different problem. The title and abstract are the complete evidence for this synthetic controlled-retrieval task. Do not use external sources.

## Review procedure

1. Complete `a3_v2_query_review_worksheet.csv`. For each query, judge whether the wording is clear, whether the direct-relevance rule is unambiguous, and whether the named topic and method are acceptable representations of the query.
2. Complete `a3_v2_label_review_worksheet.csv`. Judge each candidate independently using the rule above.
3. Fill every categorical field. Use only `yes` or `no`, relevance grades `0`, `1`, or `2`, and confidence `high`, `medium`, or `low`.
4. Use `reviewer_notes` for ambiguity, conflicts between title and abstract, or a reason that the item is not judgeable. Do not leave a required field blank merely because the decision is difficult.
5. The three `review_batch` values each contain 10 queries and 60 candidate rows. Batches may be completed in separate sessions, but do not open the key between batches.
6. When both worksheets are complete, save them under new filenames or return the completed copies. Do not revise judgments after opening the key unless a clerical correction is logged.

## Incorporation rule

No judgment cell in the supplied worksheets is filled by AI. After the human judgments are returned, they will be validated and joined to the locked key. Any disagreement with a candidate label must be resolved without viewing evaluated-model outputs. Accepted changes, unresolved items, final dataset hashes, and the adjudication result must be recorded before creating the `independent-v2-frozen` tag.

Reproduce the untouched packet with:

```bash
.venv/bin/python -m experiments.prepare_a3_v2_label_review
```
