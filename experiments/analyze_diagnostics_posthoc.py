"""Offline post-hoc diagnostics for the two workflow model groups.

This module never calls a model.  The only execution it can perform is a replay of already-saved
model code in the protocol's immutable Docker image, with a narrowly-scoped ``json.dump`` default
that converts NumPy scalar values to Python scalars.  Frozen records and validators are read-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable

from experiments.analyze_cost_aware_router_posthoc import cost_direction, naive_price_score
from src.analysis.reruns import resolve_workflow_reruns
from experiments.run_price_matched_workflow import registry as price_matched_registry
from src.contracts import ResourceLimits, StageBenchmarkRecord, WorkflowRunRecord
from src.evaluation.analysis import validate_analysis
from src.evaluation.cleaning import load_project, validate_cleaning
from src.evaluation.reporting import _derived_value, _float_unit, number_matches
from src.workflow.executor import DockerExecutor
from src.workflow.stages import model_input_files

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results/processed/diagnostics_posthoc.json"
REPORT = REPO / "results/reports/diagnostics_posthoc.md"
REPLAY_ROOT = REPO / "results/processed/diagnostics_posthoc_replay"
PINNED_IMAGE = "sha256:88988a15503bdb96538c3dd62244a79879d5c7848397db18b1267ccfd0a9727a"
INT64_ERROR = "Object of type int64 is not JSON serializable"

GROUPS = {
    "original_4096": {
        "label": "Original model group (maxTokens 4096)",
        "max_tokens": 4096,
        "part_a": REPO / "results/raw/stage_benchmark/expA_stage_v3.jsonl",
        "part_b": REPO / "results/raw/workflow_runs/expB_paths_v3.jsonl",
        "invocations": REPO / "results/raw/invocations.jsonl",
        "experiments": {"expA_stage_v3", "expB_paths_v3"},
        "names": {"A": "Sonnet 4.6", "B": "Amazon Nova Pro", "C": "OpenAI gpt-oss-120b"},
        "v31_a": REPO / "results/processed/v3_1_rescore/expA_stage_v3_reporting.json",
        "v31_b": REPO / "results/processed/v3_1_rescore/expB_paths_v3_reporting.json",
    },
    "price_matched_16384": {
        "label": "Price-matched workflow group (maxTokens 16384)",
        "max_tokens": 16384,
        "part_a": REPO / "results/raw/stage_benchmark/expA_price_matched_workflow_v3.jsonl",
        "part_b": REPO / "results/raw/workflow_runs/expB_price_matched_workflow_v3.jsonl",
        "invocations": REPO / "results/raw/price_matched_workflow/invocations.jsonl",
        "experiments": {"expA_price_matched_workflow_v3", "expB_price_matched_workflow_v3"},
        "names": {"A": "Sonnet 4.6", "B": "Kimi K3", "C": "GLM 5"},
        "v31_a": REPO / "results/processed/v3_1_rescore/expA_price_matched_workflow_v3_reporting.json",
        "v31_b": REPO / "results/processed/v3_1_rescore/expB_price_matched_workflow_v3_reporting.json",
    },
}

PATCH = '''# POST-HOC DIAGNOSTIC PATCH: preserve all model logic; only teach json.dump how to\n# serialize NumPy scalar values. No arrays, dataframes, or other objects are converted.\nimport json as _diag_json\n_diag_original_dump = _diag_json.dump\ndef _diag_numpy_scalar(value):\n    module = type(value).__module__.split(".")[0]\n    item = getattr(value, "item", None)\n    if module == "numpy" and callable(item):\n        converted = item()\n        if converted is None or isinstance(converted, (str, int, float, bool)):\n            return converted\n    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")\ndef _diag_dump(obj, fp, *args, **kwargs):\n    kwargs.setdefault("default", _diag_numpy_scalar)\n    return _diag_original_dump(obj, fp, *args, **kwargs)\n_diag_json.dump = _diag_dump\n'''


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return values[lo] if lo == hi else values[lo] * (hi - pos) + values[hi] * (pos - lo)


def distribution(values: Iterable[float]) -> dict[str, Any]:
    vals = [float(v) for v in values]
    return {"n": len(vals), "min": min(vals) if vals else None, "p25": percentile(vals, .25),
            "median": percentile(vals, .5), "p75": percentile(vals, .75),
            "max": max(vals) if vals else None, "mean": statistics.fmean(vals) if vals else None}


def load_group(key: str) -> tuple[list[StageBenchmarkRecord], list[WorkflowRunRecord], list[WorkflowRunRecord]]:
    cfg = GROUPS[key]
    a = [StageBenchmarkRecord.model_validate(row) for row in read_jsonl(cfg["part_a"])]
    raw_b = [WorkflowRunRecord.model_validate(row) for row in read_jsonl(cfg["part_b"])]
    if key == "price_matched_16384":
        b, _ = resolve_workflow_reruns(raw_b)
    else:
        b = raw_b
    return a, raw_b, b


def iter_stage_rows(a: list[StageBenchmarkRecord], b: list[WorkflowRunRecord]):
    for row in a:
        yield "A", row.run_id, row.project_id, None, row.repeat_index, row.record
    for row in b:
        for stage in row.stages:
            yield "B", row.run_id, row.project_id, row.path_id, row.repeat_index, stage


def int64_candidates() -> list[dict[str, Any]]:
    found = []
    for group in GROUPS:
        a, _, b = load_group(group)
        for part, run_id, project, path, repeat, stage in iter_stage_rows(a, b):
            if INT64_ERROR not in str(stage.failure_detail):
                continue
            code = next((REPO / p for p in stage.output_artifacts if p.endswith("/code.py")), None)
            parsed = next((REPO / p for p in stage.output_artifacts if p.endswith("/parsed.json")), None)
            found.append({"group": group, "part": part, "run_id": run_id, "project_id": project,
                          "path_id": path, "repeat_index": repeat, "stage": stage.stage.value,
                          "model_alias": stage.model_alias, "model_name": GROUPS[group]["names"][stage.model_alias],
                          "code_path": str(code.relative_to(REPO)), "parsed_path": str(parsed.relative_to(REPO))})
    return found


def patched_code(code: str) -> str:
    return PATCH + "\n" + code


def replay_candidate(candidate: dict[str, Any], executor: DockerExecutor, root: Path) -> dict[str, Any]:
    project_dir = REPO / "datasets/projects" / candidate["project_id"]
    spec, _, _ = load_project(project_dir)
    code_path = REPO / candidate["code_path"]
    parsed = json.loads((REPO / candidate["parsed_path"]).read_text())
    code = patched_code(code_path.read_text())
    out_dir = root / candidate["run_id"] / candidate["stage"]
    out_dir.mkdir(parents=True, exist_ok=False)
    if candidate["stage"] == "analysis":
        record_source = GROUPS[candidate["group"]]["part_a" if candidate["part"] == "A" else "part_b"]
        top = next(r for r in read_jsonl(record_source) if r["run_id"] == candidate["run_id"])
        stage = top["record"] if candidate["part"] == "A" else next(s for s in top["stages"] if s["stage"] == "analysis")
        cleaned = next(REPO / p for p in stage["input_artifacts"] if p.endswith(".csv"))
        inputs = {spec.cleaned_data_filename: str(cleaned)}
        expected = out_dir / spec.findings_filename
    elif candidate["stage"] == "cleaning":
        inputs = model_input_files(spec, project_dir)
        expected = out_dir / parsed["output_filename"]
    else:
        raise ValueError(f"unsupported replay stage: {candidate['stage']}")
    result = executor.execute(code, inputs, str(out_dir), ResourceLimits())
    validation = (validate_analysis(expected, project_dir) if candidate["stage"] == "analysis"
                  else validate_cleaning(expected, project_dir))
    return candidate | {
        "original_code_sha256": sha256(code_path),
        "patched_code_sha256": hashlib.sha256(code.encode()).hexdigest(),
        "patch_scope": "json.dump default converts NumPy scalar .item() only",
        "execution": result.model_dump(mode="json"),
        "output_path": str(expected.relative_to(REPO)) if expected.exists() else str(expected),
        "output_sha256": sha256(expected) if expected.exists() else None,
        "frozen_validation": validation.model_dump(mode="json"),
        "would_pass_without_serialization_bug": bool(validation.hard_pass),
    }


def run_replays(root: Path) -> dict[str, Any]:
    candidates = int64_candidates()
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"replay output directory is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    executor = DockerExecutor(image=PINNED_IMAGE)
    available, detail = executor.availability()
    if not available:
        raise RuntimeError(f"pinned diagnostic sandbox unavailable: {detail}")
    rows = [replay_candidate(c, executor, root) for c in candidates]
    grouped = defaultdict(lambda: {"n": 0, "would_pass": 0})
    for row in rows:
        key = f"{row['group']}|{row['part']}|{row['stage']}|{row['model_name']}"
        grouped[key]["n"] += 1
        grouped[key]["would_pass"] += row["would_pass_without_serialization_bug"]
    return {"label": "post-hoc serialization-only replay in pinned image", "pinned_image": PINNED_IMAGE,
            "patch": PATCH, "n_candidates": len(candidates), "summary": dict(sorted(grouped.items())),
            "records": rows}


def mandatory_failures(validation: Any) -> set[str]:
    if validation is None:
        return set()
    data = validation.model_dump(mode="json") if hasattr(validation, "model_dump") else validation
    return {c["name"] for c in data.get("checks", []) if c.get("mandatory") and not c.get("passed")}


def report_artifact(stage: Any) -> Path | None:
    paths = stage.output_artifacts if hasattr(stage, "output_artifacts") else stage.get("output_artifacts", [])
    return next((REPO / p for p in paths if p.endswith("/report.json")), None)


def decimal_places(value: Decimal) -> int:
    return max(0, -value.as_tuple().exponent)


def rounded_match(stated: Decimal, expected: float) -> bool:
    places = decimal_places(stated)
    quantum = Decimal(1).scaleb(-places)
    rounded = Decimal(str(expected)).quantize(quantum, rounding=ROUND_HALF_UP)
    return stated == rounded


def rounding_recoverable(report_path: Path, project_id: str) -> tuple[bool, list[dict[str, Any]]]:
    report = json.loads(report_path.read_text(), parse_float=Decimal, parse_int=Decimal)
    spec, gt, _ = load_project(REPO / "datasets/projects" / project_id)
    verified = gt["analysis"]["metrics"]
    tol = {k: (q.abs_tolerance, q.rel_tolerance) for q in spec.analysis_questions for k in q.metric_keys}
    details, bad = [], False
    for finding in report.get("key_findings", []):
        for dv in finding.get("derived_values", []):
            operands = dv.get("operands", [])
            if len(operands) != 2 or any(k not in verified for k in operands):
                bad = True
                continue
            expected = _derived_value(dv.get("kind"), float(verified[operands[0]]), float(verified[operands[1]]))
            stated = dv.get("value")
            if expected is None or not isinstance(stated, Decimal):
                bad = True
                continue
            abs_tol = max(tol.get(k, (1e-6, 1e-4))[0] for k in operands)
            rel_tol = max(tol.get(k, (1e-6, 1e-4))[1] for k in operands)
            frozen_ok = number_matches(float(stated), expected, _float_unit(float(stated)), abs_tol, rel_tol)
            if frozen_ok:
                continue
            ok = rounded_match(stated, expected)
            details.append({"finding_id": finding.get("finding_id"), "kind": dv.get("kind"),
                            "operands": operands, "stated": str(stated), "recomputed": expected,
                            "reported_decimal_places": decimal_places(stated), "rounds_to_stated": ok})
            bad |= not ok
    return bool(details) and not bad, details


def v31_transitions(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {}
    for path in (cfg["v31_a"], cfg["v31_b"]):
        for row in json.loads(path.read_text())["records"]:
            if not row["v3_ground_truth"]["hard_pass"] and row["v31_ground_truth"]["hard_pass"]:
                rows[row["run_id"]] = row
    return rows


def reporting_rounding() -> dict[str, Any]:
    all_rows, summary, q7 = [], {}, []
    for group, cfg in GROUPS.items():
        a, _, b = load_group(group)
        transitions = v31_transitions(cfg)
        by_model = defaultdict(lambda: {"scored": 0, "v3_passed": 0, "rounding_only_recovered": 0})
        for part, run_id, project, path, repeat, stage in iter_stage_rows(a, b):
            if stage.stage.value != "reporting" or stage.validation is None:
                continue
            item = by_model[cfg["names"][stage.model_alias]]
            item["scored"] += 1
            item["v3_passed"] += bool(stage.validation.hard_pass)
            failures = mandatory_failures(stage.validation)
            if failures == {"derived_values_correct"}:
                report = report_artifact(stage)
                if report and report.exists():
                    recoverable, details = rounding_recoverable(report, project)
                    row = {"group": group, "part": part, "run_id": run_id, "project_id": project,
                           "path_id": path, "repeat_index": repeat, "model_alias": stage.model_alias,
                           "model_name": cfg["names"][stage.model_alias], "recoverable": recoverable,
                           "report_path": str(report.relative_to(REPO)), "details": details}
                    all_rows.append(row)
                    item["rounding_only_recovered"] += recoverable
            if run_id in transitions:
                q7.append({"group": group, "part": part, "run_id": run_id, "project_id": project,
                           "path_id": path, "repeat_index": repeat, "model_alias": stage.model_alias,
                           "model_name": cfg["names"][stage.model_alias]})
        for model, item in by_model.items():
            item["reasonable_rounding_passed"] = item["v3_passed"] + item["rounding_only_recovered"]
            item["reasonable_rounding_rate"] = item["reasonable_rounding_passed"] / item["scored"]
        summary[group] = dict(sorted(by_model.items()))
    return {"label": "post-hoc sensitivity; frozen v3 is unchanged", "denominator":
            "reporting stages with a frozen ground-truth validation", "per_model": summary,
            "derived_values_only_candidates": all_rows, "known_q7_v31_false_rejects": q7}


def truncation() -> dict[str, Any]:
    result = {}
    for group, cfg in GROUPS.items():
        a, _, b = load_group(group)
        inv = [r for r in read_jsonl(cfg["invocations"]) if r["context"]["experiment_id"] in cfg["experiments"]]
        per = defaultdict(lambda: {"invocations": 0, "stop_reason_max_tokens": 0, "truncated_flag": 0})
        for row in inv:
            key = f"{cfg['names'][row['model_alias']]}|{row['context']['stage_id']}"
            per[key]["invocations"] += 1
            per[key]["stop_reason_max_tokens"] += row.get("stop_reason") == "max_tokens"
            per[key]["truncated_flag"] += bool(row.get("truncated"))
        caused = []
        for part, run_id, project, path, repeat, stage in iter_stage_rows(a, b):
            if part == "B" and str(stage.failure_type.value if stage.failure_type else "") == "truncated":
                caused.append({"run_id": run_id, "project_id": project, "path_id": path,
                               "repeat_index": repeat, "stage": stage.stage.value,
                               "model_name": cfg["names"][stage.model_alias]})
        result[group] = {"max_tokens": cfg["max_tokens"], "per_model_stage": dict(sorted(per.items())),
                         "workflow_stage_failures_caused_by_truncation": caused,
                         "n_workflow_stage_failures_caused_by_truncation": len(caused),
                         "n_distinct_workflows_affected": len({r["run_id"] for r in caused})}
    return result


def cost_sanity() -> dict[str, Any]:
    base = REPO / "results/routing/price_matched_workflow_v3_cost_posthoc"
    preds = {r["record"]["prediction_id"]: r["record"] for r in read_jsonl(base / "counterfactual_predictions.jsonl")}
    vals = [r["record"] for r in read_jsonl(base / "counterfactual_validations.jsonl")]
    registry = price_matched_registry(16384)
    rows = []
    for value in vals:
        pred = preds[value["prediction_id"]]
        ps, pa = pred["predicted_selected"]["cost_usd"], pred["predicted_alternative"]["cost_usd"]
        acs, aca = value["actual_selected"]["cost_usd"], value["actual_alternative"]["cost_usd"]
        pd, ad = pa - ps, aca - acs
        ns, na = naive_price_score(pred["selected_path_id"], registry), naive_price_score(pred["alternative_path_id"], registry)
        rows.append({"prediction_id": value["prediction_id"], "predicted_delta_usd": pd,
                     "actual_delta_usd": ad, "abs_actual_delta_usd": abs(ad),
                     "actual_relative_gap_to_selected": abs(ad) / acs if acs else None,
                     "predicted_direction": cost_direction(pa, ps), "actual_direction": cost_direction(aca, acs),
                     "naive_direction": cost_direction(na, ns),
                     "prediction_match": cost_direction(pa, ps) == cost_direction(aca, acs),
                     "naive_match": cost_direction(na, ns) == cost_direction(aca, acs)})
    actual_dirs = Counter(r["actual_direction"] for r in rows)
    predicted_dirs = Counter(r["predicted_direction"] for r in rows)
    return {"label": "post-hoc cost-counterfactual sanity check", "n": len(rows),
            "token_cost_direction": {"matches": sum(r["prediction_match"] for r in rows), "n": len(rows)},
            "naive_unit_price_direction": {"matches": sum(r["naive_match"] for r in rows), "n": len(rows)},
            "direction_counts": {"predicted": dict(predicted_dirs), "actual": dict(actual_dirs)},
            "abs_actual_delta_usd": distribution(r["abs_actual_delta_usd"] for r in rows),
            "abs_predicted_delta_usd": distribution(abs(r["predicted_delta_usd"]) for r in rows),
            "relative_actual_gap_to_selected": distribution(r["actual_relative_gap_to_selected"] for r in rows),
            "naive_mismatches": [r for r in rows if not r["naive_match"]], "records": rows,
            "interpretation": ("The cost-aware rule explicitly chooses the minimum estimated-cost member of the "
                               "feasible Pareto set, so predicted alternatives are structurally expected to be no "
                               "cheaper. Perfect observed agreement is not tautological: executed token volumes "
                               "determine actual cost. The naive unit-price baseline isolates this distinction.")}


def render_report(result: dict[str, Any]) -> str:
    ser = result["serialization_replay"]
    analysis = [r for r in ser["records"] if r["stage"] == "analysis"]
    glm = [r for r in analysis if r["model_name"] == "GLM 5"]
    rounding = result["rounding_sensitivity"]
    rounding_n = sum(r["recoverable"] for r in rounding["derived_values_only_candidates"])
    trunc_n = sum(v["n_distinct_workflows_affected"] for v in result["truncation"].values())
    cost = result["cost_direction_sanity"]
    lines = ["# Post-hoc workflow diagnostics", "", "**POST-HOC / EXPLORATORY.** Frozen raw data, validators, scores, and conclusions remain unchanged.", "",
             "## Key findings", "",
             f"- The serialization-only replay recovered **{sum(r['would_pass_without_serialization_bug'] for r in glm)}/{len(glm)}** GLM 5 analysis failures and **{sum(r['would_pass_without_serialization_bug'] for r in analysis)}/{len(analysis)}** analysis failures overall under the frozen validator. These are counterfactual diagnostics, not revised benchmark scores.",
             f"- **{rounding_n}** reporting-stage failures that failed only `derived_values_correct` become passes under the stated-precision rounding sensitivity. Known q7 false rejects are listed separately (**{len(rounding['known_q7_v31_false_rejects'])}** records).",
             f"- Truncation caused failures in **{trunc_n}** distinct Part B workflows across both groups; invocation-level counts are broken down by model and stage below.",
             f"- Token-based cost direction was **{cost['token_cost_direction']['matches']}/{cost['token_cost_direction']['n']}**, versus **{cost['naive_unit_price_direction']['matches']}/{cost['naive_unit_price_direction']['n']}** for naive unit-price ordering. The median absolute executed-cost gap was **${cost['abs_actual_delta_usd']['median']:.4f}**.", "",
             "## 1. NumPy scalar serialization replay", "",
             "Saved code was replayed in the immutable protocol image with one patch: `json.dump` converts NumPy scalar values through `.item()`. Model logic, inputs, resource limits, and the frozen validators were unchanged. All original failures and partial outputs remain untouched.", "",
             "| Group / part / stage / model | Would pass | Candidates |", "|---|---:|---:|"]
    for key, item in ser["summary"].items():
        lines.append(f"| {key.replace('|', ' / ')} | {item['would_pass']} | {item['n']} |")
    lines += ["", "Each candidate and validator check is in `results/processed/diagnostics_posthoc.json` under `serialization_replay.records`; replay outputs are in `results/processed/diagnostics_posthoc_replay/`.", "",
              "## 2. Reporting precision sensitivity", "",
              "A record qualifies only when the frozen validator's sole mandatory failure is `derived_values_correct` and every otherwise-rejected derived value equals the recomputation rounded half-up to the decimal precision literally reported by the model. This does not replace v3.", "",
              "| Group | Model | Frozen v3 passes / scored | Rounding-only recovered | Sensitivity passes / scored |", "|---|---|---:|---:|---:|"]
    for group, models in rounding["per_model"].items():
        for model, item in models.items():
            lines.append(f"| {group} | {model} | {item['v3_passed']}/{item['scored']} | {item['rounding_only_recovered']} | {item['reasonable_rounding_passed']}/{item['scored']} |")
    lines += ["", f"Known q7 false rejects already covered by v3.1: **{len(rounding['known_q7_v31_false_rejects'])}**. They are not counted as rounding recoveries; identifiers are in the JSON.", "",
              "## 3. Truncation", "", "| Group | Model / stage | Invocations | max_tokens stop | truncated flag |", "|---|---|---:|---:|---:|"]
    for group, item in result["truncation"].items():
        for key, counts in item["per_model_stage"].items():
            lines.append(f"| {group} | {key.replace('|', ' / ')} | {counts['invocations']} | {counts['stop_reason_max_tokens']} | {counts['truncated_flag']} |")
    lines += ["", "Workflow failure attribution uses the frozen stage `failure_type=truncated`; a max-token stop that still parsed is shown at invocation level but is not called a caused workflow failure.", "",
              "## 4. Why cost direction was 64/64", "",
              cost["interpretation"], "",
              f"The 64 comparisons had executed absolute gaps: min ${cost['abs_actual_delta_usd']['min']:.4f}, p25 ${cost['abs_actual_delta_usd']['p25']:.4f}, median ${cost['abs_actual_delta_usd']['median']:.4f}, p75 ${cost['abs_actual_delta_usd']['p75']:.4f}, max ${cost['abs_actual_delta_usd']['max']:.4f}. Relative to selected-path cost, the median absolute gap was {100*cost['relative_actual_gap_to_selected']['median']:.1f}%. Actual directions were {cost['direction_counts']['actual']}. The naive baseline missed {len(cost['naive_mismatches'])}/64 because unit-price ordering ignores realized input/output token volumes; this is evidence that 64/64 is not guaranteed merely by path structure.", "",
              "## Scope and reproduction", "",
              "This report is a post-hoc artifact check. It does not modify frozen data, scorers, protocol claims, or the main report. Reproduce offline with:", "",
              "```bash", ".venv/bin/python -m experiments.analyze_diagnostics_posthoc", "```", "",
              "Sources: both Part A/B record stores, their invocation ledgers, saved stage artifacts, frozen project ground truth, v3.1 rescores, `configs/models.yaml`, and `results/routing/price_matched_workflow_v3_cost_posthoc/`.", ""]
    return "\n".join(lines)


def analyze(replay_root: Path) -> dict[str, Any]:
    return {"label": "post-hoc / exploratory; frozen results unchanged",
            "serialization_replay": run_replays(replay_root),
            "rounding_sensitivity": reporting_rounding(), "truncation": truncation(),
            "cost_direction_sanity": cost_sanity()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--replay-root", type=Path, default=REPLAY_ROOT)
    args = parser.parse_args()
    result = analyze(args.replay_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.report.write_text(render_report(result))


if __name__ == "__main__":
    main()
