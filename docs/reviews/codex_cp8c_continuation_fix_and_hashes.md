# Codex CP8c — Continuation Resume Fix and Hash Reproducibility

## Continuation Amendment

The crash was isolated to reconstruction of the original cleaning artifact for
`expB_price_matched_workflow_v3-c74b8e30d7cc56c5`. The original analysis handoff—not a new
interpretation—stores the unparseable summary as `null`, retains `cleaning_summary.json`, adds the
limitation `cleaning_summary.json is not valid JSON`, and preserves cleaning status `failed`. The
runner now copies those exact fields. A run directory is reusable only when it has no task record
and contains no files or symlinks; empty subdirectories are allowed, while any evidence payload
still raises. Offline construction succeeded for all 40 approved handoffs with no further failure.

The append-only state was not changed: 30 distinct records remain, ledger spend is
`$1.0880523`, failed attempts are zero, pending reservations are empty, and 10 calls remain. The
manifest retains status and approval, records this execution-only amendment, and requires new tag
`continuation-v1.1` while retaining `continuation-v1`. Resume command:

```bash
.venv/bin/python -m experiments.run_continuations --execute-approved-continuations
```

## Hash Audit and Equivalence

All four frozen manifests and nine tree-hash fields were audited. Only
`datasets/independent_v2` differed between legacy and bytecode-excluded hashing: frozen legacy
`831c081d…02c4a`, tracked-only `48487c66…1fcfb`, caused by two untracked `__pycache__/*.pyc`
files. Every relevant tag-to-HEAD tracked-file diff returned exit 0. The additive verifier requires
both immutable legacy agreement and fresh tracked-only agreement for dataset trees; all other
hashes use the original logic. The evidence explicitly depends on this original repository's Git
history.

## Verification

`experiments.verify_frozen_hashes` reports `pass` for 4/4 frozen manifests. Targeted coverage was
39/39. The final full suite was run twice: current working tree `559 passed, 23 skipped` (52.92 s), and a
temporary checkout assembled from tracked files plus CP8c changes with bytecode excluded
`559 passed, 23 skipped` (53.55 s). No model, AWS, Docker, or network call was made.
