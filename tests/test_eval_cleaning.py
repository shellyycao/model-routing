"""Cleaning validator: reference solutions pass; deliberately broken ones fail for the right reason."""

import importlib.util
import shutil
from pathlib import Path

import pandas as pd
import pytest

from datasets.generate import PROJECTS_DIR
from src.contracts import QUALITY_METRICS, StageId
from src.evaluation.cleaning import validate_cleaning

PDIR = PROJECTS_DIR / "retail_sales"
SOLUTIONS = Path(__file__).parent / "fixtures" / "benchmark" / "solutions"


def _solution():
    spec = importlib.util.spec_from_file_location("retail_sales_clean", SOLUTIONS / "retail_sales_clean.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(tmp_path, bug=None) -> Path:
    raw = pd.read_csv(PDIR / "raw.csv", dtype=str, keep_default_na=False)
    df = _solution().clean(raw, bug)
    out = tmp_path / "cleaned.csv"
    df.to_csv(out, index=bug == "unsorted_with_index", float_format="%.2f", lineterminator="\n")
    return out


def _failed(res):
    return {c.name for c in res.checks if c.mandatory and not c.passed}


def test_canonical_file_passes_with_perfect_scores():
    res = validate_cleaning(PDIR / "canonical" / "cleaned.csv", PDIR)
    assert res.stage == StageId.CLEANING and res.hard_pass, _failed(res)
    assert set(res.quality) == set(QUALITY_METRICS[StageId.CLEANING])
    assert all(v == 1.0 for v in res.quality.values())


def test_independent_pandas_solution_passes(tmp_path):
    res = validate_cleaning(_run(tmp_path), PDIR)
    assert res.hard_pass, [c for c in res.checks if not c.passed]
    assert res.quality["cleaning_correctness"] == 1.0


def test_row_order_and_index_column_do_not_matter_for_correctness(tmp_path):
    res = validate_cleaning(_run(tmp_path, "unsorted_with_index"), PDIR)
    assert res.hard_pass                      # extra index column is a non-mandatory finding
    assert not next(c for c in res.checks if c.name == "no_extra_columns").passed
    assert res.quality["schema_compliance"] < 1.0


def test_no_dedup_fails_duplicates(tmp_path):
    res = validate_cleaning(_run(tmp_path, "no_dedup"), PDIR)
    assert not res.hard_pass
    assert "no_duplicate_keys" in _failed(res)
    assert res.quality["data_integrity"] < 1.0


def test_wrong_date_parsing_fails_values_and_rows(tmp_path):
    res = validate_cleaning(_run(tmp_path, "dayfirst_slash"), PDIR)
    assert not res.hard_pass
    failed = _failed(res)
    assert "values_match_reference" in failed       # swapped month/day
    assert "row_set_matches_reference" in failed    # impossible dates (month > 12) dropped
    detail = next(c.detail for c in res.checks if c.name == "values_match_reference")
    assert "order_date" in detail and "revenue" not in detail


def test_missing_category_synonyms_drops_rows(tmp_path):
    res = validate_cleaning(_run(tmp_path, "no_category_synonyms"), PDIR)
    assert _failed(res) == {"row_set_matches_reference"}
    assert res.quality["data_integrity"] < 1.0


def test_keeping_invalid_quantities_fails_schema_and_rows(tmp_path):
    res = validate_cleaning(_run(tmp_path, "keep_invalid_quantity"), PDIR)
    failed = _failed(res)
    assert {"schema_constraints", "row_set_matches_reference"} <= failed
    assert "quantity:min" in next(c.detail for c in res.checks if c.name == "schema_constraints")


def test_wrong_revenue_formula_fails_values_only(tmp_path):
    res = validate_cleaning(_run(tmp_path, "revenue_ignores_discount"), PDIR)
    assert _failed(res) == {"values_match_reference"}
    assert "revenue" in next(c.detail for c in res.checks if c.name == "values_match_reference")
    assert 0.9 < res.quality["cleaning_correctness"] < 1.0


def test_missing_column_fails_schema(tmp_path):
    res = validate_cleaning(_run(tmp_path, "drop_revenue"), PDIR)
    assert {"required_columns_present", "schema_constraints", "values_match_reference"} <= _failed(res)


def test_missing_and_unparseable_output(tmp_path):
    res = validate_cleaning(tmp_path / "nope.csv", PDIR)
    assert not res.hard_pass and "output_exists" in _failed(res)
    assert res.quality == {"cleaning_correctness": 0.0, "data_integrity": 0.0, "schema_compliance": 0.0}
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b\n1,2,3\n")
    res = validate_cleaning(bad, PDIR)
    assert "output_parses" in _failed(res)
    res = validate_cleaning(None, PDIR)
    assert not res.hard_pass


def test_single_changed_cell_detected(tmp_path):
    out = tmp_path / "cleaned.csv"
    shutil.copy(PDIR / "canonical" / "cleaned.csv", out)
    lines = out.read_text().splitlines()
    parts = lines[10].split(",")
    parts[3] = "South" if parts[3] != "South" else "North"
    lines[10] = ",".join(parts)
    out.write_text("\n".join(lines) + "\n")
    res = validate_cleaning(out, PDIR)
    assert _failed(res) == {"values_match_reference"}


def test_utf8_bom_on_first_header_is_ignored(tmp_path):
    out = tmp_path / "bom.csv"
    text = (PDIR / "canonical" / "cleaned.csv").read_text()
    out.write_text("\ufeff" + text, encoding="utf-8")
    assert validate_cleaning(out, PDIR).hard_pass
