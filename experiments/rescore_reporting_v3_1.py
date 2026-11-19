"""POST-HOC rescore of saved reports with reporting validator v3.1 (offline; no model client).

For every reporting stage in a record file (Experiment A StageBenchmarkRecord or Experiment B
WorkflowRunRecord), recompute v3 (must equal the stored record) and v3.1, on the ground-truth basis
and the conditional basis (the actual upstream findings the report was given). Source files are
hashed; nothing under results/raw is modified. Output feeds src/analysis reporting_scores.

Usage: .venv/bin/python -m experiments.rescore_reporting_v3_1 --records results/raw/stage_benchmark/expA_stage_v3.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from src.contracts import ProjectSpec
from src.evaluation.reporting_v3 import validate_reporting_v3
from src.evaluation.reporting_v3_1 import VALIDATOR_VERSION, validate_reporting_v3_1

REPO = Path(__file__).resolve().parents[1]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _reporting_stage(d: dict) -> tuple[dict | None, str | None]:
    if "record" in d:                                   # StageBenchmarkRecord
        return (d["record"], None) if d["stage"] == "reporting" else (None, None)
    for s in d.get("stages", []):                        # WorkflowRunRecord
        if s["stage"] == "reporting":
            return s, d.get("path_id")
    return None, None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--out-dir", default="results/processed/v3_1_rescore")
    args = ap.parse_args(argv)
    src = REPO / args.records
    lines = [json.loads(l) for l in src.read_text().splitlines() if l.strip()]
    experiment = lines[0]["experiment_id"]
    if not experiment.endswith("_v3"):
        raise SystemExit("v3.1 rescores only v3 experiments (v3.1 is a post-hoc variant of v3)")
    out_records, summary = [], {"reports_rescored": 0, "v3_ground_truth_passed": 0, "v31_ground_truth_passed": 0,
                                "v3_conditional_passed": 0, "v31_conditional_passed": 0, "transitions": {},
                                "skipped_no_report": 0}
    cache: dict[str, tuple] = {}
    for d in lines:
        st, path_id = _reporting_stage(d)
        if st is None:
            continue
        rep_p = next((REPO / p for p in st.get("output_artifacts", []) if p.endswith("report.json")), None)
        if rep_p is None or not rep_p.exists():
            summary["skipped_no_report"] += 1
            continue
        pid = d["project_id"]
        if pid not in cache:
            pdir = REPO / "datasets/projects" / pid
            cache[pid] = (ProjectSpec.model_validate_json((pdir / "project.json").read_text()),
                          json.loads((pdir / "ground_truth.json").read_text()))
        spec, gt = cache[pid]
        report = json.loads(rep_p.read_text())
        kw = dict(cleaning_counts=gt["cleaning"]["rule_log"])
        v3_gt = validate_reporting_v3(report, gt["analysis"]["metrics"], spec, quality_basis="ground_truth", **kw)
        stored = (st.get("validation") or {}).get("hard_pass")
        if stored is not None and stored != v3_gt.hard_pass:
            raise SystemExit(f"v3 recompute disagrees with stored record for {d['run_id']}; refusing")
        v31_gt = validate_reporting_v3_1(report, gt["analysis"]["metrics"], spec, quality_basis="ground_truth", **kw)
        fin_p = next((REPO / p for p in st.get("input_artifacts", []) if p.endswith("findings.json")), None)
        cond = {}
        if fin_p is not None and fin_p.exists():
            upstream = json.loads(fin_p.read_text())
            cond = {"v3_conditional": validate_reporting_v3(report, upstream, spec, quality_basis="conditional_reference"),
                    "v31_conditional": validate_reporting_v3_1(report, upstream, spec, quality_basis="conditional_reference")}
        rec = {"run_id": d["run_id"], "project_id": pid, "path_id": path_id, "model_alias": st["model_alias"],
               "report_sha256": sha(rep_p), "findings_sha256": sha(fin_p) if fin_p and fin_p.exists() else None,
               "v3_ground_truth": v3_gt.model_dump(mode="json"), "v31_ground_truth": v31_gt.model_dump(mode="json")}
        rec.update({k: v.model_dump(mode="json") for k, v in cond.items()})
        out_records.append(rec)
        summary["reports_rescored"] += 1
        summary["v3_ground_truth_passed"] += v3_gt.hard_pass
        summary["v31_ground_truth_passed"] += v31_gt.hard_pass
        if cond:
            summary["v3_conditional_passed"] += cond["v3_conditional"].hard_pass
            summary["v31_conditional_passed"] += cond["v31_conditional"].hard_pass
        t = f"v3_{v3_gt.hard_pass}_to_v31_{v31_gt.hard_pass}"
        summary["transitions"][t] = summary["transitions"].get(t, 0) + 1
    out = {"mode": "offline_saved_output_rescore", "experiment_id": experiment,
           "source_records": str(src.relative_to(REPO)), "source_records_sha256": sha(src),
           "raw_outputs_modified": False, "v3_validator": "3.0-post-freeze", "v31_validator": VALIDATOR_VERSION,
           "comparability_warning": "v3.1 is a POST-HOC secondary analysis. Report it beside v3; never replace "
                                    "or pool with v3 (primary) scores.",
           "summary": summary, "records": out_records}
    dest = REPO / args.out_dir / f"{experiment}_reporting.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"wrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
