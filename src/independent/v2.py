"""Independent benchmark v2 response contracts and deterministic scorers.

This module is additive.  The frozen v1 implementation in ``src.independent.tasks``
is intentionally not imported by the paid runner and is never modified by v2.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel, Field


A1_HARNESS_V2 = r'''
import json, os, signal
IN, OUT = os.environ["INPUT_DIR"], os.environ["OUTPUT_DIR"]
tests = json.load(open(os.path.join(IN, "tests.json")))
src = open(os.path.join(IN, "solution.py")).read()
def _raises(fn, exc):
    try:
        fn()
    except exc:
        return True
    except Exception:
        return False
    return False
class _T(Exception):
    pass
def _alarm(*_):
    raise _T()
signal.signal(signal.SIGALRM, _alarm)
results, load_error = [], None
try:
    signal.alarm(5)
    ns = {"__name__": "solution"}
    exec(compile(src, "solution.py", "exec"), ns)
    signal.alarm(0)
except BaseException as e:
    signal.alarm(0)
    load_error = f"{type(e).__name__}: {e}"[:300]
for test in tests:
    if load_error:
        results.append({"test": test, "passed": False, "error": "load_error"})
        continue
    env = dict(ns)
    env["_raises"] = _raises
    try:
        signal.alarm(2)
        passed = bool(eval(test, env))
        signal.alarm(0)
        results.append({"test": test, "passed": passed, "error": None})
    except _T:
        results.append({"test": test, "passed": False, "error": "timeout"})
    except BaseException as e:
        signal.alarm(0)
        results.append({"test": test, "passed": False, "error": f"{type(e).__name__}: {e}"[:200]})
json.dump({"load_error": load_error, "results": results}, open(os.path.join(OUT, "results.json"), "w"))
'''


class DebugResponseV2(BaseModel):
    fixed_code: str = Field(description="Complete corrected Python source.")
    bug_locations: list[str] = Field(description="Every function or code region changed.")
    explanation: str = Field(description="Concise explanation of root causes and fixes.")


class ExtractionResponseV2(BaseModel):
    fields: dict = Field(description="Exactly the requested field names; null when unsupported.")


class LiteratureClaimV2(BaseModel):
    attribute: str
    value: str | float | int
    cited_ids: list[str]


class LiteratureResponseV2(BaseModel):
    ranked_ids: list[str] = Field(description="Exactly five distinct candidate IDs, best first.")
    summary: str = Field(description="Evidence-grounded synthesis with [DOC_ID] citations.")
    claims: list[LiteratureClaimV2]


@dataclass(frozen=True)
class ExtractionEnvelope:
    """Separates recoverable content from compliance with the required wrapper."""

    fields: dict | None
    wrapper_present: bool
    parse_ok: bool


def a3_candidates_text_v2(case: dict) -> str:
    return "\n\n".join(
        f"[{doc['doc_id']}] {doc['title']} — {doc['authors']} ({doc['year']})\n{doc['abstract']}"
        for doc in case["candidates"]
    )


def _norm(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text.casefold() in {"", "null", "none", "n/a", "not stated", "unknown"}:
        return None
    if text.casefold() in {"true", "yes"}:
        return True
    if text.casefold() in {"false", "no"}:
        return False
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        pass
    number = re.fullmatch(r"[$€£]?\s*([-\d,]+(?:\.\d+)?)\s*(k|m)?", text, re.I)
    if number:
        x = float(number.group(1).replace(",", ""))
        scale = {None: 1, "k": 1_000, "m": 1_000_000}[number.group(2).lower() if number.group(2) else None]
        return x * scale
    return re.sub(r"\s+", " ", text).casefold().strip(" .")


def _equal(gold, predicted) -> bool:
    g, p = _norm(gold), _norm(predicted)
    if g is None or p is None:
        return g is None and p is None
    if isinstance(g, bool) or isinstance(p, bool):
        return g is p
    if isinstance(g, float) and isinstance(p, float):
        return math.isclose(g, p, rel_tol=0.001, abs_tol=0.011)
    return g == p


def score_debugging_v2(case: dict, response: DebugResponseV2 | None, harness: dict | None) -> dict:
    results = (harness or {}).get("results", [])
    passed = sum(bool(row.get("passed")) for row in results)
    total = len(results)
    expected_locations = set(case.get("bug_locations", []))
    named = " ".join(response.bug_locations if response else []).casefold()
    location_hits = sum(location.casefold() in named for location in expected_locations)
    return {
        "operational_success": bool(harness) and not (harness or {}).get("load_error"),
        "functional_correct": bool(total) and passed == total,
        "hidden_pass_rate": passed / total if total else 0.0,
        "hidden_passed": passed,
        "hidden_total": total,
        "bug_location_recall": location_hits / len(expected_locations) if expected_locations else 1.0,
        "difficulty": case["difficulty"],
    }


def score_extraction_v2(case: dict, envelope: ExtractionEnvelope) -> dict:
    schema, gold = case["schema"], case["gold"]
    fields = envelope.fields or {}
    missing = [key for key in schema if key not in fields]
    extra = [key for key in fields if key not in schema]
    per_field = {}
    correct_nonnull = predicted_nonnull = gold_nonnull = correct_null = null_total = 0
    for key in schema:
        g, p = gold.get(key), fields.get(key)
        if _norm(g) is None:
            null_total += 1
            if _norm(p) is None:
                correct_null += 1
                per_field[key] = "correct_null"
            else:
                predicted_nonnull += 1
                per_field[key] = "hallucinated"
        else:
            gold_nonnull += 1
            if _norm(p) is not None:
                predicted_nonnull += 1
            if _equal(g, p):
                correct_nonnull += 1
                per_field[key] = "correct"
            else:
                per_field[key] = "missed" if _norm(p) is None else "wrong_value"
    precision = correct_nonnull / predicted_nonnull if predicted_nonnull else (1.0 if not gold_nonnull else 0.0)
    recall = correct_nonnull / gold_nonnull if gold_nonnull else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    content_correct = all(v in {"correct", "correct_null"} for v in per_field.values())
    schema_compliant = envelope.wrapper_present and not missing and not extra
    return {
        "operational_success": envelope.parse_ok and schema_compliant,
        "schema_compliant": schema_compliant,
        "content_correct": content_correct,
        "content_f1": f1,
        "content_precision": precision,
        "content_recall": recall,
        "null_accuracy": correct_null / null_total if null_total else None,
        "missing_keys": missing,
        "extra_keys": extra,
        "per_field": per_field,
        "difficulty": case["difficulty"],
    }


def _dcg(gains: list[int]) -> float:
    return sum((2**gain - 1) / math.log2(index + 2) for index, gain in enumerate(gains))


def _claim_supported(claim: LiteratureClaimV2, facts: dict) -> bool:
    if not claim.cited_ids:
        return False
    for doc_id in claim.cited_ids:
        fact = facts.get(doc_id)
        if fact is None or claim.attribute not in fact:
            return False
        accepted = fact[claim.attribute]
        accepted_values = accepted if isinstance(accepted, list) else [accepted]
        if not any(_equal(value, claim.value) for value in accepted_values):
            return False
    return True


def score_literature_v2(case: dict, response: LiteratureResponseV2 | None) -> dict:
    if response is None:
        return {
            "operational_success": False,
            "ranking_valid": False,
            "ndcg_at_5": 0.0,
            "citation_accuracy": 0.0,
            "evidence_grounding": 0.0,
            "difficulty": case["difficulty"],
        }
    relevance, facts = case["relevance"], case["facts"]
    ranked = response.ranked_ids
    ranking_valid = len(ranked) == 5 and len(set(ranked)) == 5 and all(doc in relevance for doc in ranked)
    gains = [relevance.get(doc, 0) for doc in ranked[:5]]
    ideal = sorted(relevance.values(), reverse=True)[:5]
    claim_results = [_claim_supported(claim, facts) for claim in response.claims]
    prose_citations = re.findall(r"\[([A-Z]\d{4})\]", response.summary)
    valid_prose = [doc in relevance for doc in prose_citations]
    citations = valid_prose + [all(doc in relevance for doc in claim.cited_ids) for claim in response.claims]
    return {
        "operational_success": ranking_valid and len(response.claims) >= 3,
        "ranking_valid": ranking_valid,
        "ndcg_at_5": _dcg(gains) / _dcg(ideal) if ideal and _dcg(ideal) else 0.0,
        "grade2_recall_at_5": sum(relevance.get(doc, 0) == 2 for doc in ranked[:5])
        / max(1, sum(value == 2 for value in relevance.values())),
        "citation_accuracy": sum(citations) / len(citations) if citations else 0.0,
        "evidence_grounding": sum(claim_results) / len(claim_results) if claim_results else 0.0,
        "claim_count": len(response.claims),
        "difficulty": case["difficulty"],
    }
