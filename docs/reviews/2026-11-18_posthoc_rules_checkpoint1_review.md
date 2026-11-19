# Checkpoint-1 Review: `POSTHOC_V2_RULES.md` (commit `ca9cce2`)

**Reviewer:** Claude (an interested party: Claude Sonnet 4.6 is alias-hidden but evaluated).
**Inputs inspected:**
- the rules file;
- the frozen scorer;
- the A1/A3 gold formats;
- the A3 prompt;
- attribute-name counts pooled over **all** A3 responses, with no alias or per-model breakdown.

**Timing note:** this review happened after Codex had started implementing. The user relayed a
"finish the post-hoc analysis" instruction, which skipped the checkpoint-1 pause. Integrity still
holds, because the rules were committed before any per-alias computation. The report should state
this order.

## Verdict
**Approve with two required additions (R-1, R-2) and minor notes.** The rules are model-agnostic,
mechanical and well specified. Every finding below concerns construct validity, not bias.

## Confirmed by inspection
- **A1 all-zero recall is a scorer artifact.** Gold locations are phrases such as
  `clamp return expression`, `chunks range stop` and `dedupe set conversion`. The frozen rule requires
  that whole phrase as a substring of the model's text, which almost never happens. Using the first
  token as the function identifier (§1.2) is the right repair.
- **A3 gold fact keys** are exactly `dataset, first_author, method, metric, topic, value, year`
  (600 facts each), which matches §2.2.

## R-1 (required): A3 grounding is a specification gap, not only a matching gap
`prompts/independent_v2/a3_literature.txt` **never tells models which attribute names to use**, and
the response schema has a free-text `attribute: str`. Pooled over all responses, frequent attribute
strings include:

- `Dataset` 110, `dataset` 92 (both covered by the rules)
- `AUROC` 37, `MAE` 32, `Accuracy` 24, `F1 Score` 17, `F1` 11, `Test MAE` 7: a metric *name* used as the key for a numeric value
- `performance_metric` 21, `Result` 19, `result` 15, `performance` 5, `Performance Metric` 4
- `Method applied to <topic>` (several variants), `Dataset used` 4, and composites such as `Dataset: CellLife — MAE`

Many of these are not in the §2.2 synonym table, so R1/R2 will still undercount.
**Do not extend the table now.** Doing that after seeing this distribution is exactly the outcome
tuning the rules forbid. Instead, add the following to the report:

1. A descriptive **attribute-key coverage** metric per alias: the share of claims whose canonical
   attribute equals a gold key. It is computed with the existing §2.2 function and needs no new
   mapping.
2. A statement that the frozen, R1 and R2 grounding values are **lower bounds, conditional on an
   unspecified attribute vocabulary**. A3 grounding differences between aliases must not be read as
   grounding ability.
3. A forward note: any future protocol must give the attribute vocabulary in the prompt and schema
   (e.g. an enum). This affects `TIER_MATCHED_PLAN_DRAFT.md` and comparability with the 270 existing
   cells. That is a user decision.

## R-2 (required): document the Wilcoxon implementation deviation
§5.3 requires the SciPy method and version, but SciPy is not installed and the implementation is in the
standard library. Add a dated amendment (`posthoc-v2-rules-1.0.1`) that states the equivalence:
- zeros dropped;
- tie-corrected normal approximation;
- no continuity correction.

Also add a unit test against a hand-computed or known reference value. The amendment must not
change any other rule.

## Minor notes (fix or disclose)
- **§1.3 bare `N-M` anchor:** it can match non-line numbers in free text (e.g. `top 1-3`, value ranges).
  Count how many matches come only from a bare `N-M` anchor and disclose the count. Do not change the
  rule.
- **§1.3 fixed-source spans:** line numbers in the model's fixed code can map to a different function
  than in the buggy source. Disclose how many matches depend only on fixed-source spans.
- **§2.2 `task → topic`:** this is a judgment call. Report R1/R2 both with and without this single
  mapping, or disclose it as a limitation.
- **§5.5 A3 family:** the three views are highly correlated, so Holm with m = 9 is conservative.
  That is acceptable; say so.
- **§5.3:** the `frozen_all_case` view includes values above 1 from the known defect. Testing it is
  fine as a frozen reference, but label it as defective in the table.
