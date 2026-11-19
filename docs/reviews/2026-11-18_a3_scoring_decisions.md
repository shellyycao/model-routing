# A3 Scoring Decisions for price-matched-v2 (user-approved 2026-11-18, before freeze)

These decisions were made before any price-matched-v2 model output existed. Claude and the user had
seen the earlier v2 outputs; disclose that in the protocol.

1. **A3 primary metric: strict nDCG@5.** A response that fails `ranking_valid` scores 0.
   - Deduplicated nDCG@5 (first occurrence, zero-padded) is reported as a secondary metric.
   - The operational success rate is reported separately.
   - The Pareto frontier and every "primary" table for A3 use the strict value.
2. **Rename `citation_accuracy` to `citation_validity`** everywhere in code, JSON and reports. It checks
   only that cited IDs exist in the candidate set, not that the cited content supports anything. Keep
   the old key name only in the frozen v2 outputs.
3. **A3 primary grounding: all-citations rule (R1).** A claim counts as grounded only if *every* cited
   document supports it.
   - R2 (any-citation) is reported as secondary.
   - **Why:** R2 was a post-hoc relaxation that compensated for the unspecified attribute vocabulary.
     The v2.2 prompt and schema now enforce the enum, so the strict rule is fair.
4. **Known limitation, accepted by the user:** A3 ranking is near ceiling (about 0.99) for strong models.
   A3 will mainly discriminate on validity and grounding. No dataset change.

**Related CP3b correction:** "cost per successful task" must use the task's primary *quality* success
(A1 functional_correct, A2 content_correct), not only operational success. A3 has a continuous primary
metric, so for A3 report cost per valid response and total cost ÷ sum of strict nDCG@5 instead. Label
each clearly.
