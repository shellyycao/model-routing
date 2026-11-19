"""Build the immutable Independent-v2 protocol hash manifest (offline only)."""

from __future__ import annotations

import json
from pathlib import Path

from experiments import run_independent_v2_benchmark as runner
from src.bedrock.models import load_registry
from src.bedrock.provenance import hash_file


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results/processed/independent/independent_v2_freeze_manifest.json"


def build_manifest() -> dict:
    first_review = json.loads((REPO / "results/processed/independent/a3_v2_label_review_results.json").read_text())
    rereview = json.loads((REPO / "results/processed/independent/a3_v2_label_rereview_results.json").read_text())
    dataset_manifest = json.loads((runner.DATA / "manifest.json").read_text())
    cases = {task: runner.load_cases(task) for task in ("a1", "a2", "a3")}
    planned = runner.plan()

    if first_review["grade_agreement"] != 167 or first_review["grade_disagreement"] != 13:
        raise ValueError("locked first-pass review summary changed")
    if rereview["review_status"] != "complete_locked_unblinded" or rereview["grade_disagreement"]:
        raise ValueError("targeted rereview is incomplete")
    if dataset_manifest.get("status") != "frozen" or dataset_manifest.get("version") != "independent-v2-1.0":
        raise ValueError("dataset manifest is not final")
    if any(case.get("label_status") != "human_adjudicated" for case in cases["a3"]):
        raise ValueError("not all A3 cases are human adjudicated")
    if {task: len(rows) for task, rows in cases.items()} != {"a1": 30, "a2": 30, "a3": 30}:
        raise ValueError("unexpected case counts")
    if planned["planned_logical_calls"] != runner.MAX_LOGICAL_CALLS:
        raise ValueError("unexpected logical call plan")
    if planned["worst_case_output_tokens"] != runner.MAX_OUTPUT_TOKENS:
        raise ValueError("unexpected output-token plan")

    registry = load_registry()
    manifest = {
        "protocol": "Independent Benchmark v2",
        "version": "independent-v2-1.1",
        "freeze_status": "protocol_frozen_paid_execution_approved_not_started",
        "freeze_date": "2026-11-18",
        "expected_git_tag": runner.FROZEN_TAG,
        **runner._expected_freeze_values(),
        "protocol_document_sha256": hash_file(REPO / "docs/INDEPENDENT_V2_PLAN.md"),
        "a3_first_review_results_sha256": hash_file(
            REPO / "results/processed/independent/a3_v2_label_review_results.json"
        ),
        "a3_targeted_rereview_results_sha256": hash_file(
            REPO / "results/processed/independent/a3_v2_label_rereview_results.json"
        ),
        "case_counts": {task: len(rows) for task, rows in cases.items()},
        "difficulty_counts": {
            task: {tier: sum(case["difficulty"] == tier for case in rows) for tier in ("easy", "medium", "hard")}
            for task, rows in cases.items()
        },
        "planned_logical_calls": planned["planned_logical_calls"],
        "estimated_input_tokens": planned["estimated_input_tokens"],
        "worst_case_output_tokens": planned["worst_case_output_tokens"],
        "maximum_api_attempts_with_five_attempt_retry_policy": planned[
            "maximum_api_attempts_with_five_attempt_retry_policy"
        ],
        "pricing_status_at_freeze": registry.pricing_status(),
        "paid_execution_approved": True,
        "paid_execution_approval_date": "2026-11-18",
        "paid_execution_approval_budget_usd": runner.MAX_BUDGET_USD,
        "paid_calls_made": 0,
    }
    return manifest


def main() -> int:
    manifest = build_manifest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUT.relative_to(REPO)),
        "version": manifest["version"],
        "planned_logical_calls": manifest["planned_logical_calls"],
        "paid_execution_approved": manifest["paid_execution_approved"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
