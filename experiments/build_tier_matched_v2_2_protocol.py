"""Build the CP3 (explicitly not frozen) tier-matched protocol hash manifest."""

from __future__ import annotations

import json
from pathlib import Path

from experiments import run_tier_matched_v2_2 as runner
from experiments.select_tier_matched_models import DISCOVERY, OUT as SELECTION_OUT, PRICING_DIR
from src.bedrock.provenance import hash_file, hash_tree


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results/processed/independent_v2/tier_matched_protocol_manifest.json"


def build_manifest() -> dict:
    selection = json.loads(SELECTION_OUT.read_text())
    plan = json.loads(runner.PLAN_OUT.read_text())
    if plan != runner.build_plan():
        raise ValueError("saved tier-matched plan is stale")
    if plan["budget"]["fits_hard_cap"]:
        raise ValueError("expected the requested design to exceed the hard cap at CP3")
    if any(probe["status"] != "not_run" for probe in plan["access_probes"]):
        raise ValueError("CP3 manifest may not claim an executed access probe")
    return {
        "protocol": "Tier-Matched Independent Benchmark v2.2",
        "version": "tier-matched-v2.2-cp3",
        "status": "superseded_by_price_matched_v2_never_frozen",
        "superseded_by": "docs/PRICE_MATCHED_V2_PLAN.md",
        "date": "2026-11-18",
        "expected_future_tag": "tier-matched-v2.2-frozen-v1",
        "freeze_tag_created": False,
        "paid_calls_made": 0,
        "access_probes_run": 0,
        "budget_decision_required": False,
        "requested_design_worst_case_usd": plan["budget"]["worst_case_usd"],
        "hard_cap_usd": plan["budget"]["hard_cap_usd"],
        "proposed_cut_worst_case_usd": plan["proposed_cut"]["budget"]["worst_case_usd"],
        "planned_models": len(plan["models"]),
        "conditional_selected_models": sum(
            row["status"] == "selected_pending_access_probe" for row in selection["selected_slots"]
        ),
        "empty_slots": [
            {"provider": row["provider"], "band": row["band"]}
            for row in selection["selected_slots"] if row["status"].startswith("empty_")
        ],
        "candidate_rows": len(selection["candidates"]),
        "hashes": {
            "dataset_tree_sha256": hash_tree(runner.DATA),
            "plan_document_sha256": hash_file(REPO / "docs/TIER_MATCHED_PLAN_DRAFT.md"),
            "posthoc_rules_sha256": hash_file(REPO / "docs/POSTHOC_V2_RULES.md"),
            "frozen_v2_scorer_sha256": hash_file(REPO / "src/independent/v2.py"),
            "posthoc_helpers_sha256": hash_file(REPO / "src/independent/v2_posthoc.py"),
            "scorer_v2_2_sha256": hash_file(REPO / "src/independent/v2_2.py"),
            "a1_prompt_sha256": hash_file(runner.PROMPTS["a1"]),
            "a2_prompt_sha256": hash_file(runner.PROMPTS["a2"]),
            "a3_prompt_v2_2_sha256": hash_file(runner.PROMPTS["a3"]),
            "selection_script_sha256": hash_file(REPO / "experiments/select_tier_matched_models.py"),
            "selection_output_sha256": hash_file(SELECTION_OUT),
            "runner_sha256": hash_file(REPO / "experiments/run_tier_matched_v2_2.py"),
            "offline_plan_sha256": hash_file(runner.PLAN_OUT),
            "discovery_sha256": hash_file(DISCOVERY),
            "pricing_snapshot_sha256": {
                path.name: hash_file(path) for path in sorted(PRICING_DIR.glob("*.json"))
            },
        },
    }


def main() -> int:
    manifest = build_manifest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
