# Post-hoc v2 Analysis Brief (for Codex; Claude reviews)

**Status:** brief only, no analysis has been run yet. Written 2026-11-18.
**Role split:** Codex designs and runs the analysis. Claude reviews only at the two checkpoints below.
**Why:** Claude Sonnet 4.6 and gpt-oss-120b (OpenAI) are both models under test, so neither agent is neutral.
The safeguards below reduce bias through process, not through the choice of agent.

## Hard constraints

- No new model calls. Everything is offline over `results/raw/independent_v2/` and saved artifacts.
- Do not modify frozen raw records, the frozen scorer `src/independent/v2.py`, datasets, or the tag
  `independent-v2-frozen-v1.1`. New code goes in new modules (e.g. `src/independent/v2_posthoc.py`,
  `experiments/analyze_independent_v2_posthoc.py`).
- Every output is labelled **post-hoc / exploratory**. The v2 plan pre-registered no hypothesis tests.

## Bias safeguards (apply to every step)

1. **Rules before data.** For each rescoring rule, write it in
   `docs/POSTHOC_V2_RULES.md` and **commit it before computing any per-model result** under that rule.
   Looking at scorer mechanics and gold-label formats is allowed; looking at per-model outcomes is not.
2. **Blinding.** Analysis code and intermediate outputs use aliases A/B/C only. Do not print model names
   until all numbers are final; unblinding happens only in the final report.
3. **No headline picking.** Report frozen, strict and relaxed views side by side for every metric.
   A relaxed view never replaces the frozen value.
4. **Rules are model-agnostic.** No rule may reference a model alias or be tuned on a single case.

## Work items

### 1. A1 bug-location recall is 0.000 for all three models
Scorer (`score_debugging_v2`): each gold `bug_locations` string must appear as a case-insensitive
substring of the joined `response.bug_locations`. All-zero across every model points to a format
mismatch, not model failure. To do:
- Compare gold `bug_locations` format with the response format (mechanics only, aliases hidden).
- Pre-register a normalized match rule (e.g. function-name extraction, line-range overlap), commit it, then rescore.
- Classify misses as `wrong_location` or `format_mismatch`.

### 2. A3 evidence grounding is near zero for two models
Scorer (`_claim_supported`): every cited doc must have `claim.attribute` as an **exact key** in its
fact dict, and `claim.value` must `_equal` an accepted value. Candidate causes are attribute-name
mismatches (synonyms, casing), value wording, and the all-citations-must-support rule.
- Tabulate the failure reason per claim: `no_citation`, `unknown_doc`, `attribute_key_mismatch`, `value_mismatch`.
- Pre-register at most two relaxed rules (e.g. normalized attribute keys; any-citation-supports), commit them, then rescore.

### 3. A3 duplicate-ranking defect (already disclosed)
Keep the existing frozen, valid-only and strict invalid=0 views. Add a deduplicated-ranking view
(first occurrence kept, padded with gain 0) as a fourth, clearly labelled view.

### 4. A2 errors for the one alias below 100%
Classify each wrong field by the existing `per_field` labels (`wrong_value`, `missed`, `hallucinated`),
plus a manual category: unit/scale conversion, conflict resolution, or field omission.
Write the category definitions down before classifying.

### 5. Paired statistics (exploratory)
- Per task, every pair of aliases on the same 30 cases:
  - A1, A2 binary primary: exact McNemar test, discordant-pair counts, paired difference with 95% CI.
  - A3 continuous: paired bootstrap of the mean difference (fixed seed, 10,000 resamples) and a Wilcoxon signed-rank test.
- Apply a Holm correction across all comparisons in a family (state the family definition up front).
- Expect most pairs to be non-significant at n=30; report the CIs, not just p-values.
- State the ceiling effects explicitly (A2 has two aliases at 100%; A3 valid-only nDCG ≥ 0.99 for all).

## Deliverables
- `docs/POSTHOC_V2_RULES.md`, committed before rescoring (checkpoint 1).
- `experiments/analyze_independent_v2_posthoc.py` (deterministic, reproducible).
- `results/processed/independent_v2/posthoc.json`.
- `results/reports/independent_v2_posthoc.md`, which separates the pre-registered results from the post-hoc results.
- Tests in `tests/test_independent_v2_posthoc.py`; frozen tests must still pass.

## Downstream use
The committed rules become the prospective scorer v2.2 for the planned tier-matched run
(`docs/TIER_MATCHED_PLAN_DRAFT.md`). Finish and review this work before that protocol is frozen.

## Review checkpoints (Claude)
1. **After the rules are committed, before rescoring:** Claude reviews `POSTHOC_V2_RULES.md` for
   model-agnosticism and for anything that could be tuned to the outcome.
2. **After the draft report:** Claude reviews the numbers against the code and checks the wording for
   overclaiming. Claude flags Claude-favourable wording first.
