# Blinded Human Review Protocol

**Packet:** `results/review/human_review_worksheet.csv`

**Identity key:** `results/review/human_review_key.csv`

**Sampling manifest:** `results/review/human_review_manifest.json`

**Items:** 18

**Completion status:** completed; judgments locked and unblinded on 2026-11-18. Results are in `results/reports/human_review_results.md`.

## Purpose

This review checks whether frozen v1 automatic judgments agree with a human reader, with special attention to scorer disagreements and operational-versus-content distinctions. It is not intended to produce a statistically precise human benchmark estimate.

The 18 items are stratified as three tasks × three models × two items per cell. The selection deliberately includes automatically correct, incorrect, borderline, truncated, wrapper-failed, and scorer-disagreement examples.

## Blinding

Do not open `human_review_key.csv` before completing and locking every human judgment. The worksheet contains no model alias, model name, model ID, run ID, or original automatic score. Anonymous IDs were assigned after a deterministic shuffle with the seed recorded in the manifest.

The reference answer or evidence is intentionally visible because the task is correctness adjudication, not an unaided reproduction exercise.

## Review procedure

1. Work only in a copy of `human_review_worksheet.csv` or add judgments directly to its blank human columns.
2. Read the task instructions, relevant input, model output, and reference/evidence.
3. Do not infer model identity from style or length; identity is irrelevant to the judgment.
4. Fill every applicable human field. Use `NA` where a dimension does not apply.
5. Choose one primary error class and optionally note secondary errors in `reviewer_notes`.
6. After all 18 rows are complete, save the worksheet and do not revise it after opening the identity key unless a clerical error is documented.
7. Return the completed worksheet. The automatic scores will then be joined using `anonymous_sample_id` for agreement analysis.

## Judgment fields

### `human_overall_judgment`

Use one of:

- `correct`
- `mostly_correct`
- `incorrect`
- `not_judgeable`

`mostly_correct` means the central answer is right but a real, non-cosmetic defect remains.

### `human_content_correct`

Use `yes`, `partial`, `no`, or `NA`.

- A1: does the code implement the complete specification, not merely the visible examples?
- A2: are the extracted values supported and correctly transformed, regardless of wrapper format?
- A3: are the ranking and substantive claims correct with respect to the supplied documents?

### `human_schema_compliant`

Use `yes`, `no`, or `NA`. Judge only the required response structure and keys. A bare but content-correct A2 object is `no` here.

### `human_operationally_usable`

Use `yes`, `no`, or `NA`. A response is operationally usable only if the intended pipeline can parse and consume it without a post-hoc repair. Truncation is `no`.

### A3 quality fields

For ranking, grounding, and citation accuracy, use:

- `3`: fully correct or no substantive defect found;
- `2`: mostly correct, minor defect;
- `1`: substantial error but some useful correct content;
- `0`: absent, invalid, or fundamentally incorrect;
- `NA`: not applicable.

For ranking, direct method-and-topic matches should outrank partial matches and prior-work-only mentions. For grounding, each factual claim must be supported by every cited document. Accept a faithful paraphrase; do not require canonical wording. For citation accuracy, cited IDs must exist and genuinely support the associated statement.

## Error classification

Choose one primary label:

- `none`
- `functional_logic`
- `incomplete_fix`
- `wrong_bug_localization`
- `wrong_value`
- `unit_or_discount_conversion`
- `missing_field`
- `hallucinated_field`
- `schema_or_wrapper`
- `invalid_json`
- `truncation`
- `ranking_error`
- `unsupported_claim`
- `wrong_attribution`
- `citation_error`
- `ambiguous_spec_or_reference`
- `automatic_scorer_false_accept`
- `automatic_scorer_false_reject`
- `other`

## Task-specific notes

### A1

Hidden checks and the reference solution are evidence, not an instruction to demand identical code. Accept any semantically correct implementation. Record a possible test-suite gap if the code passes listed checks but violates a plausible in-scope input.

### A2

Judge content, schema, and operational usability independently. Apply the schema's conversion and conflict-resolution rules. Use null only when the document does not support a value.

### A3

This is controlled candidate selection. Do not judge whether the system searched the web. Separate ranking quality, evidence grounding, and citation accuracy. A claim faithfully copying a supplied abstract may be correct even when it differs from the canonical label's wording.

## Incorporation rule

No cell in the supplied worksheet was filled by AI. The human reviewer returned all 18 completed judgments, which were validated and then joined to the identity key. Any post-unblinding correction must be logged with sample ID, old value, new value, and reason.

Reproduce the untouched packet with:

```bash
.venv/bin/python -m experiments.prepare_human_review
```
