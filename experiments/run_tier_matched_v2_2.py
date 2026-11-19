"""Tier-matched Independent-v2.2 runner (offline plan by default).

Running this module with no arguments performs only local planning.  Paid execution
is intentionally locked at CP3: access probes, manager review, a final budget cut,
the freeze manifest and the freeze tag must all exist first.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.bedrock.client import PROMPT_TOKEN_OVERHEAD, estimate_input_tokens_upper
from src.bedrock.provenance import hash_file, hash_tree
from src.bedrock.structured import schema_instruction
from src.independent.v2_2 import (
    DebugResponseV22,
    ExtractionResponseV22,
    LiteratureResponseV22,
    a3_candidates_text_v22,
)


REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "datasets/independent_v2"
SELECTION = REPO / "results/processed/independent_v2/tier_matched_selection.json"
PLAN_OUT = REPO / "results/processed/independent_v2/tier_matched_plan.json"
MAX_TOKENS = 16_384
REPEATS = 3
RETRY_MAX_ATTEMPTS = 5
HARD_CAP_USD = 100.0
MAX_PROBE_LOGICAL_CALLS_PER_MODEL = 2  # primary plus conditional no-temperature fallback
SCHEMAS = {"a1": DebugResponseV22, "a2": ExtractionResponseV22, "a3": LiteratureResponseV22}
PROMPTS = {
    "a1": REPO / "prompts/independent_v2/a1_debugging.txt",
    "a2": REPO / "prompts/independent_v2/a2_extraction.txt",
    "a3": REPO / "prompts/independent_v2_2/a3_literature.txt",
}
ANCHOR_SPECS = [
    {
        "alias": "anchor_anthropic_sonnet_4_6",
        "role": "anchor",
        "provider": "Anthropic",
        "base_model_id": "anthropic.claude-sonnet-4-6",
        "callable_model_id": "us.anthropic.claude-sonnet-4-6",
        "temperature_support": "verified_in_prior_v2_calls",
    },
    {
        "alias": "anchor_amazon_nova_pro_v1",
        "role": "anchor",
        "provider": "Amazon",
        "base_model_id": "amazon.nova-pro-v1:0",
        "callable_model_id": "us.amazon.nova-pro-v1:0",
        "temperature_support": "verified_in_prior_v2_calls",
    },
    {
        "alias": "anchor_openai_gpt_oss_120b",
        "role": "anchor",
        "provider": "OpenAI",
        "base_model_id": "openai.gpt-oss-120b-1:0",
        "callable_model_id": "openai.gpt-oss-120b-1:0",
        "temperature_support": "verified_in_prior_v2_calls",
    },
]


def load_cases(task: str) -> list[dict[str, Any]]:
    return [json.loads(path.read_text()) for path in sorted((DATA / task / "cases").glob("*.json"))]


def render(task: str, case: dict[str, Any]) -> str:
    template = PROMPTS[task].read_text()
    if task == "a1":
        values = {
            "spec": case["spec"],
            "buggy_code": case["buggy"],
            "visible_tests": "\n".join(f"assert {test}" for test in case["visible"]),
        }
    elif task == "a2":
        values = {
            "schema": "\n".join(f"- {key}: {description}" for key, description in case["schema"].items()),
            "document": case["document"],
        }
    else:
        values = {"query": case["query"]["text"], "candidates": a3_candidates_text_v22(case)}
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    if "{{" in template:
        raise ValueError(f"unrendered placeholder in {task}")
    return template


def _models_from_selection() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selection = json.loads(SELECTION.read_text())
    by_id = {row["base_model_id"]: row for row in selection["candidates"] if row["base_model_id"]}
    out = []
    for slot in selection["selected_slots"]:
        if slot["status"] != "selected_pending_access_probe":
            continue
        row = by_id[slot["base_model_id"]]
        out.append({
            "alias": f"tier_{slot['provider'].casefold()}_{slot['band']}",
            "role": f"selected_{slot['band']}",
            "provider": slot["provider"],
            "base_model_id": slot["base_model_id"],
            "callable_model_id": slot["callable_model_id"],
            "input_per_mtok": row["input_per_mtok"],
            "output_per_mtok": row["output_per_mtok"],
            "temperature_support": "pending_access_probe",
        })
    anchors = []
    for spec in ANCHOR_SPECS:
        row = by_id[spec["base_model_id"]]
        if row["input_per_mtok"] is None or row["output_per_mtok"] is None:
            raise ValueError(f"anchor price is missing from official snapshots: {spec['base_model_id']}")
        anchors.append({
            **spec,
            "input_per_mtok": row["input_per_mtok"],
            "output_per_mtok": row["output_per_mtok"],
        })
    return out, anchors


def protocol_models() -> list[dict[str, Any]]:
    selected, anchors = _models_from_selection()
    models = selected + anchors
    if len({row["callable_model_id"] for row in models}) != len(models):
        raise ValueError("selected and anchor model IDs must be unique")
    return models


def _input_upper_by_task() -> dict[str, int]:
    totals = {}
    for task in ("a1", "a2", "a3"):
        total = 0
        for case in load_cases(task):
            full_prompt = f"{render(task, case)}\n\n{schema_instruction(SCHEMAS[task])}"
            messages = [{"role": "user", "content": [{"text": full_prompt}]}]
            total += estimate_input_tokens_upper(messages, None)
        totals[task] = total
    return totals


def _budget(models: list[dict[str, Any]], input_per_sweep: int) -> dict[str, Any]:
    evaluation_calls_per_model = 90 * REPEATS
    probe_calls_per_model = MAX_PROBE_LOGICAL_CALLS_PER_MODEL
    evaluation_attempts_per_model = evaluation_calls_per_model * RETRY_MAX_ATTEMPTS
    probe_attempts_per_model = probe_calls_per_model * RETRY_MAX_ATTEMPTS
    attempts_per_model = evaluation_attempts_per_model + probe_attempts_per_model
    probe_messages = [{"role": "user", "content": [{"text": "Reply with exactly: OK"}]}]
    probe_input_upper = estimate_input_tokens_upper(probe_messages, None)
    rows = []
    for model in models:
        input_tokens = (
            input_per_sweep * REPEATS * RETRY_MAX_ATTEMPTS
            + probe_input_upper * probe_attempts_per_model
        )
        output_tokens = MAX_TOKENS * attempts_per_model
        input_cost = input_tokens * model["input_per_mtok"] / 1_000_000
        output_cost = output_tokens * model["output_per_mtok"] / 1_000_000
        rows.append({
            "alias": model["alias"],
            "input_token_reservation": input_tokens,
            "output_token_reservation": output_tokens,
            "worst_input_usd": input_cost,
            "worst_output_usd": output_cost,
            "worst_total_usd": input_cost + output_cost,
        })
    total = sum(row["worst_total_usd"] for row in rows)
    return {
        "method": "every evaluation and probe call uses the conservative prompt-byte upper bound and every one of five attempts reserves maxTokens=16384",
        "evaluation_logical_calls": len(models) * evaluation_calls_per_model,
        "probe_logical_call_reservations": len(models) * probe_calls_per_model,
        "logical_calls_including_probe_reservations": len(models) * (
            evaluation_calls_per_model + probe_calls_per_model
        ),
        "maximum_api_attempts": len(models) * attempts_per_model,
        "models": rows,
        "worst_case_usd": total,
        "hard_cap_usd": HARD_CAP_USD,
        "fits_hard_cap": total <= HARD_CAP_USD,
    }


def build_plan() -> dict[str, Any]:
    models = protocol_models()
    input_by_task = _input_upper_by_task()
    input_per_sweep = sum(input_by_task.values())
    budget = _budget(models, input_per_sweep)
    low_only = [model for model in models if model["role"] == "selected_low"]
    low_budget = _budget(low_only, input_per_sweep)
    probes = []
    for model in models:
        probes.append({
            "callable_model_id": model["callable_model_id"],
            "primary_call": {
                "prompt": "Reply with exactly: OK",
                "maxTokens": MAX_TOKENS,
                "temperature": 0.0,
                "reasoning": "vendor default; send no reasoning-control field",
            },
            "conditional_fallback": "Only after a temperature-parameter ValidationException, repeat once with temperature omitted.",
            "status": "not_run",
        })
    return {
        "protocol": "tier-matched-v2.2",
        "status": "cp3_plan_not_frozen_no_calls_authorized",
        "generation": {
            "maxTokens": MAX_TOKENS,
            "temperature": 0.0,
            "reasoning": "vendor default; no reasoning-control field",
            "parameter_policy": "send temperature=0 only where supported; otherwise omit and record the deviation",
        },
        "case_counts": {task: len(load_cases(task)) for task in ("a1", "a2", "a3")},
        "repeats": REPEATS,
        "models": models,
        "input_token_upper_bound_per_90_case_sweep": input_per_sweep,
        "input_token_upper_bound_by_task": input_by_task,
        "budget": budget,
        "proposed_cut": {
            "proposal": "run only the three selected low-tier models; defer both high-tier models and all three anchors",
            "scientific_effect": "preserves low-tier cross-vendor RQ1; defers RQ2, RQ3 and protocol-effect separation",
            "budget": low_budget,
            "requires_user_and_manager_approval": True,
        },
        "access_probes": probes,
        "hash_inputs": {
            "dataset_tree_sha256": hash_tree(DATA),
            "a1_prompt_sha256": hash_file(PROMPTS["a1"]),
            "a2_prompt_sha256": hash_file(PROMPTS["a2"]),
            "a3_prompt_sha256": hash_file(PROMPTS["a3"]),
            "scorer_v2_2_sha256": hash_file(REPO / "src/independent/v2_2.py"),
            "posthoc_rules_sha256": hash_file(REPO / "docs/POSTHOC_V2_RULES.md"),
            "selection_sha256": hash_file(SELECTION),
        },
        "notes": {
            "prompt_token_overhead": PROMPT_TOKEN_OVERHEAD,
            "a1_a2_prompts_unchanged": True,
            "a3_grounding_comparability": "not comparable with v2 because prompt and schema now enumerate attributes",
            "a3_ranking_comparability": "comparable subject to anchor reruns and the v2.2 deduplicated scorer",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-plan", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    plan = build_plan()
    if args.write_plan:
        PLAN_OUT.parent.mkdir(parents=True, exist_ok=True)
        PLAN_OUT.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    print(json.dumps(plan, indent=2, sort_keys=True))
    if args.execute:
        raise SystemExit(
            "PAID EXECUTION LOCKED AT CP3: complete access probes, approve a <=$100 cut, "
            "freeze the manifest and create the reviewed tag first"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
