# Codex CP3c — A3 scoring fixes ready

**Status:** STOPPED for CP3c review; not frozen and no calls authorized  
**Date:** 2026-11-18  
**Base commit:** `31c82f3` (new work uncommitted; sandbox cannot write `.git`)

## Completed

- Implemented all four user-approved decisions from
  `docs/reviews/2026-11-18_a3_scoring_decisions.md` and added that file to the protocol hashes.
- A3 `ndcg_at_5` is now strict primary (`ranking_valid=false` → 0);
  `deduplicated_ndcg_at_5` is secondary. The price-matched Pareto frontier reads only the strict key.
- Replaced the prospective v2.2 key `citation_accuracy` with `citation_validity`; frozen v2 code and
  outputs retain their historical key unchanged.
- A3 `evidence_grounding` now uses R1 (all citations); R2 is exposed only as
  `evidence_grounding_any_citation`.
- Cost denominators now use A1 `functional_correct`, A2 `content_correct`, and for A3 separately
  `ranking_valid` responses and summed strict nDCG points. Cost per operational success remains a
  labelled secondary.
- Updated `docs/PRICE_MATCHED_V2_PLAN.md`, regenerated the CP3c plan/manifest, and added tests for strict
  scoring, R1/R2 roles, key renaming, task-specific cost denominators, and the strict A3 Pareto axis.
  Full suite: **474 passed, 23 skipped**.

## Deviations / open points

- No deviation from the four decisions. The accepted A3 ceiling limitation and prior exposure to v2
  outputs are disclosed in the protocol.
- No tag, model call, compatibility-pilot call or network request was made. Frozen `v2.py`, datasets,
  existing raw records and frozen v2 outputs are unchanged.
- Next gate is Claude's light CP3c check; the paid compatibility pilot still requires explicit user
  approval. Manifest SHA-256:
  `5097238b503cc9a33edf71876ff033d01762a4ab3a2bdbab1ae1695bd16ff270`.
