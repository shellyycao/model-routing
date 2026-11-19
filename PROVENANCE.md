# Provenance

This repository is a fresh-history snapshot of the working repository at commit `b723faa`
(tag `continuation-v1`, 2026-11-19). The original history is not included.

- Commit hashes and git tags cited in the docs and reports (for example `benchmark-v3-frozen` or
  `price-matched-v2-frozen-v1.1`) refer to the original repository, so they do not resolve here.
- Code that gates paid runs on an exact git tag cannot run here.
- Experiments still in progress when this snapshot was taken are not included.

## Known issue: one frozen hash is not reproducible from tracked files

The protocol manifests record `dataset_tree_sha256`. It was computed by `hash_tree` over the whole
dataset directory, which at the time also held untracked Python bytecode (`__pycache__/*.pyc`).
A fresh checkout has no such files, so the hash comes out different, and 7 tests that re-verify it
fail in this snapshot (`tests/test_price_matched_v2.py` and `tests/test_price_matched_v2_results.py`).
All other tests pass.

The dataset files themselves did not change: in the original repository,
`git diff independent-v2-frozen-v1.1 HEAD -- datasets/independent_v2` is empty, and the same holds
against `price-matched-v2-frozen-v1.1`. The file hashes in the manifests other than
`dataset_tree_sha256` were not re-verified against this snapshot, and neither was
`dataset_tree_sha256` for any dataset directory other than `datasets/independent_v2`. Fixing this properly
(hashing tracked files only) would be a protocol amendment, so it has not been done here.
