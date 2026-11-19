# Executor Phase 2 results (post-hoc / exploratory)

Gate: PASSED first. All 50 (original) and 64 (price-matched) saved validations reproduced record by
record (actual feasible values and `direction_correct`), pooled direction 22/50 and 31/64 with
`direction_correct["feasible"]`, S2+S3 pooled, effective (rerun-resolved) records. Rebuilt per-run
labels (156 per group) matched `corrected_q2.json` repeat-0 rows for all four views.

Key numbers (pooled, primary v3, k/n frozen -> corrected):
- Router direction: original 22/50 -> 21/50; price-matched 31/64 -> 24/64. Corrected labels do not
  repair the router; they lower both (3 and 8 predictions changed correctness/sign).
- Baselines (v3, corrected): always-tie 26/50 and 36/64 beats the router in both groups; always-less
  18/50 and 25/64; training-only stage-rate (frozen Part A) 18/50 and 29/64. v3.1 gives the same
  picture (router 20/50 and 20/64 corrected; always-tie 22/50 and 46/64). Router vs always-more is
  the only clear router win (exact McNemar p=0.006, original).
- Failure taxonomy: 322 (original) and 168 (price-matched) non-passed effective units, reconciled to raw
  (14 stages of 5 replaced Docker-void originals excluded and audited). Unexplained residual 0/322 and
  0/168 (all units) and 0/193 and 0/133 (failed only); the residual review sample is therefore empty.
  Int64 = 26 + 37 = 63; rounding 4 + 11 = 15; q7 13 + 17 = 30 (match the diagnostics).

Revision after manager review (no number changed; numeric diff of the three JSON outputs vs 779c701:
0 changed leaves, 0 removed, 144 added in the router JSON (per-strategy 3x3 tables) and 20 added in the
taxonomy JSON (artifact-like excluding blocked, blocked share); sample list unchanged):
- Reports now state the taxonomy caveats (catch-all `genuine_validator_mismatch`, zero residual follows
  from the rules, blocked units inflate the artifact-like share). Artifact-like share is 172/322 with
  blocked and 43/322 without (original), 100/168 and 65/168 (price-matched). Roots of blocked units are
  mostly non-artifact in the original group but mostly int64 in the price-matched group (29/35).
- Router report states plainly that always-tie beats the router (corrected v3: 26/50 vs 21/50, 36/64 vs
  24/64), no repair/validation claim, and the continuation/cleaning-recovery dependence.
- Baseline (c) now uses `norm_project` and `build_training_view` (raises on unknown project); the
  reconciliation is asserted in code; dead field dropped; new edge tests added.
- Note: the retained-void-rerun flag never fires (resolve_workflow_reruns keeps the void original, not the
  void rerun, as the effective record); no such case exists in the data.

Surprising or ambiguous:
- The residual is zero because every failed record carries a `failure_type` that maps to rules 7-9. The
  large `genuine_validator_mismatch` category (81 and 66) is therefore a broad catch-all by failure_type,
  not a check that the model was wrong.
- Rule 8 matches `structural_ok is False` on many execution errors; precedence puts them in rule 7.
  Pre-precedence multi-match counts are in the JSON.
- Rule 7's exception-class rule was read as "last non-empty line with a colon" for both stderr and
  `failure_detail`; I applied it to stderr first, then `failure_detail`.
- S2 router accuracy is very low (2/16, original); per-project accuracy is lopsided (0/16 for one
  project). Intervals are clustered-optimistic as stated in the rules.
- infrastructure_void is 0 in both groups: the 5 Docker voids sit in the price-matched replaced
  originals, which are excluded from the units by D4 and shown in the audit table.
