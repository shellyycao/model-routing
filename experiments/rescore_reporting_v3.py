"""Offline side-by-side v2/v3 rescoring of saved reporting outputs. No model client is imported."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from src.bedrock.provenance import hash_file
from src.contracts import StageId, WorkflowRunRecord
from src.evaluation.cleaning import load_project
from src.evaluation.reporting_v3 import validate_reporting_v3
from src.workflow.orchestrator import PROJECTS_DIR


def rescore(records_path: Path, results_root: Path, project_id: str, project_dir: Path) -> dict:
    spec, ground_truth, _ = load_project(project_dir)
    records = [WorkflowRunRecord.model_validate_json(line) for line in records_path.read_text().splitlines()
               if line.strip()]
    rows = []
    for record in records:
        if record.project_id != project_id or len(record.models) != 3:
            continue
        reporting = next((stage for stage in record.stages if stage.stage == StageId.REPORTING), None)
        report_path = results_root / "runs" / record.run_id / "reporting" / "output" / "report.json"
        findings_path = results_root / "runs" / record.run_id / "analysis" / "output" / spec.findings_filename
        if reporting is None or reporting.validation is None or not report_path.is_file():
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        v3_ground = validate_reporting_v3(
            report, ground_truth["analysis"]["metrics"], spec, quality_basis="ground_truth",
            cleaning_counts=ground_truth["cleaning"]["rule_log"])
        upstream = json.loads(findings_path.read_text(encoding="utf-8")) if findings_path.is_file() else None
        v3_conditional = (validate_reporting_v3(
            report, upstream, spec, quality_basis="conditional_reference") if isinstance(upstream, dict) else None)
        rows.append({
            "run_id": record.run_id,
            "path_id": record.path_id,
            "report_sha256": hash_file(report_path),
            "findings_sha256": hash_file(findings_path) if findings_path.is_file() else None,
            "v2_ground_truth": reporting.validation.model_dump(mode="json"),
            "v3_ground_truth": v3_ground.model_dump(mode="json"),
            "v2_conditional": (reporting.conditional_validation.model_dump(mode="json")
                               if reporting.conditional_validation else None),
            "v3_conditional": v3_conditional.model_dump(mode="json") if v3_conditional else None,
        })
    transition = Counter((row["v2_ground_truth"]["hard_pass"], row["v3_ground_truth"]["hard_pass"])
                         for row in rows)
    return {
        "mode": "offline_saved_output_rescore",
        "project_id": project_id,
        "source_records": str(records_path),
        "source_records_sha256": hash_file(records_path),
        "project_spec_sha256": hash_file(project_dir / "project.json"),
        "ground_truth_sha256": hash_file(project_dir / "ground_truth.json"),
        "raw_outputs_modified": False,
        "v2_validator": "2.0",
        "v3_validator": "3.0-post-freeze",
        "comparability_warning": (
            "V3 is a post-freeze secondary analysis. It must not replace or be pooled with frozen v2 scores."),
        "summary": {
            "reports_rescored": len(rows),
            "v2_ground_truth_passed": sum(row["v2_ground_truth"]["hard_pass"] for row in rows),
            "v3_ground_truth_passed": sum(row["v3_ground_truth"]["hard_pass"] for row in rows),
            "transitions": {f"v2_{old}_to_v3_{new}": count for (old, new), count in sorted(transition.items())},
        },
        "records": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="retail_sales")
    parser.add_argument("--records", type=Path, default=Path("results/raw/workflow_runs/expB_paths.jsonl"))
    parser.add_argument("--results-root", type=Path, default=Path("results/raw"))
    parser.add_argument("--out", type=Path,
                        default=Path("results/processed/pilot_v3_rescore/retail_sales_reporting.json"))
    args = parser.parse_args(argv)
    payload = rescore(args.records, args.results_root, args.project, PROJECTS_DIR / args.project)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
