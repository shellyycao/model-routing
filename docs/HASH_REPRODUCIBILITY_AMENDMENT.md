# Frozen Hash Reproducibility Amendment

## Status and Scope

This 2026-11-19 amendment is additive verification metadata. It does not edit a frozen manifest,
frozen runner, expected hash, or `src/bedrock/provenance.py`. It audits all four frozen protocol
manifests and supplies a reproducible equivalence for dataset-tree hashes whose legacy value could
include interpreter artifacts. The superseded tier-matched manifest was inspected but excluded
because its recorded status is `superseded_by_price_matched_v2_never_frozen`.

## Root Cause

Legacy `hash_tree` hashes every matching file beneath a directory. At the Independent-v2 freezes,
`datasets/independent_v2` contained two untracked files under `__pycache__/`. Their bytes entered
the frozen value `831c081d…02c4a`; a clean checkout omits those files and therefore cannot reproduce
that legacy value even though every tracked dataset file is unchanged.

The new `src/bedrock/hash_equivalence.py::hash_tree_tracked` uses the same sorted relative-path and
file-hash representation, but skips any `__pycache__/` content and every `*.pyc`. For
`datasets/independent_v2`, its reproducible value is `48487c66…1fcfb`. The other audited trees had
identical legacy and tracked-only values.

## Audited Tree Hashes

The machine-readable record is
`results/processed/hash_reproducibility_amendment.json`. It records, for every row, the manifest
path, nested key, directory, frozen legacy value, current tracked-only value, freeze/evidence tag,
and the exact `git diff --quiet <tag> HEAD -- <directory>` command and exit code.

| Frozen manifest | Tree keys audited | Evidence tag |
| --- | --- | --- |
| `independent/independent_v2_freeze_manifest.json` | dataset, Independent-v2 prompts | `independent-v2-frozen-v1.1` |
| `independent_v2/price_matched_v2_protocol_manifest.json` | dataset | `price-matched-v2-frozen-v1.1` |
| `price_matched_workflow_protocol_manifest.json` | projects, v3 prompts, pricing snapshots | `price-matched-workflow-main-v1.2` |
| `continuation_protocol_manifest.json` | projects, v3 prompts, diagnostic replay | `continuation-v1` |

The continuation replacement manifest requires `continuation-v1.1`, which does not exist until
Claude commits and tags this amendment. Its tree evidence therefore uses retained predecessor tag
`continuation-v1`; the JSON records both the evidence tag and the replacement required tag.

## Equivalence Rule

For a dataset-tree key only, verification succeeds when both statements hold:

1. the manifest's immutable legacy value equals the amendment's recorded legacy value; and
2. a fresh `hash_tree_tracked` computation equals the amendment's recorded tracked-only value.

No expected value is replaced. Prompt, pricing, replay, source-file and all other hashes continue
through their original hash logic without an exception. This makes a missing or edited tracked
dataset file fail, while making untracked Python bytecode irrelevant.

## Verification Procedure

Run:

```bash
.venv/bin/python -m experiments.verify_frozen_hashes
```

The verifier checks every frozen manifest. The shared pytest fixture in `tests/conftest.py` applies
the same equivalence only to the Independent-v2 dataset-tree lookup used by price-matched-v2 tests;
it delegates every other path and pattern to legacy `hash_tree` and leaves all other assertions
unchanged. Tests also construct a checkout from tracked files plus the CP8c changes, excluding
bytecode, and run the full suite there.

## Limitations

The tag-to-HEAD equivalence evidence relies on the original repository's retained Git history. A
clean source archive can recompute and verify the tracked-only values, but without that history it
cannot independently rerun the historical `git diff --quiet` checks. This limitation is explicit
in every machine-readable evidence row.
