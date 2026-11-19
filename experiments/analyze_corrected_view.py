"""Compute the additive CP8 corrected stage-level view (Q1), entirely offline.

The frozen records, validators, diagnostics and v3.1 rescores are read-only.  This analyzer does
not use continuation outcomes and therefore does not compute corrected Part B feasibility.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.analysis.reruns import resolve_workflow_reruns
from src.bedrock.provenance import hash_file
from src.contracts import StageBenchmarkRecord, StageStatus, WorkflowRunRecord

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "docs/CORRECTED_VIEW_RULES.md"
DIAGNOSTICS = REPO / "results/processed/diagnostics_posthoc.json"
OUT = REPO / "results/processed/corrected_view.json"
REPORT = REPO / "results/reports/corrected_view.md"

GROUPS = {
    "original_4096": {
        "part_a": REPO / "results/raw/stage_benchmark/expA_stage_v3.jsonl",
        "part_b": REPO / "results/raw/workflow_runs/expB_paths_v3.jsonl",
        "v31_a": REPO / "results/processed/v3_1_rescore/expA_stage_v3_reporting.json",
        "v31_b": REPO / "results/processed/v3_1_rescore/expB_paths_v3_reporting.json",
    },
    "price_matched_16384": {
        "part_a": REPO / "results/raw/stage_benchmark/expA_price_matched_workflow_v3.jsonl",
        "part_b": REPO / "results/raw/workflow_runs/expB_price_matched_workflow_v3.jsonl",
        "v31_a": REPO / "results/processed/v3_1_rescore/expA_price_matched_workflow_v3_reporting.json",
        "v31_b": REPO / "results/processed/v3_1_rescore/expB_price_matched_workflow_v3_reporting.json",
    },
}

REPORT_NAMES = {
    "original_4096": {"A": "Sonnet 4.6", "B": "Nova Pro", "C": "gpt-oss-120b"},
    "price_matched_16384": {"A": "Sonnet 4.6", "B": "Kimi K3", "C": "GLM 5"},
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_records(group: str):
    cfg = GROUPS[group]
    part_a = [StageBenchmarkRecord.model_validate(row) for row in read_jsonl(cfg["part_a"])]
    raw_b = [WorkflowRunRecord.model_validate(row) for row in read_jsonl(cfg["part_b"])]
    if group == "price_matched_16384":
        part_b, audit = resolve_workflow_reruns(raw_b)
    else:
        part_b, audit = raw_b, {"raw_records": len(raw_b), "effective_records": len(raw_b),
                                "replacements": []}
    return part_a, raw_b, part_b, audit


def opportunities(group: str):
    part_a, _, part_b, _ = load_records(group)
    for row in part_a:
        yield {"part": "part_a", "run_id": row.run_id, "project_id": row.project_id,
               "stage": row.stage.value, "alias": row.model_alias, "record": row.record}
    for run in part_b:
        for stage in run.stages:
            yield {"part": "part_b", "run_id": run.run_id, "project_id": run.project_id,
                   "stage": stage.stage.value, "alias": stage.model_alias, "record": stage}


def evidence():
    diagnostics = json.loads(DIAGNOSTICS.read_text())
    replay = {}
    for row in diagnostics["serialization_replay"]["records"]:
        if row["would_pass_without_serialization_bug"]:
            part = "part_a" if row["part"] == "A" else "part_b"
            replay[(row["group"], part, row["run_id"], row["stage"])] = row
    rounding = {(row["group"], "part_a" if row["part"] == "A" else "part_b", row["run_id"]): row
                for row in diagnostics["rounding_sensitivity"]["derived_values_only_candidates"]
                if row["recoverable"]}
    q7 = {(row["group"], "part_a" if row["part"] == "A" else "part_b", row["run_id"]): row
          for row in diagnostics["rounding_sensitivity"]["known_q7_v31_false_rejects"]}
    if len(rounding) != 15 or len(q7) != 30 or set(rounding) & set(q7):
        raise ValueError("rounding/q7 evidence count or disjointness differs from committed rules")
    v31 = {}
    for group, cfg in GROUPS.items():
        for part, path in (("part_a", cfg["v31_a"]), ("part_b", cfg["v31_b"])):
            for row in json.loads(path.read_text())["records"]:
                key = (group, part, row["run_id"])
                v31[key] = bool(row["v31_ground_truth"]["hard_pass"])
    if any(v31.get(key, False) for key in rounding):
        raise ValueError("a rounding recovery overlaps a v3.1 pass; unique attribution is not disjoint")
    if any(not v31.get(key, False) for key in q7):
        raise ValueError("known q7 false reject is not recovered by saved v3.1 evidence")
    return replay, rounding, q7, v31


def _view(passed: int, denominator: int, unique_additions: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"passed": passed, "rate": passed / denominator if denominator else None}
    if unique_additions is not None:
        value["unique_additions"] = unique_additions
    return value


def analyze() -> dict[str, Any]:
    replay, rounding, q7, v31 = evidence()
    buckets: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    rerun_audits = {}
    evidence_usage = Counter()
    for group in GROUPS:
        _, raw_b, part_b, audit = load_records(group)
        rerun_audits[group] = {"raw_records": len(raw_b), "effective_records": len(part_b),
                               "replacements": len(audit.get("replacements", []))}
        for row in opportunities(group):
            record = row["record"]
            frozen = record.status == StageStatus.PASSED
            replay_key = (group, row["part"], row["run_id"], row["stage"])
            report_key = (group, row["part"], row["run_id"])
            int64_add = not frozen and replay_key in replay
            if int64_add and "Object of type int64 is not JSON serializable" not in str(record.failure_detail):
                raise ValueError(f"int64 replay does not match frozen failure {row['run_id']}:{row['stage']}")
            rounding_add = not frozen and row["stage"] == "reporting" and report_key in rounding
            v31_pass = (v31.get(report_key, frozen) if row["stage"] == "reporting" else frozen)
            if frozen:
                attribution = "frozen_pass"
            elif int64_add:
                attribution = "int64_recovered"
            elif rounding_add:
                attribution = "rounding_recovered"
            elif v31_pass:
                attribution = "v3_1_recovered"
            else:
                attribution = "not_recovered"
            evidence_usage[attribution] += 1
            buckets[(group, row["part"], row["stage"], row["alias"])].append({
                "frozen": frozen,
                "int64": frozen or int64_add,
                "rounding": frozen or rounding_add,
                "v31": v31_pass,
                "combined": attribution != "not_recovered",
                "attribution": attribution,
                "void_infra": record.status == StageStatus.INFRA_ERROR,
            })

    output_groups: dict[str, Any] = {}
    for group in GROUPS:
        parts = {}
        for part in ("part_a", "part_b"):
            stages = {}
            for stage in ("cleaning", "analysis", "reporting"):
                models = {}
                for alias in "ABC":
                    rows = buckets[(group, part, stage, alias)]
                    denominator = len(rows)
                    attribution_counts = Counter(row["attribution"] for row in rows)
                    if sum(attribution_counts.values()) != denominator:
                        raise AssertionError("attribution counts do not sum to denominator")
                    models[alias] = {
                        "denominator": denominator,
                        "frozen": _view(sum(r["frozen"] for r in rows), denominator),
                        "int64_recovered": _view(sum(r["int64"] for r in rows), denominator,
                                                  attribution_counts["int64_recovered"]),
                        "rounding_recovered": _view(sum(r["rounding"] for r in rows), denominator,
                                                     attribution_counts["rounding_recovered"]),
                        "v3_1": _view(sum(r["v31"] for r in rows), denominator,
                                      attribution_counts["v3_1_recovered"]),
                        "combined": _view(sum(r["combined"] for r in rows), denominator),
                        "attribution_counts": {name: attribution_counts[name] for name in
                                               ("frozen_pass", "int64_recovered", "rounding_recovered",
                                                "v3_1_recovered", "not_recovered")},
                        "void_infra": sum(r["void_infra"] for r in rows),
                    }
                stages[stage] = {"models": models}
            parts[part] = {"stages": stages}
        output_groups[group] = {"parts": parts}

    source_paths = [RULES, DIAGNOSTICS, *[cfg[key] for cfg in GROUPS.values()
                                        for key in ("part_a", "part_b", "v31_a", "v31_b")]]
    return {
        "label": "post-hoc / sensitivity; frozen stage results remain authoritative",
        "scope": "stage-level Part A and effective-cell Part B only; no corrected Part B feasibility",
        "source_hashes": {str(path.relative_to(REPO)): hash_file(path) for path in source_paths},
        "assertions": {
            "rounding_recoveries": len(rounding), "q7_v3_1_recoveries": len(q7),
            "rounding_q7_disjoint": True,
            "attribution_precedence": ["frozen_pass", "int64_recovered", "rounding_recovered",
                                       "v3_1_recovered", "not_recovered"],
            "effective_part_b": rerun_audits,
            "total_attribution_counts": {name: evidence_usage[name] for name in
                                         ("frozen_pass", "int64_recovered", "rounding_recovered",
                                          "v3_1_recovered", "not_recovered")},
            "corrected_part_b_feasibility_computed": False,
        },
        "model_groups": output_groups,
    }


def _pct(passed: int, n: int) -> str:
    return f"{passed}/{n} ({100 * passed / n:.1f}%)" if n else "0/0 (n/a)"


def _table(result: dict[str, Any], group: str, part: str) -> list[str]:
    lines = ["| Stage | Model | Frozen | int64 view | Rounding view | v3.1 view | Combined |",
             "|---|---|---:|---:|---:|---:|---:|"]
    for stage in ("cleaning", "analysis", "reporting"):
        models = result["model_groups"][group]["parts"][part]["stages"][stage]["models"]
        for alias in "ABC":
            row = models[alias]
            n = row["denominator"]
            lines.append(
                f"| {stage} | {REPORT_NAMES[group][alias]} (`{alias}`) | "
                f"{_pct(row['frozen']['passed'], n)} | {_pct(row['int64_recovered']['passed'], n)} | "
                f"{_pct(row['rounding_recovered']['passed'], n)} | {_pct(row['v3_1']['passed'], n)} | "
                f"{_pct(row['combined']['passed'], n)} |"
            )
    return lines


def render_report(result: dict[str, Any]) -> str:
    groups = result["model_groups"]
    price_a_analysis = groups["price_matched_16384"]["parts"]["part_a"]["stages"]["analysis"]["models"]["C"]
    orig_b_analysis = groups["original_4096"]["parts"]["part_b"]["stages"]["analysis"]["models"]
    price_b_analysis = groups["price_matched_16384"]["parts"]["part_b"]["stages"]["analysis"]["models"]["C"]
    totals = result["assertions"]["total_attribution_counts"]
    lines = [
        "# Corrected Stage-Level View",
        "",
        "**POST-HOC / SENSITIVITY. Frozen v3 results remain authoritative. This report does not compute corrected Part B workflow feasibility.**",
        "",
        "## Key Findings",
        "",
        f"- GLM 5 Part A analysis changes from **{_pct(price_a_analysis['frozen']['passed'], price_a_analysis['denominator'])}** frozen to **{_pct(price_a_analysis['combined']['passed'], price_a_analysis['denominator'])}** combined because all four saved failures were serialization-only and passed the frozen validator after replay.",
        f"- Across both groups and both parts, the combined stage view adds **{totals['int64_recovered']}** int64 recoveries, **{totals['rounding_recovered']}** stated-precision recoveries, and **{totals['v3_1_recovered']}** separate v3.1 recoveries. The attribution sets are mutually exclusive.",
        f"- In original-group Part B analysis, Nova Pro gains **{orig_b_analysis['B']['int64_recovered']['unique_additions']}** and gpt-oss-120b gains **{orig_b_analysis['C']['int64_recovered']['unique_additions']}** stage passes in the int64 view; no blocked reporting stage is imputed here.",
        f"- In price-matched Part B analysis, GLM 5 changes from **{_pct(price_b_analysis['frozen']['passed'], price_b_analysis['denominator'])}** frozen to **{_pct(price_b_analysis['combined']['passed'], price_b_analysis['denominator'])}** combined. This is a stage-level artifact sensitivity, not a revised end-to-end result.",
        f"- The reporting corrections remain distinct: **{result['assertions']['rounding_recoveries']}** reports are recovered by literal stated precision and **{result['assertions']['q7_v3_1_recoveries']}** by v3.1's q7 fix; no record is counted in both.",
        "",
        "## Scope and Method",
        "",
        "Every row keeps one fixed denominator and shows frozen v3, int64-only, stated-precision-only, v3.1, and combined views side by side. Part B uses all effective stage opportunities after resolving the five append-only Docker reruns; blocked and not-run stages stay in the denominator. Corrections change only the stage with saved evidence. The processed JSON contains aliases only; names are rendered here from the group-specific registries.",
        "",
        "Source: `results/processed/corrected_view.json` fields `model_groups`, `assertions`, and `source_hashes`.",
        "",
        "## Part A",
        "",
        "### Original model group (maxTokens 4096)", "",
        *_table(result, "original_4096", "part_a"), "",
        "### Price-matched model group (maxTokens 16384)", "",
        *_table(result, "price_matched_16384", "part_a"), "",
        "## Part B Stage Pass Rates", "",
        "These are stage pass rates, not corrected workflow feasibility. A recovered upstream stage does not create a downstream result.", "",
        "### Original model group (maxTokens 4096)", "",
        *_table(result, "original_4096", "part_b"), "",
        "### Price-matched model group (maxTokens 16384)", "",
        *_table(result, "price_matched_16384", "part_b"), "",
        "## Attribution Audit", "",
        f"The correction flow across all **{sum(totals.values())}** stage opportunities is: frozen pass {totals['frozen_pass']}; unique int64 addition {totals['int64_recovered']}; unique stated-precision addition {totals['rounding_recovered']}; unique v3.1 addition {totals['v3_1_recovered']}; not recovered {totals['not_recovered']}. The counts sum to the fixed denominators. The 15 rounding and 30 q7/v3.1 run-ID sets are disjoint.", "",
        "## Limitations and Reproduction", "",
        "This additive view diagnoses scorer/environment artifacts; it does not erase model errors, infer missing calls, or replace frozen conclusions. The exact corrected Part B view waits for all 40 approved continuation records. The 11 recovered cleaning cases whose downstream stages already ran will later use those observed outcomes with an explicit disclosure that their handoffs saw upstream status `failed`.", "",
        "```bash", ".venv/bin/python -m experiments.analyze_corrected_view", "```", "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args(argv)
    result = analyze()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.report.write_text(render_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
