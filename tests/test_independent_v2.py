"""Offline acceptance tests for the candidate Independent Benchmark v2."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from datasets.independent_v2 import generate
from src.independent.v2 import (
    ExtractionEnvelope,
    LiteratureClaimV2,
    LiteratureResponseV2,
    score_extraction_v2,
    score_literature_v2,
)

ROOT = Path(__file__).resolve().parents[1] / "datasets" / "independent_v2"


def _cases(task: str) -> list[dict]:
    return [json.loads(path.read_text()) for path in sorted((ROOT / task / "cases").glob("*.json"))]


def test_v2_tree_is_reproducible_and_balanced():
    assert generate.main(["--check"]) == 0
    for task in ("a1", "a2", "a3"):
        cases = _cases(task)
        assert len(cases) == 30
        assert {tier: sum(case["difficulty"] == tier for case in cases) for tier in ("easy", "medium", "hard")} == {
            "easy": 10,
            "medium": 10,
            "hard": 10,
        }


@pytest.mark.parametrize("case", _cases("a1"), ids=lambda case: case["case_id"])
def test_a1_references_pass_and_injected_bugs_fail(case):
    assert case["verification"]["reference_passes"] == len(case["hidden"])
    assert case["verification"]["buggy_fails"] >= 1
    assert case["bug_locations"]


def test_a1_has_multi_function_or_interaction_cases_and_limited_family_reuse():
    cases = _cases("a1")
    assert max(sum(case["family"] == family for case in cases) for family in {case["family"] for case in cases}) == 2
    assert sum(len(case["bug_locations"]) >= 2 for case in cases) >= 10


@pytest.mark.parametrize("case", _cases("a2"), ids=lambda case: case["case_id"])
def test_a2_gold_content_and_schema_are_perfect(case):
    result = score_extraction_v2(case, ExtractionEnvelope(fields=case["gold"], wrapper_present=True, parse_ok=True))
    assert result["operational_success"]
    assert result["schema_compliant"]
    assert result["content_correct"]
    assert result["content_f1"] == 1.0


def test_a2_separates_content_from_wrapper_compliance():
    case = _cases("a2")[0]
    result = score_extraction_v2(case, ExtractionEnvelope(fields=case["gold"], wrapper_present=False, parse_ok=True))
    assert result["content_correct"]
    assert not result["schema_compliant"]
    assert not result["operational_success"]


def test_a2_has_heterogeneous_formats_missing_values_and_conversions():
    cases = _cases("a2")
    assert len({case["document_family"] for case in cases}) == 10
    assert len({case["document_format"] for case in cases}) >= 10
    assert sum(bool(case["missing_fields"]) for case in cases) == 10
    documents = "\n".join(case["document"] for case in cases)
    assert "weekly×52/12" in documents and "lb / crate" in documents and "billed ANNUALLY" in documents


def _ideal_literature_response(case: dict) -> LiteratureResponseV2:
    ranked = sorted(case["relevance"], key=lambda doc: (-case["relevance"][doc], doc))[:5]
    claims = []
    for doc in ranked[:3]:
        fact = case["facts"][doc]
        claims.append(LiteratureClaimV2(attribute="dataset", value=fact["dataset"], cited_ids=[doc]))
    return LiteratureResponseV2(ranked_ids=ranked, summary=" ".join(f"[{doc}]" for doc in ranked), claims=claims)


@pytest.mark.parametrize("case", _cases("a3"), ids=lambda case: case["case_id"])
def test_a3_ideal_response_scores_perfectly(case):
    result = score_literature_v2(case, _ideal_literature_response(case))
    assert result["operational_success"]
    assert result["ranking_valid"]
    assert result["ndcg_at_5"] == pytest.approx(1.0)
    assert result["citation_accuracy"] == 1.0
    assert result["evidence_grounding"] == 1.0


def test_a3_detects_ranking_citation_and_grounding_errors():
    case = _cases("a3")[0]
    response = _ideal_literature_response(case)
    response.ranked_ids[0] = "Z9999"
    response.claims[0].value = "not the cited dataset"
    response.summary += " [Z9999]"
    result = score_literature_v2(case, response)
    assert not result["ranking_valid"]
    assert result["citation_accuracy"] < 1.0
    assert result["evidence_grounding"] < 1.0


def test_a3_labels_are_human_adjudicated_and_controlled_not_live_retrieval():
    cases = _cases("a3")
    assert all(case["controlled_retrieval"] for case in cases)
    assert all(case["label_status"] == "human_adjudicated" for case in cases)
    assert all(list(case["relevance"].values()).count(2) == 4 for case in cases)
    expected_grade1 = {"easy": 4, "medium": 8, "hard": 12}
    assert all(list(case["relevance"].values()).count(1) == expected_grade1[case["difficulty"]] for case in cases)


def test_a3_hate_speech_surface_is_specific_after_human_review():
    cases = _cases("a3")
    candidate_text = "\n".join(
        candidate["title"] + "\n" + candidate["abstract"]
        for case in cases
        for candidate in case["candidates"]
    ).lower()
    assert "detecting abusive online content" not in candidate_text
    assert "detecting hate speech" in candidate_text
