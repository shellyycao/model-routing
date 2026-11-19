"""Re-verify every frozen protocol manifest, with additive dataset-tree equivalence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiments import run_continuations as continuation
from experiments import run_independent_v2_benchmark as independent
from experiments import run_price_matched_v2 as price_v2
from experiments import run_price_matched_workflow as workflow
from src.bedrock.hash_equivalence import hash_tree_tracked
from src.bedrock.models import load_registry
from src.bedrock.provenance import hash_file, hash_json, hash_tree, models_fingerprint


REPO = Path(__file__).resolve().parents[1]
AMENDMENT = REPO / "results/processed/hash_reproducibility_amendment.json"


def _check(errors: list[str], actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        errors.append(f"{label}: expected {expected!r}, got {actual!r}")


def _amendment_index() -> dict[tuple[str, str], dict[str, Any]]:
    value = json.loads(AMENDMENT.read_text())
    return {(row["manifest_path"], row["manifest_key"]): row for row in value["tree_hashes"]}


def _dataset_tree(errors: list[str], index: dict, manifest_path: str, key: str,
                  manifest_value: str, directory: Path) -> None:
    row = index.get((manifest_path, key))
    if not row or not row.get("dataset_equivalence_applies"):
        errors.append(f"{manifest_path}:{key}: no dataset equivalence record")
        return
    _check(errors, manifest_value, row["legacy_hash_as_frozen"], f"{manifest_path}:{key}:legacy")
    _check(errors, hash_tree_tracked(directory), row["tracked_only_hash_now"],
           f"{manifest_path}:{key}:tracked")


def _verify_independent(errors: list[str], index: dict) -> None:
    rel = "results/processed/independent/independent_v2_freeze_manifest.json"
    value = json.loads((REPO / rel).read_text())
    _dataset_tree(errors, index, rel, "dataset_tree_sha256", value["dataset_tree_sha256"], independent.DATA)
    _check(errors, hash_tree(independent.PROMPTS), value["prompt_tree_sha256"], f"{rel}:prompt_tree_sha256")
    checks = {
        "response_schema_and_scorer_sha256": REPO / "src/independent/v2.py",
        "runner_sha256": REPO / "experiments/run_independent_v2_benchmark.py",
        "usage_guard_sha256": REPO / "src/bedrock/usage.py",
        "protocol_document_sha256": REPO / "docs/INDEPENDENT_V2_PLAN.md",
        "a3_first_review_results_sha256": REPO / "results/processed/independent/a3_v2_label_review_results.json",
        "a3_targeted_rereview_results_sha256": REPO / "results/processed/independent/a3_v2_label_rereview_results.json",
    }
    for key, path in checks.items():
        _check(errors, hash_file(path), value[key], f"{rel}:{key}")
    _check(errors, hash_json(models_fingerprint(load_registry())), value["model_behavior_sha256"],
           f"{rel}:model_behavior_sha256")


def _verify_protocol_hashes(errors: list[str], index: dict, rel: str, frozen: dict[str, Any],
                            current: dict[str, Any], dataset_keys: dict[str, Path]) -> None:
    for key, directory in dataset_keys.items():
        _dataset_tree(errors, index, rel, f"hashes.{key}", frozen[key], directory)
    for key, expected in frozen.items():
        if key not in dataset_keys:
            _check(errors, current.get(key), expected, f"{rel}:hashes.{key}")


def verify_all() -> dict[str, Any]:
    errors: list[str] = []
    index = _amendment_index()
    _verify_independent(errors, index)

    rel = "results/processed/independent_v2/price_matched_v2_protocol_manifest.json"
    frozen = json.loads((REPO / rel).read_text())["hashes"]
    _verify_protocol_hashes(errors, index, rel, frozen, price_v2.protocol_hashes(),
                            {"dataset_tree_sha256": price_v2.DATA})

    rel = "results/processed/price_matched_workflow_protocol_manifest.json"
    frozen = json.loads((REPO / rel).read_text())["hashes"]
    _verify_protocol_hashes(errors, index, rel, frozen, workflow.protocol_hashes(),
                            {"projects_tree": REPO / "datasets/projects"})

    rel = "results/processed/continuation_protocol_manifest.json"
    frozen = json.loads((REPO / rel).read_text())["hashes"]
    _verify_protocol_hashes(errors, index, rel, frozen, continuation.protocol_hashes(),
                            {"projects_tree": REPO / "datasets/projects"})
    return {"status": "pass" if not errors else "fail", "frozen_manifests_checked": 4,
            "errors": errors}


def main() -> int:
    result = verify_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
