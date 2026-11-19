# Codex CP7g — Report updates

## Review notes addressed

1. The CP7f Part A table now names Sonnet 4.6, Kimi K3, and GLM 5 instead of reusing A/B/C,
   avoiding collision with the original model group's aliases.
2. The key findings now place token-based cost direction (64/64) beside naive unit-price ordering
   (56/64). The text labels both post-hoc/descriptive and gives the bounded interpretation that
   Sonnet and Kimi share unit prices but differ in observed token volume.
3. The workflow comparison now reports both denominators—single-model 3/12 and cross-model 38/96
   under primary v3—and explicitly says the observed direction differs from the original group's
   near-equality without establishing a causal mixing benefit.
4. `docs/FINAL_REPORT.md` gained only the requested additions: conclusion 9 (pre-registered
   protocol; exploratory strength), a “Replication with a second model group” results section with
   source paths, and verification-guide row 9.

## Verification

The CP7f renderer was updated so regeneration preserves these corrections, and derived source
hashes were refreshed. Tests cover the three model names, the 64/64 versus 56/64 comparison, and
the 3/12 versus 38/96 denominators. No raw/frozen data, paid-run result, or existing unrelated
FINAL_REPORT text was changed. Full suite: **530 passed, 23 skipped**. No model, Docker, or network
call was made.
