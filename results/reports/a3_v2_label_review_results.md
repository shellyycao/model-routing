# Independent v2 A3 Human Label Review

## Validation

Both completed worksheets passed schema, row-count, anonymous-ID, immutable-source-field, allowed-value, completeness, and grade/axis consistency checks.

## Agreement

- Query rules reviewed: 30/30.
- Candidate-query pairs reviewed: 180/180.
- Relevance-grade agreement: 167/180 (92.8%).
- Topic-match disagreements: 13.
- Method-match disagreements: 0.

## Systematic finding

All 13 label disagreements and all 3 query-rule ambiguity flags occur in A3Q-005, A3Q-015, A3Q-025. These are the three hate-speech queries. Their candidate documents use the broader surface form `detecting abusive online content`, which the human reviewer correctly judged insufficient to establish a strict hate-speech topic match.

The disagreement is therefore a dataset wording defect, not evidence that the relevance rule itself should be weakened. Simply downgrading the labels would leave the affected queries without direct-relevance documents.

## Resolution

1. Preserve these completed judgments as the locked first-pass record.
2. Replace the overly broad candidate surface form with `detecting hate speech` in the deterministic generator.
3. Regenerate the candidate dataset and issue a blinded supplemental packet for the three affected queries.
4. Keep the A3 adjudication and dataset-freeze gates open until the supplemental review is returned and validated.
