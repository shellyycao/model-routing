"""Post-freeze v3 reporting tests. Frozen v2 behavior is asserted side by side."""

import json
from pathlib import Path

from datasets.generate import PROJECTS_DIR
from src.contracts import ProjectSpec, ReportOutput
from src.evaluation.reporting import validate_reporting
from src.evaluation.reporting_v3 import validate_reporting_v3

PDIR = PROJECTS_DIR / "retail_sales"
SPEC = ProjectSpec.model_validate_json((PDIR / "project.json").read_text())
FINDINGS = json.loads((PDIR / "canonical" / "findings.json").read_text())
RAW = Path("results/raw/runs")


def _report(run_id: str) -> ReportOutput:
    return ReportOutput.model_validate_json((RAW / run_id / "reporting/output/report.json").read_text())


def _check(result, name):
    return next(check for check in result.checks if check.name == name)


def test_v3_recovers_semantics_but_records_missing_explicit_ranking():
    report = _report("expB_paths-4308de5346884de6")  # A-A-A: correct q2, omitted q3 ranking
    assert not validate_reporting(report, FINDINGS, SPEC).hard_pass
    result = validate_reporting_v3(report, FINDINGS, SPEC)
    assert result.hard_pass and result.validator_version == "3.0-post-freeze"
    assert _check(result, "rankings_correct").passed
    assert not _check(result, "rankings_explicit").passed


def test_v3_accepts_correct_metric_key_ranking_aliases():
    report = _report("expB_paths-0e2648bdbd06cdef")  # A-A-B
    assert not validate_reporting(report, FINDINGS, SPEC).hard_pass
    result = validate_reporting_v3(report, FINDINGS, SPEC)
    assert result.hard_pass and _check(result, "rankings_correct").passed


def test_v3_still_rejects_wrong_explicit_order():
    report = _report("expB_paths-16296ffeb287a694")  # A-B-B: East, West, North, South
    result = validate_reporting_v3(report, FINDINGS, SPEC)
    assert not result.hard_pass and not _check(result, "rankings_correct").passed


def test_v3_does_not_hide_nonranking_factual_failures():
    report = _report("expB_paths-9752d7ddbebd5874")  # C-B-A propagated wrong values
    result = validate_reporting_v3(report, FINDINGS, SPEC)
    assert not result.hard_pass
    failed = {check.name for check in result.checks if check.mandatory and not check.passed}
    assert {"reported_values_consistent", "derived_values_correct"} <= failed
