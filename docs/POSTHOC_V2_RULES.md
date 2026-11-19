# Independent v2 Post-hoc / Exploratory Analysis Rules

**Rule version:** `posthoc-v2-rules-1.0.1`
**Written:** 2026-11-18  
**Status:** checkpoint 1; rules frozen before post-hoc rescoring  
**Scope:** offline analysis of saved `results/raw/independent_v2/` artifacts only

## Guardrails and provenance

This document pre-registers the post-hoc rules requested by
`docs/POSTHOC_V2_ANALYSIS_BRIEF.md`. All outputs produced under these rules must be
labelled **post-hoc / exploratory**. The prospective Independent-v2 scores remain the
primary frozen results.

- No new model calls are permitted.
- Frozen raw records, `src/independent/v2.py`, datasets, and
  `independent-v2-frozen-v1.1` are read-only.
- Post-hoc code must be additive (`src/independent/v2_posthoc.py` and/or
  `experiments/analyze_independent_v2_posthoc.py`).
- Analysis code, tests, logs, and intermediate JSON use aliases `A`, `B`, and `C`
  only. Model names are added only while rendering the final report, after all
  numerical results have been computed and serialized.
- Every rule below is applied identically to all aliases and all eligible cases.
- Frozen, strict, and relaxed views are always reported together. No relaxed view
  replaces or silently edits a frozen value.
- No hypothesis test was prospectively registered. All tests below are exploratory;
  confidence intervals and effect sizes receive priority over p-values.

The rules were derived from response contracts, scorer mechanics, dataset/generator
formats, and blinded response-format inspection. No rule may be changed after this
commit based on a per-alias or individual-case outcome. Any later change requires a
new rule version and must be labelled a separate sensitivity analysis.

### Dated implementation amendment — 2026-11-18

The project environment does not contain SciPy. Section 5.3 is therefore implemented
directly with the standard Wilcoxon normal-approximation formula using exactly the
pre-registered semantics: zero differences are dropped, absolute-difference ties use
average ranks and the tie-corrected variance, the test is two-sided, and no continuity
correction is applied. An all-zero vector returns statistic 0 and p-value 1. Tests must
include a hand-computed reference value. This `posthoc-v2-rules-1.0.1` amendment changes
only the implementation dependency; it does not change a scoring rule, comparison,
family, alpha, seed, or reporting requirement.

## 1. A1 normalized bug-location rule

### 1.1 Frozen view

Retain the frozen `bug_location_recall` exactly as stored. Its match requires the full
gold location string to appear as a case-insensitive substring of the joined submitted
`bug_locations` strings.

### 1.2 Gold-location parsing

Each gold location has the form:

```text
<function_identifier> <semantic_region_description>
```

The first whitespace-delimited token is the gold function identifier. It must be a
function defined in the case's buggy Python source. The remaining text is retained for
audit output but is not used by the normalized function/region rule.

### 1.3 Normalization and anchors

For every submitted `bug_locations` entry:

1. Apply Unicode NFKC normalization and case folding.
2. Treat backticks and punctuation other than underscore as token separators.
3. Extract explicit Python identifier tokens.
4. Extract line anchors in the forms `line N`, `lines N-M`, `N-M`, `N to M`, or
   `L<N>`; endpoints are inclusive.
5. Parse the buggy source and returned `fixed_code` with Python `ast`. Record each
   defined function's inclusive `lineno..end_lineno` span. A fixed source that does
   not parse contributes no fixed-code spans; buggy-source spans remain available.

An entry points to a gold function when either:

- an identifier token equals the gold function identifier; or
- an extracted line/range overlaps that function's span in the buggy source or the
  returned fixed source.

No fuzzy string distance, synonym list, semantic embedding, or model-specific pattern
is allowed.

### 1.4 Normalized score and miss classification

For each gold location, `normalized_location_match=1` if any submitted location entry
points to its gold function; otherwise it is 0. The case-level normalized recall is the
mean across gold locations. Function-level matching can credit multiple semantic gold
regions in the same function; this limitation must be stated beside the result.

Every unmatched gold location receives exactly one reason:

- `format_mismatch`: no submitted entry contains any recognized source-function
  identifier or line anchor;
- `wrong_location`: at least one submitted entry contains a recognized function or
  line anchor, but none points to the gold function.

Missing/unparseable response objects and empty `bug_locations` lists are
`format_mismatch`. Report frozen recall, normalized recall, and both miss counts side
by side for every alias.

## 2. A3 evidence-grounding rules

### 2.1 Frozen failure-reason audit

For each structured claim, assign one mutually exclusive frozen-rule reason using the
following precedence:

1. `no_citation`: `cited_ids` is empty;
2. `unknown_doc`: at least one cited ID is absent from the case fact table;
3. `attribute_key_mismatch`: every cited document is known, but at least one lacks the
   claim's exact attribute key;
4. `value_mismatch`: every cited document has the exact attribute key, but at least
   one accepted value fails the frozen `_equal` comparison;
5. `supported`: every cited document contains the exact key and an accepted value.

This table diagnoses the frozen all-citations-must-support rule; it does not alter its
score.

### 2.2 Canonical attribute-key function

Both gold fact keys and claim attribute keys are canonicalized by:

1. Unicode NFKC normalization;
2. splitting camelCase boundaries;
3. case folding;
4. replacing non-alphanumeric runs with one underscore; and
5. trimming leading/trailing underscores.

Then apply only this fixed synonym table:

| Inputs | Canonical key |
|---|---|
| `author`, `authors`, `lead_author`, `firstauthor`, `primary_author` | `first_author` |
| `methods`, `approach`, `approaches`, `technique`, `techniques` | `method` |
| `datasets`, `corpus`, `corpora`, `benchmark`, `benchmarks` | `dataset` |
| `metrics`, `measure`, `measures`, `evaluation_metric` | `metric` |
| `score`, `metric_value`, `result_value` | `value` |
| `topics`, `task`, `research_topic` | `topic` |
| `publication_year` | `year` |

Canonical gold keys (`dataset`, `first_author`, `method`, `metric`, `topic`, `value`,
and `year`) map to themselves. No other synonym, stemming, edit-distance, or semantic
mapping is allowed. Values continue to use the frozen `_equal` function without
relaxation.

### 2.3 Relaxed view R1: normalized attributes, all citations support

A claim is supported when it has at least one citation and every cited ID:

- exists in the fact table;
- contains an attribute whose canonical key equals the canonical claim attribute; and
- has at least one accepted value passing frozen `_equal`.

R1 changes attribute-key matching only. The frozen all-citations requirement remains.

### 2.4 Relaxed view R2: normalized attributes, any citation supports

A claim is supported when it has at least one citation and at least one cited ID is a
known document containing the canonical attribute and an accepted value passing frozen
`_equal`. Unknown, attribute-mismatched, or value-mismatched additional citations do
not negate support supplied by another citation.

R2 is the only relaxation of citation aggregation and is nested above R1. No third
grounding relaxation may be introduced in this analysis. Report frozen, R1, and R2
grounding side by side, plus the frozen failure-reason table.

## 3. A3 duplicate-ranking view

Retain these previously disclosed views:

- `frozen_all_case`: the stored frozen score, unchanged;
- `valid_ranking_only`: frozen score restricted to `ranking_valid=true`;
- `strict_invalid_zero`: frozen score for valid rankings and zero otherwise.

Add `deduplicated_first5` as a fourth post-hoc view:

1. Consider only the submitted `ranked_ids[:5]`; entries after position five never
   backfill the view.
2. Traverse in order and keep the first occurrence of each ID.
3. A known ID receives its frozen relevance gain; an unknown ID receives gain zero.
4. Remove later duplicates and append zero-gain positions until the gain vector has
   length five.
5. Compute nDCG with the frozen DCG formula and frozen ideal top-five denominator.
6. Compute grade-2 recall from distinct known grade-2 IDs kept in these five positions,
   divided by the number of grade-2 documents in the case.

The deduplicated view gives partial credit but does not make the response operationally
valid. Report all four nDCG views, corresponding grade-2 recall views where defined,
and the count of frozen values above 1.

## 4. A2 error taxonomy

Every field whose frozen `per_field` label is `wrong_value`, `missed`, or
`hallucinated` retains that frozen label and receives exactly one manual category.
Categories are assigned from the case design and erroneous field, not from alias.

Apply the following priority:

1. `unit_scale_conversion` when the requested field is in the fixed conversion set;
2. `conflict_resolution` when it is not in the conversion set but is in the fixed
   conflict set;
3. `field_omission` otherwise. This residual category includes failure to supply the
   requested direct/null value; the frozen label continues to distinguish missed,
   hallucinated, and wrong-value behavior.

### Fixed conversion fields

| Document family | Fields |
|---|---|
| `invoice` | `total_due_usd` |
| `clinical` | `dose_mg` |
| `shipment` | `weight_kg` |
| `job` | `salary_usd` |
| `incident` | `duration_minutes` |
| `grant` | `maximum_award_usd` |
| `property` | `monthly_rent_usd`, `area_sqm` |
| `conference` | `registration_usd` |
| `subscription` | `monthly_total_usd` |

### Fixed conflict-resolution fields

| Document family | Fields |
|---|---|
| `invoice` | `invoice_id` |
| `clinical` | `trial_id`, `enrollment` |
| `shipment` | `destination_city` |
| `job` | `requisition` |
| `incident` | `severity`, `affected_users` |
| `policy` | `coverage_limit_usd`, `jurisdiction` |
| `grant` | `agency` |
| `subscription` | `plan`, `cancelled` |

If a field appears in both conceptual mechanisms, conversion wins by the priority
above. Report a cross-tabulation of frozen error label by manual category, plus a
case/field audit table using aliases only in processed JSON.

## 5. Exploratory paired statistics

### 5.1 Pairing and alias order

Use the same 30 case IDs within a task. Sort case IDs lexicographically. Alias order is
`A < B < C`; every effect is `first_alias - second_alias`. Analyze all three pairs:
`A-B`, `A-C`, and `B-C`. Never drop a case for A1/A2 or for an all-case A3 view.

### 5.2 Binary tasks

- A1 outcome: frozen `functional_correct`.
- A2 outcome: frozen `content_correct`.
- Report each alias mean, paired mean difference, and the two discordant counts:
  `first_only` and `second_only`.
- Difference CI: 10,000 paired bootstrap samples. Each sample draws 30 case indices
  with replacement and takes the mean of the paired binary differences.
- The 95% percentile interval uses sorted bootstrap values at zero-based indices 250
  and 9,749.
- Exact two-sided McNemar p-value: with `n=first_only+second_only` and
  `k=min(first_only,second_only)`, use
  `min(1, 2 * P[Binomial(n, 0.5) <= k])`; when `n=0`, set `p=1`.

### 5.3 Continuous A3 views

Run paired tests for all three all-case views:

1. `frozen_all_case`;
2. `strict_invalid_zero`;
3. `deduplicated_first5`.

`valid_ranking_only` remains descriptive because validity can differ by alias and
would break the fixed 30-case pairing.

- Report each alias mean and paired mean difference.
- Difference CI: the same 10,000 paired bootstrap and percentile indices as above.
- Wilcoxon signed-rank: two-sided, zeros dropped (`zero_method="wilcox"`), no
  continuity correction, and the tie-corrected normal approximation
  (`method="approx"`). Record the SciPy version and effective nonzero pair count.
  If all paired differences are zero, set statistic 0 and p-value 1.

### 5.4 Deterministic bootstrap seeds

The base seed is `20261118`. For a comparison identified by the ASCII string
`<task>|<view>|<first>-<second>`, compute SHA-256 of that string, take the first eight
hex digits as an integer, and use `(20261118 + integer) mod 2**32` as the local seed.

### 5.5 Multiplicity families and Holm correction

Use two-sided alpha 0.05 and these families, defined before analysis:

- A1 family: three McNemar comparisons for frozen functional correctness (`m=3`).
- A2 family: three McNemar comparisons for frozen content correctness (`m=3`).
- A3 family: nine Wilcoxon comparisons—three alias pairs across the three all-case
  views above (`m=9`).

Within each family, sort raw p-values ascending. For rank `i` starting at one, compute
`(m-i+1)*p_i`; the Holm-adjusted sequence is the cumulative maximum of these values,
capped at 1, then mapped back to the original comparisons. Report raw p, adjusted p,
effect, and CI for every comparison, including ceiling/tie cases.

## 6. Required reporting and implementation checks

- The final report must explicitly separate prospective frozen results from all
  post-hoc/exploratory results.
- For every affected metric, place frozen, strict, and relaxed views in the same table.
- State the A2 ceiling (two aliases have frozen content correctness at the ceiling) and
  the A3 valid-only ranking ceiling described in the brief; do not infer equivalence
  from non-significance.
- Tests must cover normalization, line-range overlap, every grounding failure reason,
  both relaxed grounding rules, duplicate removal/padding, A2 taxonomy priority,
  exact McNemar, bootstrap determinism, Wilcoxon all-zero handling, and Holm mapping.
- Processed JSON remains blinded and contains aliases only. The final Markdown report
  may unblind via the frozen registry only after the complete numeric JSON object has
  been constructed.
- Source hashes for all raw JSONL inputs, the frozen scorer, this rules file, and the
  analysis code must be recorded in `posthoc.json`.

## Checkpoint 1 handoff

At this commit no post-hoc rescoring, per-alias aggregation, hypothesis test, or draft
post-hoc report has been run. Claude's checkpoint-1 review should evaluate this file
for model-agnosticism, hidden outcome tuning, and ambiguous rules before any analysis
implementation begins.
