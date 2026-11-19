# Codex CP3 — Tier-matched protocol ready for review

**Status:** STOPPED at CP3; not frozen and no calls authorized  
**Date:** 2026-11-18  
**Base commit:** `01bf3d3`

## Completed

- Applied the fixed selection rule offline to the two official price snapshots and the saved discovery
  record. Five slots are conditionally selected; Amazon-high is empty with no near-miss substitution.
  The 55-row table, reasons, source URLs and SHA-256 hashes are in `tier_matched_selection.json`.
- Added scorer v2.2 without changing frozen `v2.py`: normalized A1 location scoring, deduplicated A3
  ranking with strict operational validity, and R2 grounding with R1 retained as a diagnostic.
- Kept A1/A2 prompts unchanged; added the seven-value A3 attribute enum in a new prompt and schema.
- Added a plan-by-default, execution-locked runner, unrun probe request skeletons, offline plan and CP3
  hash manifest. Requested design: 5 selections + 3 anchors × 90 × 3 = 2,160 evaluation calls.
- Full offline suite: **461 passed, 23 skipped**. Manifest SHA-256:
  `68ad8ff568063b93749eaf2ba4ad780cb6da66a7e20546c0c65096bcdf73eaaf`.

## Deviations / open decisions

- Strict worst case, including two probe-call reservations per model and five-attempt retry reserves,
  is **$1,076.81**, above the final $100 cap. Proposed scope cut: only the three low-tier selections,
  **$88.69** worst case. It preserves low-tier RQ1 but defers high tiers, anchors, RQ2/RQ3 and protocol-
  effect separation. Codex did not adopt it; user/manager approval is required.
- Access probes were listed but not run, as instructed. New-model temperature support remains pending;
  a temperature omission is allowed only after a validation error and must be recorded.
- No tag was created and no model/network call occurred. A commit was attempted but this session cannot
  write `.git/index.lock` (`Operation not permitted`), so CP3 work remains uncommitted on `01bf3d3`.
