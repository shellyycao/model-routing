# Codex CP2 — Post-hoc draft ready

**Status:** STOPPED for Claude review
**Date:** 2026-11-18

## Completed

- Base model-agnostic rules: `ca9cce2`; CP1-required Wilcoxon-only amendment: `108df1f`.
- Deterministic implementation, blinded processed JSON, tests, and unblinded draft report: `d874d91`.
- Outputs: `results/processed/independent_v2/posthoc.json` and
  `results/reports/independent_v2_posthoc.md`.
- R-1 handled: per-alias attribute-key coverage is reported; frozen/R1/R2 grounding is explicitly a
  lower bound under an unspecified vocabulary and cannot be read as grounding ability.
- R-2 handled: zero-dropped, tie-corrected, no-continuity-correction Wilcoxon approximation is
  documented and tested against a hand-computed reference.
- Minor notes handled: bare-range-only and fixed-span-only counts, `task → topic` disclosure,
  conservative A3 Holm family, and defective frozen-A3 label.
- Full suite: **455 passed, 23 skipped**. Ten source hashes match; processed JSON remains alias-only.

## Deviations

SciPy is absent, so the committed standard-library equivalent is used. Implementation started before
the CP1 review was relayed, but no post-hoc rescoring ran until R-1/R-2 were handled and amendment
`108df1f` was committed.

## Review / open questions

Please spot-check report values against JSON, inspect Claude-favourable wording first, and confirm the
lower-bound wording. The future attribute-enum decision is intentionally deferred to CP3. No tier-matched
plan work or new model calls occurred; `docs/TIER_MATCHED_PLAN_DRAFT.md` remains untouched.
