"""Benchmark projects: spec validity, byte reproducibility, documented imperfections, and an
independent cross-check of the ground truth (pandas follower vs pure-Python reference)."""

import csv
import importlib.util
import json
import re
from pathlib import Path

import pandas as pd
import pytest

from datasets.generate import FILES, PROJECTS_DIR, REGISTRY, build_project, check_reproducible, project_files
from src.contracts import ProjectSpec

SOLUTIONS = Path(__file__).parent / "fixtures" / "benchmark" / "solutions"
PROJECTS = list(REGISTRY)


def load_solution(name: str):
    spec = importlib.util.spec_from_file_location(name, SOLUTIONS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("pid", PROJECTS)
def test_project_files_exist_and_spec_validates(pid):
    pdir = PROJECTS_DIR / pid
    for f in project_files(pid):
        assert (pdir / f).is_file(), f
    spec = ProjectSpec.model_validate_json((pdir / "project.json").read_text())
    assert spec.project_id == pid
    keys = [k for q in spec.analysis_questions for k in q.metric_keys]
    assert len(keys) == len(set(keys))
    findings = json.loads((pdir / spec.canonical_findings_file).read_text())
    assert sorted(findings) == sorted(keys)
    assert set(spec.reporting.required_finding_ids) <= {q.question_id for q in spec.analysis_questions}
    gt = json.loads((pdir / spec.ground_truth_file).read_text())
    assert gt["label"] == "SYNTHETIC" and gt["seed"] == spec.seed
    assert gt["analysis"]["metrics"] == findings


@pytest.mark.parametrize("pid", PROJECTS)
def test_committed_files_are_byte_reproducible_from_seed(pid):
    assert check_reproducible(pid) == []


@pytest.mark.parametrize("pid", PROJECTS)
def test_two_fresh_builds_identical(pid, tmp_path):
    a = build_project(pid, tmp_path / "a")
    b = build_project(pid, tmp_path / "b")
    for f in project_files(pid):
        assert (a / f).read_bytes() == (b / f).read_bytes(), f


def test_retail_raw_has_each_documented_imperfection():
    pdir = PROJECTS_DIR / "retail_sales"
    with open(pdir / "raw.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    ids = [r["order_id"] for r in rows]
    assert len(ids) - len(set(ids)) > 0                                     # duplicates
    fmts = {
        "iso": r"^\d{4}-\d{2}-\d{2}$", "us": r"^\d{2}/\d{2}/\d{4}$", "dmy": r"^\d{2}-[A-Za-z]{3}-\d{4}$",
        "ymd": r"^\d{4}/\d{2}/\d{2}$", "long": r"^[A-Za-z]+ \d{1,2}, \d{4}$"}
    for name, pat in fmts.items():                                          # inconsistent dates
        assert any(re.match(pat, r["order_date"]) for r in rows), name
    missing = {"", "NA", "N/A", "null", "None", "-"}
    assert sum(r["unit_price"] in missing for r in rows) > 0                # missing values
    assert sum(r["region"] in missing for r in rows) > 0
    assert any("$" in r["unit_price"] for r in rows)                        # numbers as strings
    assert any("," in r["unit_price"] for r in rows)
    assert any(r["unit_price"] == "TBD" for r in rows)
    assert any(r["quantity"].endswith(".0") for r in rows)
    assert any(r["discount_pct"].endswith("%") for r in rows)
    regions = {r["region"] for r in rows}
    assert {"north", "NORTH", "N"} & regions and any(r != r.strip() for r in regions)   # case/spelling
    assert {"Home And Garden", "Home&Garden", "Electronic", "Apparel"} & {r["product_category"] for r in rows}
    q = [float(r["quantity"]) for r in rows]
    assert min(q) <= 0 and max(q) > 50                                      # invalid numerics
    assert any(r["unit_price"].lstrip("$USD ").startswith("-") for r in rows)


def test_retail_rule_log_reconciles_with_injection_log():
    gt = json.loads((PROJECTS_DIR / "retail_sales" / "ground_truth.json").read_text())
    log, inj = gt["cleaning"]["rule_log"], gt["generation"]["injected"]
    assert log["R2_duplicates_removed"] == inj["duplicate_rows_exact"] + inj["duplicate_rows_changed_value"]
    assert log["dropped_R3_date"] == inj["missing_date"]
    assert log["dropped_R4_region"] == inj["missing_region"]
    assert log["dropped_R5_category"] == inj["unknown_category"]
    assert log["dropped_R6_unit_price"] == inj["missing_price"] + inj["unparseable_price"] + inj["negative_price"]
    assert log["dropped_R7_quantity"] == inj["nonpositive_or_too_large_quantity"] + inj["fractional_quantity"]
    # some out-of-range discounts were later overwritten by a missing-discount injection (-> 0, kept)
    assert 0 < log["dropped_R8_discount"] <= inj["discount_out_of_range"]
    dropped = sum(v for k, v in log.items() if k.startswith("dropped_"))
    assert log["raw_rows"] - log["R2_duplicates_removed"] - dropped == log["cleaned_rows"] == gt["cleaning"]["expected_row_count"]


def test_retail_ground_truth_matches_independent_pandas_analysis():
    """Independent implementation (pandas) of the analysis questions agrees with the reference."""
    pdir = PROJECTS_DIR / "retail_sales"
    spec = ProjectSpec.model_validate_json((pdir / "project.json").read_text())
    ref = json.loads((pdir / spec.canonical_findings_file).read_text())
    ind = load_solution("retail_sales_analysis").analyze(pd.read_csv(pdir / spec.canonical_cleaned_file))
    for q in spec.analysis_questions:
        for k in q.metric_keys:
            assert abs(ind[k] - ref[k]) <= max(q.abs_tolerance, q.rel_tolerance * abs(ref[k])), k


def test_retail_cleaning_rules_are_followable_by_independent_implementation():
    """A pandas script written only from the NL rules reproduces the canonical rows exactly
    (values agree within the cleaning tolerance; half-cent float rounding may differ)."""
    pdir = PROJECTS_DIR / "retail_sales"
    raw = pd.read_csv(pdir / "raw.csv", dtype=str, keep_default_na=False)
    ind = load_solution("retail_sales_clean").clean(raw)
    ref = pd.read_csv(pdir / "canonical" / "cleaned.csv", dtype={"order_id": str})
    assert list(ind.columns) == list(ref.columns)
    assert ind["order_id"].tolist() == ref["order_id"].tolist()
    for c in ["order_date", "customer_id", "region", "product_category"]:
        assert ind[c].tolist() == ref[c].tolist(), c
    for c in ["quantity", "unit_price", "discount_pct", "revenue"]:
        assert (ind[c].astype(float) - ref[c]).abs().max() <= 0.011 + 1e-9, c


@pytest.mark.parametrize("pid", PROJECTS)
def test_duplicate_copies_include_a_different_value(pid):
    """Keep-first deduplication is observable, not a no-op over identical copies."""
    pdir = PROJECTS_DIR / pid
    spec = ProjectSpec.model_validate_json((pdir / "project.json").read_text())
    key = json.loads((pdir / "ground_truth.json").read_text())["cleaning"]["key_column"]
    with open(pdir / spec.raw_data_file, newline="") as fh:
        rows = list(csv.DictReader(fh))
    value_columns = {
        "retail_sales": "unit_price",
        "customer_churn": "monthly_fee",
        "energy_consumption": "energy",
        "support_operations": "resolution_minutes",
    }

    def semantic_value(text):
        value = text.strip().lower().replace("usd", "").replace("$", "").replace(",", "").strip()
        scale = 1000.0 if value.endswith("mwh") else 1.0
        for suffix in ("minutes", "min", "mwh", "kwh"):
            if value.endswith(suffix):
                value = value[:-len(suffix)].strip()
                break
        try:
            return float(value) * scale
        except ValueError:
            return None

    groups = {}
    for row in rows:
        groups.setdefault(row[key].strip(), []).append(row)
    col = value_columns[pid]
    assert any(len({semantic_value(r[col]) for r in copies if semantic_value(r[col]) is not None}) > 1
               for copies in groups.values() if len(copies) > 1)


def test_two_file_project_exposes_only_declared_inputs():
    spec = ProjectSpec.model_validate_json((PROJECTS_DIR / "support_operations" / "project.json").read_text())
    assert [(f.name, f.path) for f in spec.model_input_files()] == [
        ("tickets.csv", "raw.csv"), ("agents.csv", "agents.csv")]


@pytest.mark.parametrize("pid", PROJECTS)
def test_v2_question_metadata_and_difficulty_levers(pid):
    spec = ProjectSpec.model_validate_json((PROJECTS_DIR / pid / "project.json").read_text())
    assert 1 <= sum("derived step" in q.question.lower() for q in spec.analysis_questions) <= 2
    assert all("e.g." not in q.question.lower() for q in spec.analysis_questions)
    for q in spec.analysis_questions:
        if q.direction_key:
            assert q.direction_key in q.metric_keys
        if q.ranking_labels:
            assert set(q.ranking_labels) <= set(q.metric_keys) and len(q.ranking_labels) >= 2
