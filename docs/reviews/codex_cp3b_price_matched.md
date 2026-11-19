# Codex CP3b — Price-matched-v2 ready for review

**Status:** STOPPED at CP3b; not frozen and no calls authorized  
**Date:** 2026-11-18  
**Base commit:** `b01c8c5` (new work uncommitted; sandbox cannot write `.git`)

## Completed

- Verified the final three models offline from the saved official regional-standard price snapshots
  and account-access snapshot: Sonnet 4.6 `$3.30/$16.50`, Kimi K3 `$3.30/$16.50`, Grok 4.7
  `$2.20/$6.60`; all are AVAILABLE/AUTHORIZED. Global CRIS and non-standard SKUs are excluded.
- Reused the additive v2.2 scorer and A3 enum prompt from `f698ddf`; frozen `v2.py`, datasets and raw
  results are unchanged. Marked the tier-matched plan and manifest superseded without deleting them.
- Added the future freeze-gated runner: exactly **810** evaluation calls in repeat-major order with
  models interleaved, a mandatory stop after repeat 1, a shared reserve-then-settle `$100` cap and
  reasoning-usage capture. The current manifest/tag gate refuses before creating an AWS client.
- Listed the nine-call synthetic compatibility pilot; every call remains `not_run`, quality review is
  forbidden, and paid execution still needs explicit approval.
- Added actual cost per task, cost per operational success, and per-task quality–cost Pareto analysis,
  with tests. Full offline suite: **470 passed, 23 skipped**.

## Budget / open review points

- Static worst case: **$932.24** (819 logical calls, five attempts each, byte-bound input and full
  16,384 output tokens). Realistic estimate: **$26.22** (no retries; bytes/4 + 256 input; billed output
  including reasoning of A1 3,500, A2 1,000, A3 2,000 tokens/call). Runtime cap remains **$100** and
  may stop the run early; repeat-1 continuation requires projected total `pilot + 3×repeat1 <= $100`.
- Sonnet temperature 0 has prior evidence; Kimi/Grok parameter support remains pending the separately
  approved pilot. A failure stops the pilot rather than adding an unapproved call.
- No tag, model call, compatibility call or network request was made. CP3b manifest SHA-256:
  `4ed00bf602e2098fb21b4aba921d2416c00abc15cf92da4a6ef8631ca1f38215`.
