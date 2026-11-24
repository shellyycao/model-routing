# Codex CP7e — Docker void rerun amendment

## Authorization and scope

The completed main run has 36/36 Part A and 156/156 original Part B records. Five repeat-0 cells
are `void_infra` solely because an approximately two-minute Docker daemon outage made `docker info`
time out: energy `C-C-A`, `C-C-B`, `C-C-C`, and retail `A-A-A`, `A-A-B`. On 2026-11-19 the user
gave standing authorization (translated: **“No need for my approval; if it's a Docker problem, just re-run it”**;
the exact original wording is in the manifest).
No rerun was executed in this turn.

## Rerun implementation and analysis rule

Added `--rerun-docker-voids`. It selects only original repeat-0 voids with both sandbox-gate refusal
and Docker-daemon/`docker info` failure, then freezes all five targets before execution. Each target
uses the same path, repeat index, registry, prompts, parameters, pinned image, shared ledger, and
$100 cap; `infra_attempt=1` supplies a new run ID and `rerun_of` records the original ID. Existing
reruns are skipped, so interrupted execution is resumable and no cell can be rerun twice. The first
156 JSONL lines are hash-checked and never rewritten; reruns append up to five lines.

The analysis rule is `successful_rerun_replaces_void`: a rerun whose outcome is not `void_infra`
becomes the effective `(project, path, repeat)` cell; if it is again void, the original remains the
effective cell. Raw originals and reruns remain present, and processed metadata reports the mapping.
Offline routing now refuses until all five approved rerun records exist, then resolves back to 156
effective cells.

## Verification and execution handoff

The manifest remains `main_frozen_paid_execution_approved`, preserves the user's main approval and
$100 cap, and adds the exact rerun authorization, five original run IDs, immutable 156-line prefix
hash, append-only/analysis rules, and required tag `price-matched-workflow-main-v1.2`. Tags `v1`
and `v1.1` remain. Tests cover selection specificity, idempotency, append-only preservation, both
analysis-resolution branches, manifest reproducibility after an appended rerun, legacy JSON
compatibility, and the tag/hash gate. Full suite: **524 passed, 23 skipped**.

After commit and tag creation, the exact approved command is:

```bash
.venv/bin/python -m experiments.run_price_matched_workflow --rerun-docker-voids
```

This preparation made no model or network calls.
