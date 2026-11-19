"""Prospective Independent-v2 runner. Planning is offline; --execute makes paid calls.

Plan only (safe default):
  .venv/bin/python -m experiments.run_independent_v2_benchmark --plan

Paid execution is permitted only from the exact ``independent-v2-frozen-v1.1`` tag and
requires explicit call/token/dollar guards. The primary protocol always runs all three tasks,
all three registered study models, and repeat index zero.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from src.bedrock.models import load_registry
from src.bedrock.provenance import config_hash, hash_file, hash_json, hash_tree, make_run_id, models_fingerprint
from src.independent.records import IndependentTaskRecord
from src.independent.v2 import (
    A1_HARNESS_V2,
    DebugResponseV2,
    ExtractionEnvelope,
    ExtractionResponseV2,
    LiteratureResponseV2,
    a3_candidates_text_v2,
    score_debugging_v2,
    score_extraction_v2,
    score_literature_v2,
)


REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "datasets/independent_v2"
PROMPTS = REPO / "prompts/independent_v2"
RAW = REPO / "results/raw/independent_v2"
FREEZE_MANIFEST = REPO / "results/processed/independent/independent_v2_freeze_manifest.json"
FROZEN_TAG = "independent-v2-frozen-v1.1"
PROMPT_VERSION = "independent_v2"
EXPERIMENT_IDS = {"a1": "indepA1_debug_v2", "a2": "indepA2_extract_v2", "a3": "indepA3_lit_v2"}
SCHEMAS = {"a1": DebugResponseV2, "a2": ExtractionResponseV2, "a3": LiteratureResponseV2}
TEMPLATES = {"a1": "a1_debugging.txt", "a2": "a2_extraction.txt", "a3": "a3_literature.txt"}
MAX_TOKENS = {"a1": 4096, "a2": 4096, "a3": 8192}
STUDY_MODELS = ["A", "B", "C"]
MAX_LOGICAL_CALLS = 270
MAX_API_ATTEMPTS = 1350
MAX_INPUT_TOKENS = 500_000
MAX_OUTPUT_TOKENS = 1_474_560
MAX_BUDGET_USD = 100.0


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_cases(task: str) -> list[dict]:
    return [json.loads(path.read_text()) for path in sorted((DATA / task / "cases").glob("*.json"))]


def render(task: str, case: dict) -> str:
    template = (PROMPTS / TEMPLATES[task]).read_text()
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
        values = {"query": case["query"]["text"], "candidates": a3_candidates_text_v2(case)}
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    if "{{" in template:
        raise ValueError(f"unrendered placeholder in {task}")
    return template


def _protocol_extra(task: str, case: dict, alias: str, repeat: int) -> dict:
    return {
        "case": case["case_id"],
        "model": alias,
        "repeat": repeat,
        "max_tokens": MAX_TOKENS[task],
        "prompt_tree": hash_tree(PROMPTS),
        "scorer": hash_file(REPO / "src/independent/v2.py"),
    }


def run_id(registry, task: str, case: dict, alias: str, repeat: int) -> str:
    return make_run_id(
        EXPERIMENT_IDS[task], registry, PROMPT_VERSION, hash_tree(DATA / task),
        extra=_protocol_extra(task, case, alias, repeat),
    )


def completed(task: str) -> set[str]:
    path = RAW / f"{EXPERIMENT_IDS[task]}.jsonl"
    return {json.loads(line)["run_id"] for line in path.read_text().splitlines() if line.strip()} if path.exists() else set()


def plan(tasks: list[str] | None = None, models: list[str] | None = None, repeat: int = 0) -> dict:
    tasks = tasks or ["a1", "a2", "a3"]
    models = models or STUDY_MODELS
    registry = load_registry()
    rows = []
    estimated_input = 0
    worst_output = 0
    for task in tasks:
        done = completed(task)
        for case in load_cases(task):
            estimated_prompt_tokens = (len(render(task, case)) + 3) // 4 + 512
            for alias in models:
                identifier = run_id(registry, task, case, alias, repeat)
                if identifier in done:
                    continue
                rows.append((task, case["case_id"], alias, identifier))
                estimated_input += estimated_prompt_tokens
                worst_output += MAX_TOKENS[task]
    return {
        "planned_logical_calls": len(rows),
        "by_task": {task: sum(row[0] == task for row in rows) for task in tasks},
        "estimated_input_tokens": estimated_input,
        "worst_case_output_tokens": worst_output,
        "maximum_api_attempts_with_five_attempt_retry_policy": len(rows) * 5,
        "runs": rows,
    }


def _current_tags() -> set[str]:
    result = subprocess.run(
        ["git", "tag", "--points-at", "HEAD"], cwd=REPO, check=True, capture_output=True, text=True
    )
    return set(result.stdout.split())


def _expected_freeze_values() -> dict:
    registry = load_registry()
    return {
        "dataset_tree_sha256": hash_tree(DATA),
        "prompt_tree_sha256": hash_tree(PROMPTS),
        "response_schema_and_scorer_sha256": hash_file(REPO / "src/independent/v2.py"),
        "runner_sha256": hash_file(Path(__file__)),
        "usage_guard_sha256": hash_file(REPO / "src/bedrock/usage.py"),
        "model_behavior_sha256": hash_json(models_fingerprint(registry)),
        "max_tokens": MAX_TOKENS,
        "experiment_ids": EXPERIMENT_IDS,
        "hard_guards": {
            "logical_calls": MAX_LOGICAL_CALLS,
            "api_attempts": MAX_API_ATTEMPTS,
            "input_tokens": MAX_INPUT_TOKENS,
            "output_tokens": MAX_OUTPUT_TOKENS,
            "budget_usd": MAX_BUDGET_USD,
        },
    }


def verify_frozen_protocol() -> dict:
    if FROZEN_TAG not in _current_tags():
        raise SystemExit(f"paid execution requires HEAD to have exact tag {FROZEN_TAG}")
    if not FREEZE_MANIFEST.exists():
        raise SystemExit("freeze manifest is missing")
    frozen = json.loads(FREEZE_MANIFEST.read_text())
    expected = _expected_freeze_values()
    differences = {key: {"frozen": frozen.get(key), "current": value} for key, value in expected.items() if frozen.get(key) != value}
    if differences:
        raise SystemExit(f"frozen protocol hash mismatch: {json.dumps(differences, sort_keys=True)}")
    return frozen


def _append(task: str, record: dict) -> None:
    line = IndependentTaskRecord(**record).model_dump_json()
    path = RAW / f"{EXPERIMENT_IDS[task]}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(line + "\n")


def execute(limits, ledger: Path) -> dict:
    from src.bedrock.client import BedrockClient
    from src.bedrock.usage import InvocationContext
    from src.workflow.executor import DockerExecutor
    from src.workflow.stages import SandboxGate

    verify_frozen_protocol()
    client = BedrockClient(limits=limits, ledger_path=ledger)
    registry = client.registry
    executor = DockerExecutor()
    gate = SandboxGate().check(executor)
    if not gate.ok:
        raise SystemExit(f"sandbox gate refused before any model call: {gate.reason}")
    summary = {"executed": 0, "skipped_completed": 0, "void_infra": 0, "consecutive_infra": 0}
    dataset_version = (DATA / "a1/VERSION").read_text().strip()

    def one(task: str, case: dict, alias: str) -> None:
        identifier = run_id(registry, task, case, alias, 0)
        if identifier in completed(task):
            summary["skipped_completed"] += 1
            return
        run_dir = REPO / "results/raw/runs" / identifier
        run_dir.mkdir(parents=True, exist_ok=True)
        prompt = render(task, case)
        (run_dir / "prompt.txt").write_text(prompt)
        spec = registry.get(alias)
        record = {
            "run_id": identifier,
            "experiment_id": EXPERIMENT_IDS[task],
            "task": task,
            "case_id": case["case_id"],
            "model_alias": alias,
            "model_id": spec.model_id,
            "repeat_index": 0,
            "prompt_version": PROMPT_VERSION,
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
            "dataset_version": dataset_version,
            "case_hash": hash_file(DATA / task / "cases" / f"{case['case_id']}.json"),
            "config_hash": config_hash(
                registry, PROMPT_VERSION, hash_tree(DATA / task), extra=_protocol_extra(task, case, alias, 0)
            ),
            "started_at": now(),
        }
        context = InvocationContext(
            experiment_id=EXPERIMENT_IDS[task], run_id=identifier, stage_id=task,
            prompt_version=PROMPT_VERSION, repeat_index=0,
        )
        try:
            structured = client.converse_structured(
                alias, prompt, SCHEMAS[task], context=context, use_cache=False, max_tokens=MAX_TOKENS[task]
            )
        except Exception as error:  # API, budget, or infrastructure failure; never a model score
            record.update(
                status="void_infra", failure_type="infra", failure_detail=str(error)[:500], finished_at=now()
            )
            _append(task, record)
            summary["void_infra"] += 1
            summary["consecutive_infra"] += 1
            if summary["consecutive_infra"] >= 5:
                raise SystemExit("stopped after five consecutive infrastructure failures")
            return

        summary["consecutive_infra"] = 0
        invocation = structured.result.record
        (run_dir / "response.txt").write_text(structured.result.text or "")
        record.update(
            invocation_ids=[invocation.invocation_id],
            parse_ok=structured.parsed is not None,
            truncated=bool(invocation.truncated),
            generation_ms=invocation.latency_ms,
            input_tokens=invocation.input_tokens,
            output_tokens=invocation.output_tokens,
            reasoning_chars=invocation.reasoning_chars,
            cost_usd=invocation.cost_usd,
            cost_status=invocation.cost_status,
            artifacts=[str((run_dir / name).relative_to(REPO)) for name in ("prompt.txt", "response.txt")],
        )
        if structured.parsed is not None:
            (run_dir / "parsed.json").write_text(structured.parsed.model_dump_json(indent=2))
            record["artifacts"].append(str((run_dir / "parsed.json").relative_to(REPO)))

        if task == "a1":
            harness = None
            if structured.parsed is not None:
                solution = run_dir / "solution.py"
                tests = run_dir / "tests.json"
                solution.write_text(structured.parsed.fixed_code)
                tests.write_text(json.dumps(case["hidden"]))
                execution = executor.execute(
                    A1_HARNESS_V2, {"solution.py": str(solution), "tests.json": str(tests)}, str(run_dir / "output")
                )
                record["execution"] = {
                    "status": execution.status.value,
                    "runtime_ms": execution.runtime_ms,
                    "sandbox_image": execution.sandbox_image,
                    "stderr_tail": (execution.stderr or "")[-400:],
                }
                if execution.status.value == "sandbox_unavailable":
                    record.update(
                        status="void_infra", failure_type="infra", failure_detail=(execution.stderr or "")[:300],
                        finished_at=now(),
                    )
                    _append(task, record)
                    summary["void_infra"] += 1
                    return
                result_path = run_dir / "output/results.json"
                harness = json.loads(result_path.read_text()) if result_path.exists() else None
            scores = score_debugging_v2(case, structured.parsed, harness)
        elif task == "a2":
            envelope = ExtractionEnvelope(
                fields=structured.parsed.fields if structured.parsed is not None else None,
                wrapper_present=structured.parsed is not None,
                parse_ok=structured.parsed is not None,
            )
            scores = score_extraction_v2(case, envelope)
        else:
            scores = score_literature_v2(case, structured.parsed)

        operational = bool(scores["operational_success"])
        record.update(
            scores=scores,
            status="passed" if operational else "failed",
            failure_type=None if operational else ("truncated" if invocation.truncated else "validation_failed"),
            failure_detail=None if operational else str(structured.parse_error or "operational requirements not met")[:500],
            finished_at=now(),
        )
        _append(task, record)
        summary["executed"] += 1

    with executor.image_lease(gate.image_id):
        for task in ("a1", "a2", "a3"):
            for case in load_cases(task):
                for alias in STUDY_MODELS:
                    one(task, case, alias)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-api-attempts", type=int)
    parser.add_argument("--max-input-tokens", type=int)
    parser.add_argument("--max-output-tokens", type=int)
    parser.add_argument("--max-budget-usd", type=float)
    args = parser.parse_args(argv)
    planned = plan()
    print(json.dumps({key: value for key, value in planned.items() if key != "runs"}, indent=2))
    if not args.execute:
        print("PLAN ONLY: no AWS client created and no model call made.")
        return 0
    if None in (args.max_api_attempts, args.max_input_tokens, args.max_output_tokens, args.max_budget_usd):
        raise SystemExit(
            "--execute requires --max-api-attempts, --max-input-tokens, "
            "--max-output-tokens and --max-budget-usd"
        )
    if not (0 < args.max_api_attempts <= MAX_API_ATTEMPTS):
        raise SystemExit(f"max API attempts must be between 1 and {MAX_API_ATTEMPTS}")
    if not (0 < args.max_input_tokens <= MAX_INPUT_TOKENS):
        raise SystemExit(f"max input tokens must be between 1 and {MAX_INPUT_TOKENS}")
    if not (0 < args.max_output_tokens <= MAX_OUTPUT_TOKENS):
        raise SystemExit(f"max output tokens must be between 1 and {MAX_OUTPUT_TOKENS}")
    if not (0 < args.max_budget_usd <= MAX_BUDGET_USD):
        raise SystemExit(f"max dollar budget must be between $0 and ${MAX_BUDGET_USD:.2f}")
    if planned["planned_logical_calls"] > MAX_LOGICAL_CALLS:
        raise SystemExit("planned logical calls exceed the frozen protocol")
    from src.bedrock.usage import UsageLimits

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ledger = REPO / "results/raw/ledgers" / f"independent_v2_{timestamp}.json"
    summary = execute(
        UsageLimits(
            max_calls=args.max_api_attempts,
            max_input_tokens=args.max_input_tokens,
            max_output_tokens=args.max_output_tokens,
            max_budget_usd=args.max_budget_usd,
        ),
        ledger,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
