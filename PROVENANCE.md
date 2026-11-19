# Provenance

This repository is a fresh-history snapshot of the working repository at commit `b723faa`
(tag `continuation-v1`, 2026-11-19). The original history is not included.

- Commit hashes and git tags cited in the docs and reports (for example `benchmark-v3-frozen` or
  `price-matched-v2-frozen-v1.1`) refer to the original repository, so they do not resolve here.
- Code that gates paid runs on an exact git tag cannot run here.
- Experiments still in progress when this snapshot was taken are not included.

## Hash reproducibility (resolved by additive amendment)

The protocol manifests record `dataset_tree_sha256`, computed by `hash_tree` over the dataset directory, which at
freeze time also held untracked `__pycache__/*.pyc` files. A fresh checkout therefore hashes differently. This was
fixed additively, without editing any frozen file: see `docs/HASH_REPRODUCIBILITY_AMENDMENT.md`,
`results/processed/hash_reproducibility_amendment.json` and `experiments/verify_frozen_hashes.py`.
The equivalence evidence (`git diff <freeze tag> HEAD -- <dataset dir>` is empty) relies on the original
repository's history, which is not included here.

Later work added after the first snapshot: the 40-cell continuation run, corrected Q1/Q2 views, the router
re-scoring with corrected labels, the failure taxonomy (post-hoc, exploratory), and the hash amendment.
