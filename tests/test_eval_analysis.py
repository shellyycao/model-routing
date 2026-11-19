"""Analysis validator: reference solutions pass; broken analyses fail for the right reason."""

import importlib.util
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from datasets.generate import PROJECTS_DIR
from src.contracts import QUALITY_METRICS, StageId
from src.evaluation.analysis import conditional_reference_metrics, validate_analysis

PDIR = PROJECTS_DIR / "retail_sales"
SOLUTIONS = Path(__file__).parent / "fixtures" / "benchmark" / "solutions"
CANON = json.loads((PDIR / "canonical" / "findings.json").read_text())


def _analyze(bug=None, cleaned=PDIR / "canonical" / "cleaned.csv"):
    spec = importlib.util.spec_from_file_location("retail_sales_analysis", SOLUTIONS / "retail_sales_analysis.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.analyze(pd.read_csv(cleaned), bug)


def _failed(res):
    return {c.name for c in res.checks if c.mandatory and not c.passed}


def _detail(res, name):
    return next(c.detail for c in res.checks if c.name == name)


def test_canonical_findings_pass_without_reproducibility():
    res = validate_analysis(PDIR / "canonical" / "findings.json", PDIR)
    assert res.stage == StageId.ANALYSIS and res.hard_pass
    assert res.quality == {"numerical_accuracy": 1.0, "calculation_coverage": 1.0}
    assert "reproducibility" not in res.quality          # not faked without a second execution


def test_independent_solution_passes_and_reproducibility_from_two_runs():
    a, b = _analyze(), _analyze()
    res = validate_analysis(a, PDIR, second_findings=b)
    assert res.hard_pass
    assert set(res.quality) == set(QUALITY_METRICS[StageId.ANALYSIS])
    assert res.quality["reproducibility"] == 1.0


def test_non_reproducible_runs_lower_reproducibility_only():
    a = _analyze()
    b = dict(a, total_revenue=a["total_revenue"] + 100)
    res = validate_analysis(a, PDIR, second_findings=b)
    assert res.hard_pass                                   # reproducibility is a quality metric, not a gate
    assert res.quality["reproducibility"] == pytest.approx((len(CANON) - 1) / len(CANON))


@pytest.mark.parametrize("bug,bad_key", [
    ("region_mean_not_sum", "revenue_north"),          # wrong aggregation
    ("population_std", "order_revenue_std"),           # wrong statistic
    ("yoy_wrong_base", "revenue_yoy_change_pct"),      # wrong percentage change
    ("discount_gt_not_ge", "electronics_high_discount_orders"),  # wrong filter boundary
])
def test_wrong_calculations_fail_values(bug, bad_key):
    res = validate_analysis(_analyze(bug), PDIR)
    assert _failed(res) == {"values_within_tolerance"}
    assert bad_key in _detail(res, "values_within_tolerance")
    assert res.quality["numerical_accuracy"] < 1.0 and res.quality["calculation_coverage"] == 1.0


def test_missing_metric_fails_presence():
    res = validate_analysis(_analyze("missing_std"), PDIR)
    assert {"required_keys_present", "values_within_tolerance"} <= _failed(res)
    assert "order_revenue_std" in _detail(res, "required_keys_present")
    assert res.quality["calculation_coverage"] == pytest.approx((len(CANON) - 1) / len(CANON))


def test_non_numeric_and_bad_files(tmp_path):
    res = validate_analysis(dict(CANON, order_count="520"), PDIR)
    assert "values_numeric" in _failed(res)
    assert not validate_analysis(tmp_path / "none.json", PDIR).hard_pass
    p = tmp_path / "f.json"
    p.write_text("{not json")
    assert "findings_parses" in _failed(validate_analysis(p, PDIR))
    p.write_text("[1, 2]")
    assert "findings_parses" in _failed(validate_analysis(p, PDIR))
    p.write_text(json.dumps({"metrics": CANON}))           # nested is not the agreed format
    assert "required_keys_present" in _failed(validate_analysis(p, PDIR))


def test_within_tolerance_accepted():
    res = validate_analysis(dict(CANON, total_revenue=CANON["total_revenue"] + 0.009), PDIR)
    assert res.hard_pass


def test_conditional_reference_separates_upstream_error(tmp_path):
    """Analysis done correctly on WRONG upstream cleaned data: fails vs ground truth, passes vs the
    trusted reference recomputed on that same upstream file."""
    clean_spec = importlib.util.spec_from_file_location("c", SOLUTIONS / "retail_sales_clean.py")
    cmod = importlib.util.module_from_spec(clean_spec)
    clean_spec.loader.exec_module(cmod)
    bad = cmod.clean(pd.read_csv(PDIR / "raw.csv", dtype=str, keep_default_na=False), "no_category_synonyms")
    up = tmp_path / "cleaned.csv"
    bad.to_csv(up, index=False, float_format="%.2f")
    findings = _analyze(cleaned=up)
    assert not validate_analysis(findings, PDIR).hard_pass
    ref = conditional_reference_metrics(PDIR, up)
    res = validate_analysis(findings, PDIR, reference_metrics=ref)
    assert res.hard_pass
    if "quality_basis" in type(res).model_fields:          # contracts >= 1.1
        assert res.quality_basis == "conditional_reference"
        assert validate_analysis(findings, PDIR).quality_basis == "ground_truth"


def test_conditional_reference_unavailable_for_broken_upstream(tmp_path):
    p = tmp_path / "cleaned.csv"
    p.write_text("x,y\n1,2\n")
    assert conditional_reference_metrics(PDIR, p) is None
