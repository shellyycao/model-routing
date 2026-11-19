"""Cross-project checks for every benchmark project: independent follower solutions pass all three
validators, deliberately broken ones fail for the right reason, and rule logs reconcile."""

import importlib.util
import json
import re
from pathlib import Path

import pandas as pd
import pytest

from datasets.generate import PROJECTS_DIR, REGISTRY
from src.contracts import KeyFinding, ProjectSpec, ReportOutput
from src.evaluation.analysis import validate_analysis
from src.evaluation.cleaning import validate_cleaning
from src.evaluation.reporting import validate_reporting

SOLUTIONS = Path(__file__).parent / "fixtures" / "benchmark" / "solutions"
PROJECTS = list(REGISTRY)


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, SOLUTIONS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _clean(pid, tmp_path, bug=None) -> Path:
    raw = pd.read_csv(PROJECTS_DIR / pid / "raw.csv", dtype=str, keep_default_na=False)
    out = tmp_path / f"{pid}_{bug}_cleaned.csv"
    if pid == "support_operations":
        agents = pd.read_csv(PROJECTS_DIR / pid / "agents.csv", dtype=str, keep_default_na=False)
        cleaned = _mod(f"{pid}_clean").clean(raw, bug, agents=agents)
    else:
        cleaned = _mod(f"{pid}_clean").clean(raw, bug)
    cleaned.to_csv(out, index=False)
    return out


def _failed(res):
    return {c.name for c in res.checks if c.mandatory and not c.passed}


def _spec(pid):
    return ProjectSpec.model_validate_json((PROJECTS_DIR / pid / "project.json").read_text())


@pytest.mark.parametrize("pid", PROJECTS)
def test_follower_pipeline_passes_cleaning_and_analysis(pid, tmp_path):
    pdir = PROJECTS_DIR / pid
    cleaned = _clean(pid, tmp_path)
    res = validate_cleaning(cleaned, pdir)
    assert res.hard_pass, [c for c in res.checks if not c.passed]
    assert res.quality["cleaning_correctness"] == 1.0
    an = _mod(f"{pid}_analysis")
    on_canonical = an.analyze(pd.read_csv(pdir / "canonical" / "cleaned.csv"))
    on_own = an.analyze(pd.read_csv(cleaned))
    r1 = validate_analysis(on_canonical, pdir, second_findings=on_own)
    assert r1.hard_pass, [c for c in r1.checks if not c.passed]
    assert r1.quality["reproducibility"] == 1.0
    assert validate_analysis(on_own, pdir).hard_pass


@pytest.mark.parametrize("pid", PROJECTS)
def test_canonical_artifacts_pass(pid):
    pdir = PROJECTS_DIR / pid
    assert validate_cleaning(pdir / "canonical" / "cleaned.csv", pdir).hard_pass
    assert validate_analysis(pdir / "canonical" / "findings.json", pdir).hard_pass


CLEANING_BUGS = [
    ("customer_churn", "no_dedup", {"no_duplicate_keys"}),
    ("customer_churn", "drop_missing_satisfaction", {"row_set_matches_reference"}),
    ("customer_churn", "tickets_missing_dropped", {"row_set_matches_reference"}),
    ("customer_churn", "churn_strings_unmapped", {"row_set_matches_reference"}),
    ("energy_consumption", "ignore_mwh", {"values_match_reference"}),
    ("energy_consumption", "ignore_fahrenheit", {"values_match_reference"}),
    ("energy_consumption", "drop_bad_temperature", {"row_set_matches_reference"}),
]


@pytest.mark.parametrize("pid,bug,expected", CLEANING_BUGS)
def test_broken_cleaning_fails_for_the_right_reason(pid, bug, expected, tmp_path):
    res = validate_cleaning(_clean(pid, tmp_path, bug), PROJECTS_DIR / pid)
    assert not res.hard_pass
    assert expected <= _failed(res), _failed(res)


def test_unit_conversion_errors_point_at_the_right_column(tmp_path):
    pdir = PROJECTS_DIR / "energy_consumption"
    for bug, col in [("ignore_mwh", "energy_kwh"), ("ignore_fahrenheit", "temperature_c")]:
        res = validate_cleaning(_clean("energy_consumption", tmp_path, bug), pdir)
        detail = next(c.detail for c in res.checks if c.name == "values_match_reference")
        assert detail.startswith(col), detail


ANALYSIS_BUGS = [
    ("customer_churn", "rate_as_fraction", "churn_rate_pct"),
    ("customer_churn", "missing_sat_as_zero", "satisfaction_mean"),
    ("customer_churn", "at_risk_includes_missing_sat", "at_risk_customer_count"),
    ("energy_consumption", "spearman_not_pearson", "commercial_temp_kwh_corr"),
    ("energy_consumption", "hot_gt_not_ge", "hot_commercial_reading_count"),
    ("energy_consumption", "h2_base", "kwh_h2_vs_h1_change_pct"),
]


@pytest.mark.parametrize("pid,bug,key", ANALYSIS_BUGS)
def test_broken_analysis_fails_for_the_right_reason(pid, bug, key):
    pdir = PROJECTS_DIR / pid
    findings = _mod(f"{pid}_analysis").analyze(pd.read_csv(pdir / "canonical" / "cleaned.csv"), bug)
    res = validate_analysis(findings, pdir)
    assert _failed(res) == {"values_within_tolerance"}
    assert key in next(c.detail for c in res.checks if c.name == "values_within_tolerance")


def _auto_report(spec: ProjectSpec, f: dict) -> ReportOutput:
    """A faithful SYNTHETIC_FIXTURE report: every metric stated with 2 decimals and reported exactly."""
    kfs = [KeyFinding(finding_id=q.question_id,
                      statement="; ".join(f"{k.replace('_', ' ')}: {f[k]:,.2f}" for k in q.metric_keys) + ".",
                      evidence_refs=list(q.metric_keys), reported_values={k: f[k] for k in q.metric_keys},
                      direction=("increase" if f[q.direction_key] > 0 else
                                 "decrease" if f[q.direction_key] < 0 else "no_change") if q.direction_key else None,
                      ranking=([q.ranking_labels[k] for k in sorted(
                          q.ranking_labels, key=lambda k: (-f[k], q.ranking_labels[k]))]
                          if q.ranking_labels else None))
           for q in spec.analysis_questions]
    return ReportOutput(title=f"{spec.project_id} findings", executive_summary="Summary of verified findings.",
                        key_findings=kfs, limitations=["Synthetic data."], conclusion="See findings.")


@pytest.mark.parametrize("pid", PROJECTS)
def test_faithful_report_passes_and_fabrication_fails(pid):
    spec = _spec(pid)
    f = json.loads((PROJECTS_DIR / pid / "canonical" / "findings.json").read_text())
    rep = _auto_report(spec, f)
    res = validate_reporting(rep, f, spec)
    assert res.hard_pass, [c for c in res.checks if not c.passed]
    assert res.quality["unsupported_claim_count"] == 0.0
    rep.executive_summary = "An estimated 4,321.9 units were affected."
    res = validate_reporting(rep, f, spec)
    assert res.hard_pass and res.quality["unsupported_claim_count"] == 1.0


def test_churn_natural_group_and_cohort_swaps_are_hard_failures():
    spec = _spec("customer_churn")
    f = json.loads((PROJECTS_DIR / "customer_churn" / "canonical" / "findings.json").read_text())
    rep = _auto_report(spec, f)
    rep.key_findings[1].statement = (
        f"Basic churn rate was {f['churn_rate_standard_pct']}%; "
        f"Standard churn rate was {f['churn_rate_basic_pct']}%; "
        f"Premium churn rate was {f['churn_rate_premium_pct']}%.")
    assert "prose_claims_consistent" in _failed(validate_reporting(rep, f, spec))

    rep = _auto_report(spec, f)
    rep.key_findings[2].statement = (
        f"2021 churn rate was {f['churn_rate_cohort_2022_pct']}%; "
        f"2022 churn rate was {f['churn_rate_cohort_2021_pct']}%; "
        f"2023 churn rate was {f['churn_rate_cohort_2023_pct']}%; "
        f"2024 churn rate was {f['churn_rate_cohort_2024_pct']}%.")
    assert "prose_claims_consistent" in _failed(validate_reporting(rep, f, spec))


def _gt(pid):
    return json.loads((PROJECTS_DIR / pid / "ground_truth.json").read_text())


def test_churn_rule_log_reconciles():
    g = _gt("customer_churn")
    log, inj = g["cleaning"]["rule_log"], g["generation"]["injected"]
    assert log["R2_duplicates_removed"] == inj["duplicate_rows_exact"] + inj["duplicate_rows_changed_value"]
    assert log["dropped_R3_signup_date"] == inj["missing_signup_date"]
    assert log["dropped_R4_plan"] == inj["unknown_plan"]
    assert log["dropped_R5_contract_type"] == inj["missing_contract"]
    assert log["dropped_R6_monthly_fee"] == inj["invalid_fee"] + inj["missing_fee"]
    assert log["dropped_R7_tenure_months"] == inj["invalid_tenure"]
    assert log["dropped_R8_support_tickets"] == inj["negative_tickets"]
    assert log["dropped_R10_churned"] == inj["missing_or_unrecognised_churned"]
    assert 0 < log["R9_satisfaction_set_missing"] <= inj["missing_satisfaction"] + inj["satisfaction_out_of_range"]
    assert g["analysis"]["metrics"]["satisfaction_missing_count"] == log["R9_satisfaction_set_missing"]


def test_energy_rule_log_reconciles():
    g = _gt("energy_consumption")
    log, inj = g["cleaning"]["rule_log"], g["generation"]["injected"]
    assert log["R2_duplicates_removed"] == inj["duplicate_rows_exact"] + inj["duplicate_rows_changed_value"]
    assert log["dropped_R3_reading_date"] == inj["missing_date"]
    assert log["dropped_R4_meter_id"] == inj["missing_meter"]
    assert log["dropped_R5_building_type"] == inj["unknown_building_type"]
    assert log["dropped_R6_tariff"] == inj["missing_tariff"]
    assert log["dropped_R7_energy"] == inj["missing_energy"] + inj["unparseable_energy"] + inj["negative_energy"]
    assert 0 < log["R8_temperature_set_missing"] <= inj["missing_temperature"] + inj["temperature_sensor_error"]
    assert g["analysis"]["metrics"]["temperature_missing_count"] == log["R8_temperature_set_missing"]


def test_energy_raw_has_mixed_units():
    text = (PROJECTS_DIR / "energy_consumption" / "raw.csv").read_text()
    for token in ["MWh", "kWh", "kwh", "°F", "°C", "ERR", "999.0"]:
        assert token in text, token
    assert re.search(r"\d\.\d\dF$", text, flags=re.M)              # Fahrenheit without degree sign


def test_churn_raw_has_encoding_variants():
    raw = pd.read_csv(PROJECTS_DIR / "customer_churn" / "raw.csv", dtype=str, keep_default_na=False)
    assert {"Churned", "Active", "Y", "N", "?"} & set(raw["churned"]) >= {"Churned", "Active", "?"}
    assert raw["tenure_months"].str.contains("onth").any()
    assert raw["customer_id"].str.strip().duplicated().any()
