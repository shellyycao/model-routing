"""Reporting validator: deterministic checks of a ReportOutput against verified findings.
Reports here are SYNTHETIC_FIXTURE objects built in the test, not model outputs."""

import json

import pytest

from datasets.generate import PROJECTS_DIR
from src.contracts import DerivedValue, QUALITY_METRICS, KeyFinding, ProjectSpec, ReportOutput, StageId
from src.evaluation.reporting import extract_numbers, number_matches, validate_reporting

PDIR = PROJECTS_DIR / "retail_sales"
SPEC = ProjectSpec.model_validate_json((PDIR / "project.json").read_text())
F = json.loads((PDIR / "canonical" / "findings.json").read_text())


def good_report() -> ReportOutput:
    findings = []
    for q in SPEC.analysis_questions:
        direction = None
        if q.direction_key:
            direction = "increase" if F[q.direction_key] > 0 else "decrease" if F[q.direction_key] < 0 else "no_change"
        ranking = None
        if q.ranking_labels:
            ranking = [q.ranking_labels[k] for k in sorted(
                q.ranking_labels, key=lambda k: (-F[k], q.ranking_labels[k]))]
        findings.append(KeyFinding(
            finding_id=q.question_id,
            statement="; ".join(f"{k}: {F[k]:,.6f}" for k in q.metric_keys) + ".",
            evidence_refs=list(q.metric_keys), reported_values={k: F[k] for k in q.metric_keys},
            direction=direction, ranking=ranking))
    return ReportOutput(
        title="Retail sales review 2023-2024",
        executive_summary="All required metrics were checked against verified findings.",
        key_findings=findings,
        limitations=["Data is synthetic; dates were standardised from five formats."],
        conclusion="Growth was concentrated in the second half of 2024.",
    )


def _failed(res):
    return {c.name for c in res.checks if c.mandatory and not c.passed}


def test_reference_report_passes():
    res = validate_reporting(good_report(), F, SPEC)
    assert res.stage == StageId.REPORTING and res.hard_pass, [c for c in res.checks if not c.passed]
    assert set(res.quality) == set(QUALITY_METRICS[StageId.REPORTING])
    assert res.quality == {"finding_coverage": 1.0, "numerical_consistency": 1.0, "unsupported_claim_count": 0.0}


def test_accepts_dict_and_json():
    rep = good_report()
    assert validate_reporting(rep.model_dump(), F, SPEC).hard_pass
    assert validate_reporting(rep.model_dump_json(), F, SPEC).hard_pass


def test_fabricated_number_in_text_is_unsupported():
    rep = good_report()
    rep.conclusion = "Customer satisfaction rose to 87.5% and churn fell by 3.2%."
    res = validate_reporting(rep, F, SPEC)
    assert res.hard_pass
    assert res.quality["unsupported_claim_count"] == 2.0
    check = next(c for c in res.checks if c.name == "unsupported_claims_within_threshold")
    assert check.passed and "87.5%" in check.detail
    assert not next(c for c in validate_reporting(rep, F, SPEC, max_unsupported_claims=0).checks
                    if c.name == "unsupported_claims_within_threshold").passed


def test_wrong_reported_value_breaks_consistency():
    rep = good_report()
    rep.key_findings[1].reported_values["revenue_east"] = F["revenue_east"] * 1.05
    res = validate_reporting(rep, F, SPEC)
    assert {"reported_values_consistent"} == _failed(res)
    n = sum(len(q.metric_keys) for q in SPEC.analysis_questions)
    assert res.quality["numerical_consistency"] == pytest.approx((n - 1) / n)


def test_correct_number_attributed_to_wrong_key_is_inconsistent():
    rep = good_report()
    rep.key_findings[1].reported_values["revenue_east"] = F["revenue_south"]
    res = validate_reporting(rep, F, SPEC)
    assert "reported_values_consistent" in _failed(res)
    assert res.quality["unsupported_claim_count"] == 0.0    # the number itself exists in findings


def test_missing_required_finding_lowers_coverage():
    rep = good_report()
    rep.key_findings = [kf for kf in rep.key_findings if kf.finding_id != "q5"]
    res = validate_reporting(rep, F, SPEC)
    assert _failed(res) == {"required_findings_covered", "required_metric_keys_present"}
    assert res.quality["finding_coverage"] == pytest.approx((len(SPEC.analysis_questions) - 1) / len(SPEC.analysis_questions))


def test_finding_without_relevant_evidence_is_not_covered():
    rep = good_report()
    rep.key_findings[2].evidence_refs = ["total_revenue"]
    rep.key_findings[2].reported_values = {}
    res = validate_reporting(rep, F, SPEC)
    assert "required_metric_keys_present" in _failed(res)


def test_no_reported_values_omits_consistency_metric():
    rep = good_report()
    for kf in rep.key_findings:
        kf.reported_values = {}
    res = validate_reporting(rep, F, SPEC)
    assert "numerical_consistency" not in res.quality
    assert {"required_metric_keys_present", "reported_values_consistent"} <= _failed(res)


def test_report_checked_against_verified_not_canonical_findings():
    """If the upstream (verified) findings differ, a report faithful to them is consistent."""
    verified = dict(F, total_revenue=400000.0)
    rep = good_report()
    rep.key_findings[0].reported_values["total_revenue"] = 400000.0
    rep.key_findings[0].statement = (f"total_revenue: 400000; order_count: {F['order_count']}; "
                                     f"average_order_value: {F['average_order_value']}.")
    res = validate_reporting(rep, verified, SPEC, quality_basis="conditional_reference")
    assert res.hard_pass
    if "quality_basis" in type(res).model_fields:
        assert res.quality_basis == "conditional_reference"


def test_invalid_report():
    res = validate_reporting({"title": "x"}, F, SPEC)
    assert "report_valid" in _failed(res) and not res.hard_pass


def test_number_extraction_rules():
    vals = [c.value for c in extract_numbers(
        "Q1 revenue_2024_q1 R100001 on 2024-03-05 rose 12.5% to $1,234.50, about $1.2M or 3k; down -4%")]
    assert vals == [12.5, 1234.5, 1.2e6, 3000.0, -4.0]


def test_rounding_rule():
    assert number_matches(445.3e3, 445325.07, 100, 0.01, 1e-4)      # "$445.3K"
    assert not number_matches(1.0e6, 1234567, 1e6, 0.01, 1e-4)      # "$1M": >1% off
    assert number_matches(10.1, 10.082501, 0.1, 0.01, 1e-4)
    assert not number_matches(10.3, 10.082501, 0.1, 0.01, 1e-4)


def test_missing_required_metric_key_is_a_hard_failure():
    rep = good_report()
    del rep.key_findings[1].reported_values["revenue_west"]
    assert "required_metric_keys_present" in _failed(validate_reporting(rep, F, SPEC))


def test_see_values_statement_fails_even_with_complete_structured_values():
    rep = good_report()
    rep.key_findings[0].statement = "See values."
    assert "finding_statements_substantive" in _failed(validate_reporting(rep, F, SPEC))


def test_wrong_direction_and_ranking_are_hard_failures():
    rep = good_report()
    rep.key_findings[3].direction = "decrease" if rep.key_findings[3].direction == "increase" else "increase"
    assert "directions_correct" in _failed(validate_reporting(rep, F, SPEC))
    rep = good_report()
    rep.key_findings[1].ranking = list(reversed(rep.key_findings[1].ranking))
    assert "rankings_correct" in _failed(validate_reporting(rep, F, SPEC))


def test_comparative_direction_wording_does_not_false_reject():
    rep = good_report()
    rep.key_findings[3].statement += " The earlier year's revenue was lower than the later year's revenue."
    assert validate_reporting(rep, F, SPEC).hard_pass


def test_tied_groups_may_appear_in_either_order():
    verified = dict(F)
    tied = max(F[k] for k in ("revenue_north", "revenue_south", "revenue_east", "revenue_west")) + 100
    verified["revenue_east"] = verified["revenue_south"] = tied
    rep = good_report()
    rep.key_findings[1].reported_values.update(revenue_east=tied, revenue_south=tied)
    rep.key_findings[1].statement = "; ".join(
        f"{k}: {verified[k]}" for k in SPEC.analysis_questions[1].metric_keys) + "."
    rest = sorted(["North", "West"], key=lambda label: -verified[f"revenue_{label.lower()}"])
    rep.key_findings[1].ranking = ["South", "East", *rest]
    assert validate_reporting(rep, verified, SPEC).hard_pass


def test_value_under_wrong_finding_is_a_hard_failure():
    rep = good_report()
    rep.key_findings[1].reported_values["total_revenue"] = F["total_revenue"]
    assert {"required_metric_keys_present", "reported_values_consistent"} <= _failed(validate_reporting(rep, F, SPEC))


def test_text_number_matching_another_finding_is_wrong_attribution():
    rep = good_report()
    rep.key_findings[1].statement += f" Total revenue was {F['total_revenue']}."
    assert "numeric_attribution_correct" in _failed(validate_reporting(rep, F, SPEC))


def test_correct_values_under_wrong_groups_in_text_are_a_hard_failure():
    rep = good_report()
    rep.key_findings[1].statement = (f"East revenue was {F['revenue_south']}; "
                                     f"South revenue was {F['revenue_east']}; "
                                     f"North revenue was {F['revenue_north']}; "
                                     f"West revenue was {F['revenue_west']}.")
    assert "prose_claims_consistent" in _failed(validate_reporting(rep, F, SPEC))


def test_nonranking_metric_values_cannot_be_swapped_in_text():
    rep = good_report()
    rep.key_findings[0].statement = (
        f"total revenue: {F['average_order_value']}; order count: {F['order_count']}; "
        f"average order value: {F['total_revenue']}.")
    assert "prose_claims_consistent" in _failed(validate_reporting(rep, F, SPEC))


def test_novel_wrong_number_attached_to_metric_is_a_hard_failure():
    rep = good_report()
    rep.key_findings[0].statement = (
        f"total revenue: 12345; order count: {F['order_count']}; "
        f"average order value: {F['average_order_value']}.")
    assert "prose_claims_consistent" in _failed(validate_reporting(rep, F, SPEC))


def test_group_value_before_label_is_checked():
    rep = good_report()
    rep.key_findings[1].statement = (
        f"{F['revenue_south']} East; {F['revenue_east']} South; "
        f"{F['revenue_north']} North; {F['revenue_west']} West.")
    assert "prose_claims_consistent" in _failed(validate_reporting(rep, F, SPEC))


@pytest.mark.parametrize("statement", [
    "Across 520 orders, total revenue was $400,000.",
    "Total revenue was $400,000 across 520 orders.",
])
def test_correct_multi_metric_natural_sentence_is_not_misattributed(statement):
    rep = good_report()
    verified = dict(F, total_revenue=400000.0, order_count=520.0)
    rep.key_findings[0].reported_values.update(total_revenue=400000.0, order_count=520.0)
    rep.key_findings[0].statement = statement
    assert validate_reporting(rep, verified, SPEC).hard_pass


@pytest.mark.parametrize("kind,operands", [
    ("difference", ["revenue_east", "revenue_south"]),
    ("ratio", ["revenue_east", "revenue_south"]),
    ("pct_change", ["revenue_east", "revenue_south"]),
    ("share", ["revenue_east", "total_revenue"]),
])
def test_each_correct_derived_value_kind_is_supported(kind, operands):
    rep = good_report()
    a, b = (F[k] for k in operands)
    value = {"difference": a - b, "ratio": a / b,
             "pct_change": (a - b) / b * 100, "share": a / b * 100}[kind]
    rep.key_findings[1].derived_values = [DerivedValue(
        kind=kind, operands=operands, value=value)]
    rep.key_findings[1].statement += f" The declared {kind} was {value:.6f}."
    rep.executive_summary += f" The verified {kind} was {value:.6f}."
    res = validate_reporting(rep, F, SPEC)
    assert res.hard_pass and res.quality["unsupported_claim_count"] == 0


def test_verified_cleaning_count_is_supported():
    rep = good_report()
    rep.limitations.append("Cleaning removed 40 duplicate rows.")
    res = validate_reporting(rep, F, SPEC, cleaning_counts={"duplicates_removed": 40})
    assert res.hard_pass and res.quality["unsupported_claim_count"] == 0


def test_incorrect_derived_value_is_a_hard_failure():
    rep = good_report()
    rep.key_findings[1].derived_values = [DerivedValue(
        kind="share", operands=["revenue_east", "total_revenue"], value=99.0)]
    assert "derived_values_correct" in _failed(validate_reporting(rep, F, SPEC))
