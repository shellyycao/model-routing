"""Price-matched-v2 runner: offline plan by default, execution remains locked.

The planned run order is repeat-major with models interleaved.  This module does not
create an AWS client unless a future reviewed version unlocks ``--execute``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.bedrock.client import estimate_input_tokens_upper
from src.bedrock.provenance import hash_file, hash_tree
from src.bedrock.structured import schema_instruction
from src.independent.v2_2 import (
    A1_HARNESS_V22,
    DebugResponseV22,
    ExtractionEnvelope,
    ExtractionResponseV22,
    LiteratureResponseV22,
    a3_candidates_text_v22,
    score_debugging_v22,
    score_extraction_v22,
    score_literature_v22,
)


REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "datasets/independent_v2"
VERIFICATION = REPO / "results/processed/independent_v2/price_matched_model_verification.json"
PILOT = REPO / "configs/price_matched_v2_compatibility_pilot.json"
PLAN_OUT = REPO / "results/processed/independent_v2/price_matched_v2_plan.json"
MANIFEST = REPO / "results/processed/independent_v2/price_matched_v2_protocol_manifest.json"
RAW = REPO / "results/raw/price_matched_v2"
LEDGER = REPO / "results/raw/ledgers/price_matched_v2.json"
CHECKPOINT = RAW / "repeat1_cost_checkpoint.json"
PILOT_RECORDS = REPO / "results/raw/price_matched_v2_pilot/records.jsonl"
PILOT_INVOCATIONS = REPO / "results/raw/price_matched_v2_pilot/invocations.jsonl"
PILOT_SUMMARY = REPO / "results/raw/price_matched_v2_pilot/summary.json"
REPILOT_RECORDS = REPO / "results/raw/price_matched_v2_pilot/repilot_records.jsonl"
REPILOT_INVOCATIONS = REPO / "results/raw/price_matched_v2_pilot/repilot_invocations.jsonl"
REPILOT_SUMMARY = REPO / "results/raw/price_matched_v2_pilot/repilot_summary.json"
MODEL_PROBE = REPO / "results/raw/model_probe_2026-11-18.json"
ACCESS_SNAPSHOT = REPO / "results/raw/model_access_2026-11-18.json"
PRICING_DIR = REPO / "results/raw/pricing"
PROMPTS = {
    "a1": REPO / "prompts/independent_v2/a1_debugging.txt",
    "a2": REPO / "prompts/independent_v2/a2_extraction.txt",
    "a3": REPO / "prompts/independent_v2_2/a3_literature.txt",
}
SCHEMAS = {"a1": DebugResponseV22, "a2": ExtractionResponseV22, "a3": LiteratureResponseV22}
MAX_TOKENS = 16_384
REPEATS = 3
RETRY_MAX_ATTEMPTS = 5
HARD_CAP_USD = 100.0
INITIAL_PILOT_LOGICAL_CALLS = 9
REPILOT_LOGICAL_CALLS = 6
REALISTIC_OUTPUT_TOKENS = {"a1": 3_500, "a2": 1_000, "a3": 2_000}
FUTURE_TAG = "price-matched-v2-frozen-v1.1"
EXPERIMENT_IDS = {
    "a1": "price_matched_v2_a1",
    "a2": "price_matched_v2_a2",
    "a3": "price_matched_v2_a3",
}


def models() -> list[dict[str, Any]]:
    verified = json.loads(VERIFICATION.read_text())
    return [
        {
            "alias": row["alias"],
            "provider": row["provider"],
            "base_model_id": row["base_model_id"],
            "callable_model_id": row["callable_model_id"],
            "input_per_mtok": row["input_per_mtok"],
            "output_per_mtok": row["output_per_mtok"],
            "temperature": None if row["alias"] == "kimi_k3" else 0.0,
            "temperature_support": {
                "sonnet_4_6": "temperature_0_verified_in_compatibility_pilot",
                "kimi_k3": "temperature_omission_verified_in_repilot_3_of_3",
                "glm_5": "temperature_0_verified_in_repilot_3_of_3",
            }[row["alias"]],
            "reasoning_setting": "vendor_default_no_control_field",
        }
        for row in verified["models"]
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


def full_prompt(task: str, case: dict[str, Any]) -> str:
    return f"{render(task, case)}\n\n{schema_instruction(SCHEMAS[task])}"


def plan_rows() -> list[dict[str, Any]]:
    """Exact repeat-major order; adjacent rows interleave models for one case."""
    rows = []
    for repeat in range(REPEATS):
        for task in ("a1", "a2", "a3"):
            for case in load_cases(task):
                for model in models():
                    identity = {
                        "protocol": "price-matched-v2",
                        "repeat": repeat,
                        "task": task,
                        "case_id": case["case_id"],
                        "model": model["alias"],
                    }
                    rows.append({
                        **identity,
                        "run_id": hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest(),
                        "callable_model_id": model["callable_model_id"],
                    })
    return rows


def initial_pilot_calls() -> list[dict[str, Any]]:
    """Historical approved nine-call plan; kept exact after the model swap."""
    config = json.loads(PILOT.read_text())
    initial_models = (
        ("sonnet_4_6", "us.anthropic.claude-sonnet-4-6"),
        ("kimi_k3", "us.moonshotai.kimi-k3"),
        ("grok_4_7", "us.xai.grok-4.7"),
    )
    calls = []
    for task in ("a1", "a2", "a3"):
        case = config["cases"][task]
        for alias, model_id in initial_models:
            calls.append({
                "task": task,
                "synthetic_case_id": case["case_id"],
                "model_alias": alias,
                "callable_model_id": model_id,
                "maxTokens": MAX_TOKENS,
                "temperature": 0.0,
                "reasoning": "vendor default; no reasoning-control field",
                "checks": config["checks"],
                "quality_review_forbidden": True,
                "status": "completed_or_skipped_as_recorded",
            })
    return calls


def pilot_calls() -> list[dict[str, Any]]:
    """Backward-compatible name for the immutable historical pilot plan."""
    return initial_pilot_calls()


def repilot_calls() -> list[dict[str, Any]]:
    """Exact six user-approved calls after the GLM swap and Kimi deviation."""
    config = json.loads(PILOT.read_text())
    selected = {row["alias"]: row for row in models()}
    calls = []
    for task in ("a1", "a2", "a3"):
        case = config["cases"][task]
        for alias in ("kimi_k3", "glm_5"):
            model = selected[alias]
            calls.append({
                "task": task,
                "synthetic_case_id": case["case_id"],
                "model_alias": alias,
                "callable_model_id": model["callable_model_id"],
                "maxTokens": MAX_TOKENS,
                "temperature": model["temperature"],
                "temperature_field": "omitted" if model["temperature"] is None else "sent",
                "reasoning": "vendor default; no reasoning-control field",
                "checks": config["checks"],
                "quality_review_forbidden": True,
                "status": "completed_success_as_recorded",
            })
    return calls


def _input_totals(cases: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, int], dict[str, int]]:
    static, realistic = {}, {}
    for task, task_cases in cases.items():
        prompts = [full_prompt(task, case) for case in task_cases]
        static[task] = sum(
            estimate_input_tokens_upper([{"role": "user", "content": [{"text": prompt}]}], None)
            for prompt in prompts
        )
        realistic[task] = sum(math.ceil(len(prompt.encode("utf-8")) / 4) + 256 for prompt in prompts)
    return static, realistic


def _budget() -> dict[str, Any]:
    evaluation_cases = {task: load_cases(task) for task in ("a1", "a2", "a3")}
    eval_static, eval_realistic = _input_totals(evaluation_cases)
    ledger = json.loads(LEDGER.read_text()) if LEDGER.exists() else {}
    sunk_pilot_cost = float(ledger.get("spent_usd_priced", 0.0))
    sunk_pilot_attempts = int(ledger.get("calls", 0))
    static_rows, realistic_rows = [], []
    for model in models():
        static_input = sum(eval_static.values()) * REPEATS * RETRY_MAX_ATTEMPTS
        static_output = 90 * REPEATS * RETRY_MAX_ATTEMPTS * MAX_TOKENS
        static_cost = (
            static_input * model["input_per_mtok"]
            + static_output * model["output_per_mtok"]
        ) / 1_000_000
        realistic_input = sum(eval_realistic.values()) * REPEATS
        realistic_output = sum(
            REALISTIC_OUTPUT_TOKENS[task] * (30 * REPEATS)
            for task in ("a1", "a2", "a3")
        )
        realistic_cost = (
            realistic_input * model["input_per_mtok"]
            + realistic_output * model["output_per_mtok"]
        ) / 1_000_000
        static_rows.append({
            "model_alias": model["alias"],
            "input_token_reservation": static_input,
            "output_token_reservation": static_output,
            "includes_repilot_calls": 0,
            "worst_case_usd": static_cost,
        })
        realistic_rows.append({
            "model_alias": model["alias"],
            "assumed_input_tokens": realistic_input,
            "assumed_output_tokens_including_reasoning": realistic_output,
            "includes_repilot_calls": 0,
            "estimated_usd": realistic_cost,
        })
    return {
        "hard_cap_usd": HARD_CAP_USD,
        "static_worst_case": {
            "assumptions": "completed pilot and re-pilot ledger actual plus 810 evaluation calls; five attempts per future logical call; conservative byte-count input bound and 16384 output tokens on every future attempt",
            "evaluation_logical_calls": 810,
            "completed_initial_pilot_logical_slots": INITIAL_PILOT_LOGICAL_CALLS,
            "completed_repilot_logical_calls": REPILOT_LOGICAL_CALLS,
            "sunk_pilot_api_attempts": sunk_pilot_attempts,
            "maximum_future_api_attempts": 810 * RETRY_MAX_ATTEMPTS,
            "maximum_api_attempts": sunk_pilot_attempts + 810 * RETRY_MAX_ATTEMPTS,
            "sunk_pilot_actual_priced_usd": sunk_pilot_cost,
            "models": static_rows,
            "total_usd": sunk_pilot_cost + sum(row["worst_case_usd"] for row in static_rows),
        },
        "realistic_estimate": {
            "assumptions": {
                "retries": 0,
                "input_tokens": "UTF-8 bytes / 4 rounded up + 256 tokens per rendered prompt including schema",
                "billed_output_tokens_including_reasoning_per_call": REALISTIC_OUTPUT_TOKENS,
                "includes_completed_pilot_and_repilot_actual": True,
            },
            "sunk_pilot_actual_priced_usd": sunk_pilot_cost,
            "models": realistic_rows,
            "total_usd": sunk_pilot_cost + sum(row["estimated_usd"] for row in realistic_rows),
        },
        "runtime_enforcement": {
            "reserve_then_settle": True,
            "single_shared_cap_for_pilot_and_main": True,
            "cost_checkpoint_after_repeat": 1,
            "checkpoint_rule": "stop after repeat 1; resume only after ledger audit and projected total = pilot actual + 3 * repeat-1 evaluation actual is <= $100",
        },
    }


def build_plan() -> dict[str, Any]:
    rows = plan_rows()
    pilot = initial_pilot_calls()
    repilot = repilot_calls()
    pilot_summary = json.loads(PILOT_SUMMARY.read_text())
    repilot_summary = json.loads(REPILOT_SUMMARY.read_text())
    return {
        "protocol": "price-matched-v2",
        "status": "protocol_frozen_paid_execution_approved",
        "user_approval": {"wording": "Approve main run", "date": "2026-11-18"},
        "models": models(),
        "generation": {
            "maxTokens": MAX_TOKENS,
            "temperature": "0 for Sonnet 4.6 and GLM 5; omitted for Kimi K3 after the pilot ValidationException and final user approval",
            "reasoning": "vendor default; no reasoning-control field",
        },
        "evaluation": {
            "logical_calls": len(rows),
            "repeats": REPEATS,
            "ordering": "repeat-major, then task, case, model; models interleaved within every case",
            "calls_per_repeat": len(rows) // REPEATS,
            "repeat_boundaries": [
                {"repeat": repeat + 1, "start_index": repeat * 270, "end_index_exclusive": (repeat + 1) * 270}
                for repeat in range(REPEATS)
            ],
            "cost_checkpoint_after_repeat_1": True,
            "first_rows": rows[:9],
            "last_rows": rows[-9:],
        },
        "compatibility_pilot": {
            "authorized": True,
            "executed": True,
            "logical_calls": len(pilot),
            "executor": "experiments/run_price_matched_v2_pilot.py",
            "pilot_hard_cap_usd": 15.0,
            "shared_overall_ledger": str(LEDGER.relative_to(REPO)),
            "pilot_spend_counts_toward_overall_100_usd": True,
            "outcome_summary": pilot_summary,
            "calls": pilot,
        },
        "compatibility_repilot": {
            "authorized": True,
            "executed": True,
            "logical_calls": len(repilot),
            "executor": "experiments/run_price_matched_v2_pilot.py",
            "required_flag": "--execute-approved-repilot",
            "pilot_hard_cap_usd": 15.0,
            "shared_overall_ledger": str(LEDGER.relative_to(REPO)),
            "outcome_summary": repilot_summary,
            "ledger_spent_usd_after_repilot": _ledger_spent(),
            "calls": repilot,
        },
        "selection_disclosure": {
            "removed_model": "grok_4_7",
            "removed_reason": "real compatibility-pilot invokes returned AccessDeniedException despite AVAILABLE control-plane metadata",
            "replacement_model": "glm_5",
            "decision_priority": "generation match over price match",
            "previous_blended_price_ratio": 2.0,
            "new_blended_price_ratio": max(row["input_per_mtok"] * 0.75 + row["output_per_mtok"] * 0.25 for row in models()) / min(row["input_per_mtok"] * 0.75 + row["output_per_mtok"] * 0.25 for row in models()),
        },
        "budget": _budget(),
        "analysis": {
            "script": "experiments/analyze_price_matched_v2.py",
            "metrics": [
                "actual cost per task from recorded input/output tokens",
                "A1 cost per functional_correct and A2 cost per content_correct",
                "A3 cost per valid response and cost per strict-nDCG point",
                "per-task quality-cost Pareto frontier using strict A3 nDCG",
                "token usage, latency, truncation and format-failure rates",
            ],
        },
        "hash_inputs": {
            "dataset_tree_sha256": hash_tree(DATA),
            "a1_prompt_sha256": hash_file(PROMPTS["a1"]),
            "a2_prompt_sha256": hash_file(PROMPTS["a2"]),
            "a3_prompt_sha256": hash_file(PROMPTS["a3"]),
            "scorer_v2_2_sha256": hash_file(REPO / "src/independent/v2_2.py"),
            "a3_scoring_decisions_sha256": hash_file(
                REPO / "docs/reviews/2026-11-18_a3_scoring_decisions.md"
            ),
            "model_verification_sha256": hash_file(VERIFICATION),
            "pilot_config_sha256": hash_file(PILOT),
            "pilot_executor_sha256": hash_file(
                REPO / "experiments/run_price_matched_v2_pilot.py"
            ),
            "initial_pilot_records_sha256": hash_file(PILOT_RECORDS),
            "initial_pilot_summary_sha256": hash_file(PILOT_SUMMARY),
            "repilot_records_sha256": hash_file(REPILOT_RECORDS),
            "repilot_invocations_sha256": hash_file(REPILOT_INVOCATIONS),
            "repilot_summary_sha256": hash_file(REPILOT_SUMMARY),
            "model_probe_sha256": hash_file(MODEL_PROBE),
        },
        "execution_gate": {
            "required_tag": FUTURE_TAG,
            "repilot_completed": True,
            "protocol_manifest_must_be_frozen": True,
            "user_paid_execution_approval": "Approve main run",
            "hard_cap_usd": HARD_CAP_USD,
        },
    }


def _current_tags() -> set[str]:
    result = subprocess.run(
        ["git", "tag", "--points-at", "HEAD"], cwd=REPO, check=True, capture_output=True, text=True
    )
    return set(result.stdout.split())


def protocol_hashes() -> dict[str, Any]:
    """Complete immutable protocol/evidence hash set used by build and execution."""
    files = {
        "plan_document_sha256": REPO / "docs/PRICE_MATCHED_V2_PLAN.md",
        "superseded_plan_sha256": REPO / "docs/TIER_MATCHED_PLAN_DRAFT.md",
        "posthoc_rules_sha256": REPO / "docs/POSTHOC_V2_RULES.md",
        "a3_scoring_decisions_sha256": REPO / "docs/reviews/2026-11-18_a3_scoring_decisions.md",
        "frozen_v2_scorer_sha256": REPO / "src/independent/v2.py",
        "posthoc_helpers_sha256": REPO / "src/independent/v2_posthoc.py",
        "scorer_v2_2_sha256": REPO / "src/independent/v2_2.py",
        "independent_records_sha256": REPO / "src/independent/records.py",
        "a1_prompt_sha256": PROMPTS["a1"],
        "a2_prompt_sha256": PROMPTS["a2"],
        "a3_prompt_v2_2_sha256": PROMPTS["a3"],
        "pilot_config_sha256": PILOT,
        "pilot_executor_sha256": REPO / "experiments/run_price_matched_v2_pilot.py",
        "model_verifier_sha256": REPO / "experiments/verify_price_matched_models.py",
        "model_verification_sha256": VERIFICATION,
        "runner_sha256": Path(__file__),
        "offline_plan_sha256": PLAN_OUT,
        "analysis_sha256": REPO / "experiments/analyze_price_matched_v2.py",
        "manifest_builder_sha256": REPO / "experiments/build_price_matched_v2_protocol.py",
        "bedrock_client_sha256": REPO / "src/bedrock/client.py",
        "bedrock_models_sha256": REPO / "src/bedrock/models.py",
        "bedrock_usage_sha256": REPO / "src/bedrock/usage.py",
        "bedrock_structured_sha256": REPO / "src/bedrock/structured.py",
        "workflow_executor_sha256": REPO / "src/workflow/executor.py",
        "workflow_stages_sha256": REPO / "src/workflow/stages.py",
        "access_snapshot_sha256": ACCESS_SNAPSHOT,
        "model_probe_sha256": MODEL_PROBE,
        "initial_pilot_records_sha256": PILOT_RECORDS,
        "initial_pilot_invocations_sha256": PILOT_INVOCATIONS,
        "initial_pilot_summary_sha256": PILOT_SUMMARY,
        "repilot_records_sha256": REPILOT_RECORDS,
        "repilot_invocations_sha256": REPILOT_INVOCATIONS,
        "repilot_summary_sha256": REPILOT_SUMMARY,
    }
    return {
        "dataset_tree_sha256": hash_tree(DATA),
        **{name: hash_file(path) for name, path in files.items()},
        "pricing_snapshot_sha256": {
            path.name: hash_file(path) for path in sorted(PRICING_DIR.glob("*.json"))
        },
    }


def verify_frozen_protocol() -> dict[str, Any]:
    """Refuse before any AWS client exists unless the future freeze is exact."""
    if FUTURE_TAG not in _current_tags():
        raise SystemExit(f"paid execution requires HEAD to have exact tag {FUTURE_TAG}")
    if not MANIFEST.exists():
        raise SystemExit("price-matched freeze manifest is missing")
    manifest = json.loads(MANIFEST.read_text())
    if manifest.get("status") != "protocol_frozen_paid_execution_approved":
        raise SystemExit("price-matched protocol is not frozen and paid-approved")
    expected = protocol_hashes()
    if manifest.get("hashes") != expected:
        frozen = manifest.get("hashes", {})
        keys = set(frozen) | set(expected)
        differences = {
            key: {"frozen": frozen.get(key), "current": expected.get(key)}
            for key in sorted(keys) if frozen.get(key) != expected.get(key)
        }
        raise SystemExit(f"frozen protocol hash mismatch: {json.dumps(differences, sort_keys=True)}")
    if manifest.get("hard_cap_usd") != HARD_CAP_USD:
        raise SystemExit("frozen hard cap mismatch")
    if manifest.get("user_approval", {}).get("wording") != "Approve main run":
        raise SystemExit("paid execution approval wording is missing")
    if manifest.get("evaluation_logical_calls") != 810:
        raise SystemExit("frozen evaluation call count mismatch")
    return manifest


def _registry():
    from src.bedrock.models import InferenceSettings, ModelRegistry, ModelSpec, Pricing

    names = {"sonnet_4_6": "Claude Sonnet 4.6", "kimi_k3": "Kimi K3", "glm_5": "GLM 5"}
    specs = {}
    source = "official saved AWS Price List snapshots verified by experiments.verify_price_matched_models"
    for row in models():
        specs[row["alias"]] = ModelSpec(
            alias=row["alias"],
            name=names[row["alias"]],
            family=row["provider"],
            model_id=row["callable_model_id"],
            base_model_id=row["base_model_id"],
            pricing=Pricing(
                input_per_mtok=row["input_per_mtok"],
                output_per_mtok=row["output_per_mtok"],
                source=source,
                retrieved="2026-11-18",
            ),
            inference=InferenceSettings(max_tokens=MAX_TOKENS, temperature=row["temperature"]),
        )
    return ModelRegistry(region="us-east-1", aws_profile="xai-bedrock", models=specs)


def reasoning_tokens_from_usage(usage: dict[str, Any]) -> int | None:
    """Extract a provider-reported reasoning-token subset without inventing one."""
    for key in ("reasoningTokens", "reasoning_tokens"):
        value = usage.get(key)
        if isinstance(value, int):
            return value
    for key in ("outputTokenDetails", "outputTokensDetails", "output_token_details"):
        details = usage.get(key)
        if isinstance(details, dict):
            for reasoning_key in ("reasoningTokens", "reasoning_tokens"):
                value = details.get(reasoning_key)
                if isinstance(value, int):
                    return value
    return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append(task: str, record: dict[str, Any]) -> None:
    from src.independent.records import IndependentTaskRecord

    path = RAW / f"{EXPERIMENT_IDS[task]}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(IndependentTaskRecord(**record).model_dump_json() + "\n")


def _completed() -> set[str]:
    return {
        json.loads(line)["run_id"]
        for path in (RAW / f"{EXPERIMENT_IDS[task]}.jsonl" for task in ("a1", "a2", "a3"))
        if path.exists()
        for line in path.read_text().splitlines()
        if line.strip()
    }


def _ledger_spent() -> float:
    if not LEDGER.exists():
        return 0.0
    return float(json.loads(LEDGER.read_text()).get("spent_usd_priced", 0.0))


def execute(*, repeats: tuple[int, ...]) -> dict[str, Any]:
    """Future paid path. ``verify_frozen_protocol`` must run before this function."""
    from src.bedrock.client import BedrockClient
    from src.bedrock.usage import InvocationContext, UsageLimits
    from src.workflow.executor import DockerExecutor
    from src.workflow.stages import SandboxGate

    registry = _registry()
    ledger_state = json.loads(LEDGER.read_text()) if LEDGER.exists() else {}
    budget_models = build_plan()["budget"]["static_worst_case"]["models"]
    limits = UsageLimits(
        max_calls=(810 + INITIAL_PILOT_LOGICAL_CALLS + REPILOT_LOGICAL_CALLS) * RETRY_MAX_ATTEMPTS,
        max_input_tokens=int(ledger_state.get("input_tokens", 0)) + sum(
            row["input_token_reservation"] for row in budget_models
        ),
        max_output_tokens=int(ledger_state.get("output_tokens", 0)) + sum(
            row["output_token_reservation"] for row in budget_models
        ),
        max_budget_usd=HARD_CAP_USD,
    )
    client = BedrockClient(
        registry=registry,
        limits=limits,
        ledger_path=LEDGER,
        log_path=RAW / "invocations.jsonl",
        cache_dir=None,
    )
    executor = DockerExecutor()
    gate = SandboxGate().check(executor)
    if not gate.ok:
        raise SystemExit(f"sandbox gate refused before evaluation: {gate.reason}")
    case_maps = {
        task: {case["case_id"]: case for case in load_cases(task)} for task in ("a1", "a2", "a3")
    }
    done = _completed()
    summary = {"executed": 0, "skipped_completed": 0, "void_infra": 0}
    dataset_version = (DATA / "a1/VERSION").read_text().strip()

    def one(row: dict[str, Any]) -> None:
        if row["run_id"] in done:
            summary["skipped_completed"] += 1
            return
        task, case, alias = row["task"], case_maps[row["task"]][row["case_id"]], row["model"]
        run_dir = REPO / "results/raw/runs" / row["run_id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        prompt = render(task, case)
        (run_dir / "prompt.txt").write_text(prompt)
        started = _now()
        record: dict[str, Any] = {
            "run_id": row["run_id"],
            "experiment_id": EXPERIMENT_IDS[task],
            "task": task,
            "case_id": case["case_id"],
            "model_alias": alias,
            "model_id": registry.get(alias).model_id,
            "repeat_index": row["repeat"],
            "prompt_version": "independent_v2_2",
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
            "dataset_version": dataset_version,
            "case_hash": hash_file(DATA / task / "cases" / f"{case['case_id']}.json"),
            "config_hash": hashlib.sha256(json.dumps({
                "protocol": "price-matched-v2", "maxTokens": MAX_TOKENS,
                "temperature": registry.get(alias).inference.temperature,
                "temperature_field": (
                    "omitted" if registry.get(alias).inference.temperature is None else "sent"
                ),
                "model": alias, "repeat": row["repeat"],
            }, sort_keys=True).encode()).hexdigest(),
            "started_at": started,
        }
        context = InvocationContext(
            experiment_id=EXPERIMENT_IDS[task], run_id=row["run_id"], stage_id=task,
            prompt_version="independent_v2_2", repeat_index=row["repeat"],
        )
        try:
            structured = client.converse_structured(
                alias, prompt, SCHEMAS[task], context=context, use_cache=False, max_tokens=MAX_TOKENS
            )
        except Exception as error:
            record.update(
                status="void_infra", failure_type="infra", failure_detail=str(error)[:500],
                finished_at=_now(),
            )
            _append(task, record)
            summary["void_infra"] += 1
            return

        invocation = structured.result.record
        raw_usage = structured.result.raw_response.get("usage") or {}
        (run_dir / "response.txt").write_text(structured.result.text or "")
        (run_dir / "usage.json").write_text(json.dumps(raw_usage, indent=2, sort_keys=True) + "\n")
        artifacts = [str((run_dir / name).relative_to(REPO)) for name in ("prompt.txt", "response.txt", "usage.json")]
        if structured.parsed is not None:
            (run_dir / "parsed.json").write_text(structured.parsed.model_dump_json(indent=2))
            artifacts.append(str((run_dir / "parsed.json").relative_to(REPO)))

        harness = None
        if task == "a1" and structured.parsed is not None:
            solution, tests = run_dir / "solution.py", run_dir / "tests.json"
            solution.write_text(structured.parsed.fixed_code)
            tests.write_text(json.dumps(case["hidden"]))
            execution = executor.execute(
                A1_HARNESS_V22, {"solution.py": str(solution), "tests.json": str(tests)}, str(run_dir / "output")
            )
            record["execution"] = {
                "status": execution.status.value,
                "runtime_ms": execution.runtime_ms,
                "sandbox_image": execution.sandbox_image,
                "stderr_tail": (execution.stderr or "")[-400:],
            }
            result_path = run_dir / "output/results.json"
            harness = json.loads(result_path.read_text()) if result_path.exists() else None

        if task == "a1":
            scores = score_debugging_v22(case, structured.parsed, harness)
        elif task == "a2":
            scores = score_extraction_v22(case, ExtractionEnvelope(
                fields=structured.parsed.fields if structured.parsed else None,
                wrapper_present=structured.parsed is not None,
                parse_ok=structured.parsed is not None,
            ))
        else:
            scores = score_literature_v22(case, structured.parsed)
        operational = bool(scores["operational_success"])
        record.update(
            invocation_ids=[invocation.invocation_id],
            parse_ok=structured.parsed is not None,
            truncated=bool(invocation.truncated),
            scores=scores,
            generation_ms=invocation.latency_ms,
            input_tokens=invocation.input_tokens,
            output_tokens=invocation.output_tokens,
            reasoning_tokens=reasoning_tokens_from_usage(raw_usage),
            reasoning_chars=invocation.reasoning_chars,
            cost_usd=invocation.cost_usd,
            cost_status=invocation.cost_status,
            artifacts=artifacts,
            status="passed" if operational else "failed",
            failure_type=None if operational else ("truncated" if invocation.truncated else "validation_failed"),
            failure_detail=None if operational else str(structured.parse_error or "operational requirements not met")[:500],
            finished_at=_now(),
        )
        _append(task, record)
        done.add(row["run_id"])
        summary["executed"] += 1

    with executor.image_lease(gate.image_id):
        for row in plan_rows():
            if row["repeat"] in repeats:
                one(row)
    return summary


def _write_repeat1_checkpoint(baseline_spent: float, summary: dict[str, Any]) -> dict[str, Any]:
    spent = _ledger_spent()
    repeat_cost = max(0.0, spent - baseline_spent)
    projected = baseline_spent + 3 * repeat_cost
    checkpoint = {
        "protocol": "price-matched-v2",
        "status": "repeat1_complete_manual_resume_required",
        "pilot_actual_and_preexisting_usd": baseline_spent,
        "repeat1_evaluation_actual_usd": repeat_cost,
        "projected_total_usd": projected,
        "hard_cap_usd": HARD_CAP_USD,
        "projection_within_cap": projected <= HARD_CAP_USD,
        "summary": summary,
        "created_at": _now(),
    }
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n")
    return checkpoint


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-plan", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--continue-after-repeat-1", action="store_true")
    args = parser.parse_args(argv)
    plan = build_plan()
    if args.write_plan:
        PLAN_OUT.parent.mkdir(parents=True, exist_ok=True)
        PLAN_OUT.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    print(json.dumps(plan, indent=2, sort_keys=True))
    if args.execute:
        verify_frozen_protocol()
        if args.continue_after_repeat_1:
            if not CHECKPOINT.exists():
                raise SystemExit("repeat-1 checkpoint is missing")
            checkpoint = json.loads(CHECKPOINT.read_text())
            if not checkpoint.get("projection_within_cap"):
                raise SystemExit("repeat-1 projected total exceeds $100; continuation refused")
            summary = execute(repeats=(1, 2))
            print(json.dumps({"phase": "repeats_2_and_3", "summary": summary}, indent=2))
        else:
            baseline = _ledger_spent()
            summary = execute(repeats=(0,))
            checkpoint = _write_repeat1_checkpoint(baseline, summary)
            print(json.dumps({"phase": "repeat_1", "checkpoint": checkpoint}, indent=2))
            print("STOPPED AFTER REPEAT 1: audit the checkpoint before an explicit continuation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
