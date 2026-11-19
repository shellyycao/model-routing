"""Prospective Independent benchmark scorer v2.2.

This additive module applies the model-agnostic rules committed in
``docs/POSTHOC_V2_RULES.md``.  The frozen v2 scorer remains unchanged.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from src.independent import v2 as frozen
from src.independent.v2_posthoc import (
    claim_supported_r1,
    claim_supported_r2,
    score_a1_locations,
    score_a3_deduplicated,
)


SCORER_VERSION = "independent-v2.2-1.0"
A3Attribute = Literal["dataset", "first_author", "method", "metric", "topic", "value", "year"]

# A1 and A2 contracts are intentionally identical to v2.
DebugResponseV22 = frozen.DebugResponseV2
ExtractionResponseV22 = frozen.ExtractionResponseV2
ExtractionEnvelope = frozen.ExtractionEnvelope
A1_HARNESS_V22 = frozen.A1_HARNESS_V2


class LiteratureClaimV22(BaseModel):
    attribute: A3Attribute = Field(description="The supported fact attribute.")
    value: str | float | int
    cited_ids: list[str]


class LiteratureResponseV22(BaseModel):
    ranked_ids: list[str] = Field(description="Exactly five distinct candidate IDs, best first.")
    summary: str = Field(description="Evidence-grounded synthesis with [DOC_ID] citations.")
    claims: list[LiteratureClaimV22]


def a3_candidates_text_v22(case: dict) -> str:
    return frozen.a3_candidates_text_v2(case)


def score_debugging_v22(
    case: dict, response: DebugResponseV22 | None, harness: dict | None
) -> dict:
    """Keep functional scoring and replace only the defective location headline."""
    base = frozen.score_debugging_v2(case, response, harness)
    raw_response = response.model_dump() if response is not None else None
    normalized = score_a1_locations(case, raw_response)
    return {
        **base,
        "frozen_v2_bug_location_recall": base["bug_location_recall"],
        "bug_location_recall": normalized["normalized_location_recall"],
        "bug_location_wrong": normalized["wrong_location"],
        "bug_location_format_mismatch": normalized["format_mismatch"],
    }


def score_extraction_v22(case: dict, envelope: ExtractionEnvelope) -> dict:
    """A2 scoring is unchanged from v2."""
    return frozen.score_extraction_v2(case, envelope)


def score_literature_v22(case: dict, response: LiteratureResponseV22 | None) -> dict:
    """Use strict primary ranking and canonical all-citations grounding.

    A duplicate or unknown ID still makes the response operationally invalid.  The
    primary nDCG is zero for every invalid ranking. The committed first-occurrence,
    zero-padded deduplicated view remains secondary. The primary grounding value is
    R1 (all citations support); R2 (any citation supports) remains secondary.
    """
    if response is None:
        return {
            "operational_success": False,
            "ranking_valid": False,
            "ndcg_at_5": 0.0,
            "deduplicated_ndcg_at_5": 0.0,
            "grade2_recall_at_5": 0.0,
            "citation_validity": 0.0,
            "evidence_grounding": 0.0,
            "evidence_grounding_any_citation": 0.0,
            "claim_count": 0,
            "difficulty": case["difficulty"],
        }

    raw = response.model_dump()
    relevance, facts = case["relevance"], case["facts"]
    ranked = response.ranked_ids
    ranking_valid = len(ranked) == 5 and len(set(ranked)) == 5 and all(doc in relevance for doc in ranked)
    deduplicated = score_a3_deduplicated(case, raw)
    r1 = [claim_supported_r1(claim, facts) for claim in raw["claims"]]
    r2 = [claim_supported_r2(claim, facts) for claim in raw["claims"]]
    prose_citations = re.findall(r"\[([A-Z]\d{4})\]", response.summary)
    citations = [doc in relevance for doc in prose_citations]
    citations.extend(all(doc in relevance for doc in claim.cited_ids) for claim in response.claims)
    n_claims = len(response.claims)
    return {
        "operational_success": ranking_valid and n_claims >= 3,
        "ranking_valid": ranking_valid,
        "ndcg_at_5": deduplicated["ndcg_at_5"] if ranking_valid else 0.0,
        "deduplicated_ndcg_at_5": deduplicated["ndcg_at_5"],
        "grade2_recall_at_5": deduplicated["grade2_recall_at_5"],
        "citation_validity": sum(citations) / len(citations) if citations else 0.0,
        "evidence_grounding": sum(r1) / n_claims if n_claims else 0.0,
        "evidence_grounding_any_citation": sum(r2) / n_claims if n_claims else 0.0,
        "claim_count": n_claims,
        "difficulty": case["difficulty"],
    }
