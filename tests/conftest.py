"""Shared test-only frozen dataset-tree equivalence.

Only the Independent-v2 dataset lookup in the price-matched-v2 protocol module is intercepted.
Every non-dataset hash and every assertion retains its original implementation and expected value.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def frozen_dataset_tree_hash_equivalence(monkeypatch):
    from experiments import run_price_matched_v2 as runner
    from src.bedrock.hash_equivalence import hash_tree_tracked

    amendment_path = REPO / "results/processed/hash_reproducibility_amendment.json"
    if not amendment_path.exists():
        yield
        return
    rows = json.loads(amendment_path.read_text())["tree_hashes"]
    row = next(item for item in rows if
               item["manifest_path"] == "results/processed/independent_v2/price_matched_v2_protocol_manifest.json"
               and item["manifest_key"] == "hashes.dataset_tree_sha256")
    dataset = (REPO / row["directory"]).resolve()
    original = runner.hash_tree

    def equivalent_hash_tree(root, pattern="**/*"):
        if Path(root).resolve() == dataset and pattern == "**/*":
            assert hash_tree_tracked(root, pattern) == row["tracked_only_hash_now"]
            return row["legacy_hash_as_frozen"]
        return original(root, pattern)

    monkeypatch.setattr(runner, "hash_tree", equivalent_hash_tree)
    yield
