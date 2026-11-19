"""Build the additive frozen tree-hash reproducibility audit (offline only)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from src.bedrock.hash_equivalence import hash_tree_tracked


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results/processed/hash_reproducibility_amendment.json"


AUDIT = (
    ("results/processed/independent/independent_v2_freeze_manifest.json",
     "dataset_tree_sha256", "datasets/independent_v2", "independent-v2-frozen-v1.1", True),
    ("results/processed/independent/independent_v2_freeze_manifest.json",
     "prompt_tree_sha256", "prompts/independent_v2", "independent-v2-frozen-v1.1", False),
    ("results/processed/independent_v2/price_matched_v2_protocol_manifest.json",
     "hashes.dataset_tree_sha256", "datasets/independent_v2", "price-matched-v2-frozen-v1.1", True),
    ("results/processed/price_matched_workflow_protocol_manifest.json",
     "hashes.projects_tree", "datasets/projects", "price-matched-workflow-main-v1.2", True),
    ("results/processed/price_matched_workflow_protocol_manifest.json",
     "hashes.prompts_v3_tree", "prompts/v3", "price-matched-workflow-main-v1.2", False),
    ("results/processed/price_matched_workflow_protocol_manifest.json",
     "hashes.pricing_snapshots_tree", "results/raw/pricing", "price-matched-workflow-main-v1.2", False),
    ("results/processed/continuation_protocol_manifest.json",
     "hashes.projects_tree", "datasets/projects", "continuation-v1", True),
    ("results/processed/continuation_protocol_manifest.json",
     "hashes.prompts_v3_tree", "prompts/v3", "continuation-v1", False),
    ("results/processed/continuation_protocol_manifest.json",
     "hashes.replay_tree", "results/processed/diagnostics_posthoc_replay", "continuation-v1", False),
)


def nested_get(value: dict[str, Any], dotted: str) -> Any:
    for part in dotted.split("."):
        value = value[part]
    return value


def git_evidence(tag: str, directory: str) -> dict[str, Any]:
    command = ["git", "diff", "--quiet", tag, "HEAD", "--", directory]
    result = subprocess.run(command, cwd=REPO, check=False)
    return {
        "command": " ".join(command),
        "exit_code": result.returncode,
        "meaning": "exit 0: tracked files in the directory are unchanged from the freeze tag to HEAD",
        "repository": "original repository with its retained git history",
    }


def build_amendment() -> dict[str, Any]:
    entries = []
    for manifest_path, key, directory, freeze_tag, dataset_equivalence in AUDIT:
        manifest = json.loads((REPO / manifest_path).read_text())
        legacy = nested_get(manifest, key)
        tracked = hash_tree_tracked(REPO / directory)
        evidence = git_evidence(freeze_tag, directory)
        if evidence["exit_code"] != 0:
            raise ValueError(f"tracked content changed since {freeze_tag}: {directory}")
        entries.append({
            "manifest_path": manifest_path,
            "manifest_key": key,
            "directory": directory,
            "freeze_tag": freeze_tag,
            "manifest_required_tag": (
                manifest.get("required_tag") or manifest.get("main_required_tag")
                or manifest.get("expected_git_tag")
            ),
            "legacy_hash_as_frozen": legacy,
            "tracked_only_hash_now": tracked,
            "dataset_equivalence_applies": dataset_equivalence,
            "git_evidence": evidence,
        })
    return {
        "version": "hash-reproducibility-amendment-v1",
        "date": "2026-11-19",
        "scope": "additive verification metadata; no frozen manifest or expected hash is changed",
        "legacy_algorithm": "hash every matching file, including untracked Python bytecode",
        "tracked_algorithm": "same representation, excluding __pycache__/ and *.pyc",
        "equivalence_rule": (
            "For dataset-tree keys only, the frozen legacy value must equal this amendment's "
            "legacy value and the recomputed tracked-only value must equal this amendment's "
            "tracked-only value. Other hashes retain their original verification logic."
        ),
        "history_dependency": (
            "Equivalence evidence relies on the original repository's retained git history; "
            "a source archive without that history can recompute the tracked-only hash but cannot "
            "independently rerun the tag-to-HEAD git-diff evidence."
        ),
        "audited_frozen_manifests": sorted({row[0] for row in AUDIT}),
        "excluded_manifests": [{
            "path": "results/processed/independent_v2/tier_matched_protocol_manifest.json",
            "reason": "status is superseded_by_price_matched_v2_never_frozen",
        }],
        "tree_hashes": entries,
    }


def main() -> int:
    value = build_amendment()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(REPO)), "tree_hashes": len(value["tree_hashes"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
