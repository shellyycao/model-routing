"""Audit and summarize the completed Independent-v2 benchmark (offline only).

The frozen scores are never overwritten. A3 additionally reports two disclosed
sensitivity views because the frozen scorer assigns numerical ranking scores even
when a response repeats IDs and therefore fails ``ranking_valid``.
"""

from __future__ import annotations

import collections
import hashlib
import json
import math
import random
import statistics as stats
from pathlib import Path

from experiments import run_independent_v2_benchmark as runner
from src.bedrock.models import load_registry
from src.bedrock.provenance import hash_file


REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "results/raw/independent_v2"
PROCESSED = REPO / "results/processed/independent_v2"
REPORT = REPO / "results/reports/independent_v2_benchmark.md"
FILES = {task: f"{experiment_id}.jsonl" for task, experiment_id in runner.EXPERIMENT_IDS.items()}
NAMES = {"A": "Claude Sonnet 4.6", "B": "Amazon Nova Pro", "C": "OpenAI gpt-oss-120b"}
DIFFICULTIES = ("easy", "medium", "hard")


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _median(values: list[float]) -> float | None:
    return stats.median(values) if values else None


def _wilson(successes: int, n: int, z: float = 1.96) -> list[float] | None:
    if not n:
        return None
    p = successes / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [max(0.0, centre - radius), min(1.0, centre + radius)]


def _bootstrap_mean_ci(values: list[float], *, seed: int, draws: int = 20_000) -> list[float] | None:
    if not values:
        return None
    rng = random.Random(seed)
    n = len(values)
    estimates = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws))
    return [estimates[int(0.025 * draws)], estimates[int(0.975 * draws) - 1]]


def _load_records() -> tuple[dict[str, list[dict]], dict[str, str]]:
    records, sources = {}, {}
    for task, filename in FILES.items():
        path = RAW / filename
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        records[task] = rows
        sources[str(path.relative_to(REPO))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return records, sources


def _find_matching_ledger(records: dict[str, list[dict]]) -> tuple[Path, dict]:
    all_rows = [row for rows in records.values() for row in rows]
    expected = {
        "calls": len(all_rows),
        "input_tokens": sum(row.get("input_tokens") or 0 for row in all_rows),
        "output_tokens": sum(row.get("output_tokens") or 0 for row in all_rows),
    }
    matches = []
    for path in sorted((REPO / "results/raw/ledgers").glob("independent_v2_*.json")):
        ledger = json.loads(path.read_text())
        if all(ledger.get(key) == value for key, value in expected.items()):
            matches.append((path, ledger))
    if len(matches) != 1:
        raise ValueError(f"expected one matching v2 ledger, found {len(matches)}")
    return matches[0]


def audit(records: dict[str, list[dict]], ledger: dict) -> dict:
    registry = load_registry()
    run_ids, invocation_ids = set(), set()
    errors = []
    expected_models = set(runner.STUDY_MODELS)
    for task, rows in records.items():
        cases = {case["case_id"]: case for case in runner.load_cases(task)}
        expected_cells = {(case_id, alias) for case_id in cases for alias in expected_models}
        observed_cells = {(row["case_id"], row["model_alias"]) for row in rows}
        if len(rows) != 90 or observed_cells != expected_cells:
            errors.append(f"{task}: incomplete or duplicate case-model matrix")
        for row in rows:
            case = cases[row["case_id"]]
            if row["run_id"] in run_ids:
                errors.append(f"duplicate run_id {row['run_id']}")
            run_ids.add(row["run_id"])
            for invocation_id in row["invocation_ids"]:
                if invocation_id in invocation_ids:
                    errors.append(f"duplicate invocation_id {invocation_id}")
                invocation_ids.add(invocation_id)
            prompt = runner.render(task, case)
            expected = {
                "run_id": runner.run_id(registry, task, case, row["model_alias"], 0),
                "model_id": registry.get(row["model_alias"]).model_id,
                "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
                "case_hash": hash_file(runner.DATA / task / "cases" / f"{row['case_id']}.json"),
            }
            for field, value in expected.items():
                if row.get(field) != value:
                    errors.append(f"{row['run_id']}: {field} mismatch")
            for artifact in row["artifacts"]:
                if not (REPO / artifact).is_file():
                    errors.append(f"{row['run_id']}: missing artifact {artifact}")

    all_rows = [row for rows in records.values() for row in rows]
    totals = {
        "records": len(all_rows),
        "calls": ledger["calls"],
        "input_tokens": sum(row.get("input_tokens") or 0 for row in all_rows),
        "output_tokens": sum(row.get("output_tokens") or 0 for row in all_rows),
        "cost_usd": sum(row.get("cost_usd") or 0.0 for row in all_rows),
    }
    comparisons = {
        "input_tokens": ledger["input_tokens"],
        "output_tokens": ledger["output_tokens"],
        "cost_usd": ledger["spent_usd_priced"],
    }
    for field, value in comparisons.items():
        if not math.isclose(totals[field], value, rel_tol=0, abs_tol=1e-9):
            errors.append(f"ledger {field} mismatch")
    if ledger["calls"] != len(all_rows):
        errors.append("ledger call count mismatch")
    if ledger["pending"] or ledger["failed_attempts"] or ledger["unknown_usage_calls"]:
        errors.append("ledger contains pending, failed, or unknown-usage attempts")
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "unique_run_ids": len(run_ids),
        "unique_invocation_ids": len(invocation_ids),
        "totals": totals,
        "failed_attempts": ledger["failed_attempts"],
        "unknown_usage_calls": ledger["unknown_usage_calls"],
        "unpriced_calls": ledger["unpriced_calls"],
        "dollar_guard_active": ledger["dollar_guard_active"],
        "limits": ledger["limits"],
    }


def _metric_summary(values: list[float], seed: int) -> dict:
    return {"mean": _mean(values), "bootstrap_95": _bootstrap_mean_ci(values, seed=seed), "n": len(values)}


def summarize(records: dict[str, list[dict]]) -> dict:
    cells = {}
    metric_names = {
        "a1": ("hidden_pass_rate", "bug_location_recall"),
        "a2": ("content_f1", "content_precision", "content_recall", "null_accuracy"),
        "a3": ("ndcg_at_5", "grade2_recall_at_5", "citation_accuracy", "evidence_grounding"),
    }
    binary_primary = {"a1": "functional_correct", "a2": "content_correct"}
    for task, rows in records.items():
        for alias in runner.STUDY_MODELS:
            model_rows = [row for row in rows if row["model_alias"] == alias]
            cell = {
                "task": task,
                "model_alias": alias,
                "model_name": NAMES[alias],
                "n": len(model_rows),
                "status_pass": sum(row["status"] == "passed" for row in model_rows),
                "operational_success": sum(bool(row["scores"].get("operational_success")) for row in model_rows),
                "parse_ok": sum(bool(row.get("parse_ok")) for row in model_rows),
                "truncated": sum(bool(row.get("truncated")) for row in model_rows),
                "cost_usd": sum(row.get("cost_usd") or 0.0 for row in model_rows),
                "input_tokens": sum(row.get("input_tokens") or 0 for row in model_rows),
                "output_tokens": sum(row.get("output_tokens") or 0 for row in model_rows),
                "generation_seconds_median": _median([(row.get("generation_ms") or 0.0) / 1000 for row in model_rows]),
                "metrics": {},
                "by_difficulty": {},
            }
            if task in binary_primary:
                name = binary_primary[task]
                successes = sum(bool(row["scores"].get(name)) for row in model_rows)
                cell["primary"] = {
                    "name": name,
                    "successes": successes,
                    "rate": successes / len(model_rows),
                    "wilson_95": _wilson(successes, len(model_rows)),
                }
            else:
                frozen = [float(row["scores"].get("ndcg_at_5", 0.0)) for row in model_rows]
                valid = [row for row in model_rows if row["scores"].get("ranking_valid")]
                valid_values = [float(row["scores"]["ndcg_at_5"]) for row in valid]
                strict_values = [
                    float(row["scores"].get("ndcg_at_5", 0.0)) if row["scores"].get("ranking_valid") else 0.0
                    for row in model_rows
                ]
                cell["primary"] = {
                    "name": "ndcg_at_5",
                    "frozen_all_case": _metric_summary(frozen, seed=300 + ord(alias)),
                    "valid_ranking_only": _metric_summary(valid_values, seed=400 + ord(alias)),
                    "strict_invalid_as_zero": _metric_summary(strict_values, seed=500 + ord(alias)),
                    "ranking_valid": len(valid),
                    "frozen_values_over_one": sum(value > 1.0 + 1e-12 for value in frozen),
                    "grade2_recall_values_over_one": sum(
                        float(row["scores"].get("grade2_recall_at_5", 0.0)) > 1.0 + 1e-12 for row in model_rows
                    ),
                }
            for metric_index, name in enumerate(metric_names[task]):
                values = [
                    float(row["scores"][name]) for row in model_rows if row["scores"].get(name) is not None
                ]
                cell["metrics"][name] = _metric_summary(
                    values, seed=1000 * (1 + list(FILES).index(task)) + 100 * ord(alias) + metric_index
                )
            for difficulty in DIFFICULTIES:
                subset = [row for row in model_rows if row["scores"].get("difficulty") == difficulty]
                if task in binary_primary:
                    name = binary_primary[task]
                    values = [float(bool(row["scores"].get(name))) for row in subset]
                else:
                    values = [
                        float(row["scores"].get("ndcg_at_5", 0.0))
                        if row["scores"].get("ranking_valid") else 0.0
                        for row in subset
                    ]
                cell["by_difficulty"][difficulty] = {
                    "n": len(subset),
                    "primary_mean": _mean(values),
                    "operational_rate": _mean(
                        [float(bool(row["scores"].get("operational_success"))) for row in subset]
                    ),
                }
            cells[f"{task}|{alias}"] = cell
    return cells


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{100 * value:.1f}%"


def _num(value: float | None, digits: int = 3) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def render_report(result: dict) -> str:
    audit_result, cells = result["audit"], result["cells"]
    totals = audit_result["totals"]
    lines = [
        "# Independent Benchmark v2 Results",
        "",
        "**Protocol:** `independent-v2-1.1` / tag `independent-v2-frozen-v1.1`  ",
        "**Execution date:** 2026-11-18  ",
        f"**Integrity audit:** {audit_result['status'].upper()}  ",
        "",
        "## Execution and accounting",
        "",
        f"All {totals['records']} planned model-case cells completed. The ledger records "
        f"{totals['calls']} API attempts, {totals['input_tokens']:,} input tokens, "
        f"{totals['output_tokens']:,} output tokens, and ${totals['cost_usd']:.7f}. "
        f"There were {audit_result['failed_attempts']} failed attempts, "
        f"{audit_result['unknown_usage_calls']} unknown-usage calls, and "
        f"{audit_result['unpriced_calls']} unpriced calls.",
        "",
        "## Primary results",
        "",
        "| Task | Model | Operational | Primary result | Parse | Truncated | Cost |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for task in FILES:
        for alias in runner.STUDY_MODELS:
            cell = cells[f"{task}|{alias}"]
            if task in ("a1", "a2"):
                primary = f"{cell['primary']['successes']}/{cell['n']} ({_pct(cell['primary']['rate'])})"
            else:
                primary = _num(cell["primary"]["strict_invalid_as_zero"]["mean"])
            lines.append(
                f"| {task.upper()} | {cell['model_name']} | {_pct(cell['operational_success'] / cell['n'])} | "
                f"{primary} | {cell['parse_ok']}/{cell['n']} | {cell['truncated']} | ${cell['cost_usd']:.4f} |"
            )
    lines += [
        "",
        "A1 primary is functional correctness; A2 primary is content correctness. For A3, the table uses the "
        "disclosed strict sensitivity view in which a response that fails the frozen `ranking_valid` contract receives "
        "zero nDCG. Cell-level Wilson or deterministic bootstrap 95% intervals are stored in the JSON artifact.",
        "",
        "## Secondary metrics",
        "",
        "| Task | Model | Hidden pass / content F1 / valid-only nDCG | Bug-location / null accuracy / grounding | Citation accuracy | Median generation |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for task in FILES:
        for alias in runner.STUDY_MODELS:
            cell = cells[f"{task}|{alias}"]
            if task == "a1":
                first = cell["metrics"]["hidden_pass_rate"]["mean"]
                second = cell["metrics"]["bug_location_recall"]["mean"]
                citation = None
            elif task == "a2":
                first = cell["metrics"]["content_f1"]["mean"]
                second = cell["metrics"]["null_accuracy"]["mean"]
                citation = None
            else:
                first = cell["primary"]["valid_ranking_only"]["mean"]
                second = cell["metrics"]["evidence_grounding"]["mean"]
                citation = cell["metrics"]["citation_accuracy"]["mean"]
            lines.append(
                f"| {task.upper()} | {cell['model_name']} | {_num(first)} | {_num(second)} | "
                f"{_num(citation)} | {cell['generation_seconds_median']:.2f}s |"
            )
    lines += [
        "",
        "## Difficulty stratification",
        "",
        "Primary means are functional-correctness rate for A1, content-correctness rate for A2, and strict "
        "invalid-as-zero nDCG for A3.",
        "",
        "| Task | Model | Easy | Medium | Hard |",
        "|---|---|---:|---:|---:|",
    ]
    for task in FILES:
        for alias in runner.STUDY_MODELS:
            cell = cells[f"{task}|{alias}"]
            vals = [cell["by_difficulty"][difficulty]["primary_mean"] for difficulty in DIFFICULTIES]
            lines.append(
                f"| {task.upper()} | {cell['model_name']} | {_num(vals[0])} | {_num(vals[1])} | {_num(vals[2])} |"
            )
    a3 = [cells[f"a3|{alias}"] for alias in runner.STUDY_MODELS]
    lines += [
        "",
        "## Frozen A3 scorer audit",
        "",
        "The frozen scorer computes nDCG and grade-2 recall even when the submitted ranking repeats IDs and fails "
        "`ranking_valid`. Duplicates can therefore produce values above 1. The raw frozen values remain unchanged; "
        "they are not used as the sole headline view.",
        "",
        "| Model | Valid rankings | Frozen all-case nDCG | Valid-only nDCG | Strict invalid=0 nDCG | nDCG > 1 | Recall > 1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for cell in a3:
        primary = cell["primary"]
        lines.append(
            f"| {cell['model_name']} | {primary['ranking_valid']}/30 | "
            f"{_num(primary['frozen_all_case']['mean'])} | {_num(primary['valid_ranking_only']['mean'])} | "
            f"{_num(primary['strict_invalid_as_zero']['mean'])} | {primary['frozen_values_over_one']} | "
            f"{primary['grade2_recall_values_over_one']} |"
        )
    lines += [
        "",
        "## Interpretation limits",
        "",
        "- These are 30 fixed cases per task and one deterministic-temperature run per model-case cell; inference is bounded to this benchmark.",
        "- No single composite pools A1, A2, and A3.",
        "- A1 bug-location recall is a strict string-overlap diagnostic and is not a substitute for functional correctness.",
        "- A3 evidence grounding requires exact accepted fact values in structured claims; it should be read separately from ranking and citation validity.",
        "- The A3 strict and valid-only views are disclosed sensitivity analyses prompted by a frozen-scorer defect; the original scores remain in the raw records.",
        "",
        "## Reproducibility",
        "",
        "```bash",
        ".venv/bin/python -m experiments.analyze_independent_v2",
        "```",
        "",
    ]
    return "\n".join(lines)


def analyze() -> dict:
    records, sources = _load_records()
    ledger_path, ledger = _find_matching_ledger(records)
    sources[str(ledger_path.relative_to(REPO))] = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
    result = {
        "analysis_version": "independent-v2-analysis-1.0",
        "protocol_version": "independent-v2-1.1",
        "frozen_tag": runner.FROZEN_TAG,
        "sources": sources,
        "audit": audit(records, ledger),
        "cells": summarize(records),
    }
    if result["audit"]["status"] != "pass":
        raise ValueError(f"integrity audit failed: {result['audit']['errors']}")
    return result


def main() -> int:
    result = analyze()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    (PROCESSED / "analysis.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(result))
    print(json.dumps({
        "audit": result["audit"]["status"],
        "records": result["audit"]["totals"]["records"],
        "cost_usd": result["audit"]["totals"]["cost_usd"],
        "analysis": str((PROCESSED / "analysis.json").relative_to(REPO)),
        "report": str(REPORT.relative_to(REPO)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
