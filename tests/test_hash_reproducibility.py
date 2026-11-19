import json
from pathlib import Path

from experiments import verify_frozen_hashes as verifier
from src.bedrock.hash_equivalence import hash_tree_tracked
from src.bedrock.provenance import hash_tree


def test_hash_tree_tracked_excludes_only_bytecode_artifacts(tmp_path: Path):
    (tmp_path / "data.txt").write_text("protocol input\n")
    baseline = hash_tree_tracked(tmp_path)
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "module.cpython-312.pyc").write_bytes(b"variable bytecode")
    (tmp_path / "loose.pyc").write_bytes(b"more bytecode")
    assert hash_tree_tracked(tmp_path) == baseline
    assert hash_tree(tmp_path) != baseline
    (tmp_path / "data.txt").write_text("changed\n")
    assert hash_tree_tracked(tmp_path) != baseline


def test_amendment_audits_every_frozen_manifest_and_preserves_legacy_values():
    value = json.loads(verifier.AMENDMENT.read_text())
    assert len(value["audited_frozen_manifests"]) == 4
    assert len(value["tree_hashes"]) == 9
    assert all(row["git_evidence"]["exit_code"] == 0 for row in value["tree_hashes"])
    assert all(row["legacy_hash_as_frozen"] for row in value["tree_hashes"])
    assert value["excluded_manifests"][0]["reason"] == "status is superseded_by_price_matched_v2_never_frozen"


def test_all_frozen_hashes_reverify_with_dataset_equivalence():
    result = verifier.verify_all()
    assert result == {"status": "pass", "frozen_manifests_checked": 4, "errors": []}
