# Codex CP8b — Continuation Freeze and Corrected Q1

## Approval Freeze

Generated `results/processed/continuation_protocol_manifest.json` with status
`continuation_frozen_paid_execution_approved`. It records Claude's question (translated: “Spending cap $15, expected actual about
$1.41; OK to re-run these 40?”) and the user's reply (translated: “Approved”) on 2026-11-19; the exact original wording is in the manifest. The manifest
freezes 40 logical calls, the separate $15 reserve-then-settle ledger, all 40 eligible replay/code/
output hashes, the inventory hash, protocol/code/data trees, original settings, and exact required
tag `continuation-v1`. Simulated verification passes when HEAD is reported at that tag; this turn
did not create it.

Execution command after Claude commits and tags:

```bash
.venv/bin/python -m experiments.run_continuations --execute-approved-continuations
```

Task records append to `results/raw/workflow_continuations/continuation_v1.jsonl`; per-run artifacts
go under `results/raw/continuations/runs/`, invocations to
`results/raw/continuations/invocations.jsonl`, and spend to the separate
`results/raw/ledgers/continuations.json`. Exactly 40 task-record lines and 40 distinct
`continued_from` values mean complete; invocation lines are not the progress denominator.

## Corrected Q1

Implemented `experiments/analyze_corrected_view.py` and generated alias-only
`results/processed/corrected_view.json` plus the name-rendered
`results/reports/corrected_view.md`. Across 1,008 fixed stage opportunities, attribution is: 518
frozen passes, 55 unique int64 recoveries, 15 unique stated-precision recoveries, 30 unique v3.1
recoveries, and 390 not recovered. The 15 rounding and 30 q7 sets are asserted disjoint.

The largest artifact-sensitive rows are GLM 5 Part A analysis, 0/4 frozen to 4/4 combined, and GLM
5 price-matched Part B analysis, 27/60 to 56/60. Original Part B analysis adds 9 Nova Pro and 2
gpt-oss-120b int64-recovered passes. These are explicitly stage-level post-hoc sensitivities; no
corrected Part B feasibility number was computed.

## Review Notes

All three CP8a notes are now in `docs/CONTINUATION_PROTOCOL.md` and the manifest guard:

1. the 11 recovered cleaning cells will enter exact corrected Part B using their already observed
   downstream outcomes, with no duplicate calls;
2. the future report must disclose that those downstream handoffs saw upstream cleaning status
   `failed`, so their outcomes are conditional on that label; and
3. exact corrected Part B analysis is prohibited until all 40 continuation task records exist.

## Verification

Added tests for alias-only JSON, fixed denominators, attribution sums and selected corrected counts;
the manifest test verifies exact approval wording, 40 replay entries, $15 ledger scope, hash gate,
and successful verification under a mocked `continuation-v1` tag. Full suite: **552 passed, 23
skipped in 53.98s**. No model, Bedrock, Docker, or network call was made, and no frozen/raw file was
modified.
