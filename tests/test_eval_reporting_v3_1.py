"""Regression tests for the POST-HOC reporting validator v3.1 (comparative-clause false reject)."""
import copy
import json
from pathlib import Path

import pytest

from src.contracts import ProjectSpec
from src.evaluation.reporting_v3 import validate_reporting_v3
from src.evaluation.reporting_v3_1 import VALIDATOR_VERSION, validate_reporting_v3_1

REPO = Path(__file__).resolve().parents[1]
P = REPO / "datasets/projects/customer_churn"
SPEC = ProjectSpec.model_validate_json((P / "project.json").read_text())
GT = json.loads((P / "ground_truth.json").read_text())
REPORT = json.loads((REPO / "tests/fixtures/reporting_v3_1/churn_claude_report.json").read_text())
REPORT.pop("_provenance")


def _with_q7(statement):
    rep = copy.deepcopy(REPORT)
    for f in rep["key_findings"]:
        if f["finding_id"] == "q7":
            f["statement"] = statement
    return rep


def _run(rep):
    kw = dict(cleaning_counts=GT["cleaning"]["rule_log"])
    return (validate_reporting_v3(rep, GT["analysis"]["metrics"], SPEC, **kw),
            validate_reporting_v3_1(rep, GT["analysis"]["metrics"], SPEC, **kw))


def test_comparative_clause_false_reject_is_cleared():
    v3, v31 = _run(REPORT)                      # real Phase 1 report: "Premium LTV is 292.0% higher than Basic"
    assert not v3.hard_pass and v31.hard_pass
    assert v31.validator_version == VALIDATOR_VERSION
    check = next(c for c in v31.checks if c.name == "prose_claims_consistent")
    assert check.passed and "v3.1 cleared" in check.detail


@pytest.mark.parametrize("statement", [
    "Basic LTV is $1,816.78, Standard $868.83 and Premium $463.46.",   # swapped values, no comparative
    "Premium LTV is 150.0% higher than Basic.",                        # comparative but wrong number
    "Premium LTV is $463.46.",                                         # another key's value, plain attribution
])
def test_genuine_errors_still_fail(statement):
    v3, v31 = _run(_with_q7(statement))
    assert not v31.hard_pass, [c.detail for c in v31.checks if not c.passed]


def test_v31_never_fails_what_v3_passes():
    v3, v31 = _run(_with_q7("Premium customers have the highest lifetime value at $1,816.78, 292.0% above Basic ($463.46)."))
    assert v31.hard_pass or not v3.hard_pass
