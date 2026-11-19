"""Model-agnostic post-hoc helpers for Independent-v2.

Exploratory only. These functions never mutate or replace frozen scores.
"""

from __future__ import annotations

import ast
import hashlib
import math
import random
import re
import unicodedata
from collections import Counter
from typing import Iterable

from src.independent import v2 as frozen


IDENTIFIER_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
LINE_PATTERNS = (
    ("explicit_range", re.compile(r"\blines?\s+(\d+)\s*(?:-|–|—|to)\s*(\d+)\b", re.I)),
    ("explicit_line", re.compile(r"\bline\s+(\d+)\b", re.I)),
    ("explicit_l", re.compile(r"\bL(\d+)\b", re.I)),
    ("bare_range", re.compile(r"\b(\d+)\s*(?:-|–|—|to)\s*(\d+)\b", re.I)),
)


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def function_spans(source: str | None) -> dict[str, list[tuple[int, int]]]:
    if not source:
        return {}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    spans: dict[str, list[tuple[int, int]]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            spans.setdefault(node.name.casefold(), []).append((node.lineno, node.end_lineno or node.lineno))
    return spans


def line_anchor_details(text: str) -> list[tuple[int, int, str]]:
    anchors = []
    occupied: set[tuple[int, int]] = set()
    for kind, pattern in LINE_PATTERNS:
        for match in pattern.finditer(text):
            start = int(match.group(1))
            end = int(match.group(2)) if match.lastindex and match.lastindex >= 2 else start
            anchor = (min(start, end), max(start, end))
            if anchor not in occupied:
                anchors.append((anchor[0], anchor[1], kind))
                occupied.add(anchor)
    return anchors


def line_anchors(text: str) -> list[tuple[int, int]]:
    return [(start, end) for start, end, _ in line_anchor_details(text)]


def _overlaps(anchor: tuple[int, int], span: tuple[int, int]) -> bool:
    return anchor[0] <= span[1] and span[0] <= anchor[1]


def score_a1_locations(case: dict, response: dict | None) -> dict:
    """Apply the committed normalized function/line rule and classify every miss."""
    entries = list((response or {}).get("bug_locations") or [])
    buggy_spans = function_spans(case.get("buggy"))
    fixed_spans = function_spans((response or {}).get("fixed_code"))
    all_spans: dict[str, list[tuple[int, int]]] = {}
    for mapping in (buggy_spans, fixed_spans):
        for name, spans in mapping.items():
            all_spans.setdefault(name, []).extend(spans)
    known_functions = set(all_spans)

    parsed_entries = []
    any_locatable = False
    for entry in entries:
        normalized = normalize_text(str(entry))
        identifiers = {token.casefold() for token in IDENTIFIER_RE.findall(normalized)}
        anchors = line_anchor_details(normalized)
        locatable = bool(identifiers & known_functions or anchors)
        any_locatable = any_locatable or locatable
        parsed_entries.append((identifiers, anchors))

    rows = []
    for gold in case.get("bug_locations", []):
        function_name = str(gold).split(maxsplit=1)[0].casefold()
        spans = all_spans.get(function_name, [])
        by_identifier = any(function_name in identifiers for identifiers, _ in parsed_entries)
        by_buggy = any(
            _overlaps((start, end), span)
            for _, anchors in parsed_entries
            for start, end, _ in anchors
            for span in buggy_spans.get(function_name, [])
        )
        by_fixed = any(
            _overlaps((start, end), span)
            for _, anchors in parsed_entries
            for start, end, _ in anchors
            for span in fixed_spans.get(function_name, [])
        )
        by_nonbare = any(
            kind != "bare_range" and _overlaps((start, end), span)
            for _, anchors in parsed_entries
            for start, end, kind in anchors
            for span in spans
        )
        by_bare = any(
            kind == "bare_range" and _overlaps((start, end), span)
            for _, anchors in parsed_entries
            for start, end, kind in anchors
            for span in spans
        )
        matched = by_identifier or by_buggy or by_fixed
        rows.append({
            "gold_location": gold,
            "gold_function": function_name,
            "normalized_location_match": matched,
            "miss_reason": None if matched else ("wrong_location" if any_locatable else "format_mismatch"),
            "bare_range_only_match": matched and not by_identifier and not by_nonbare and by_bare,
            "fixed_span_only_match": matched and not by_identifier and not by_buggy and by_fixed,
        })
    return {
        "normalized_location_recall": (
            sum(row["normalized_location_match"] for row in rows) / len(rows) if rows else 1.0
        ),
        "locations": rows,
        "wrong_location": sum(row["miss_reason"] == "wrong_location" for row in rows),
        "format_mismatch": sum(row["miss_reason"] == "format_mismatch" for row in rows),
        "bare_range_only_match": sum(row["bare_range_only_match"] for row in rows),
        "fixed_span_only_match": sum(row["fixed_span_only_match"] for row in rows),
    }


ATTRIBUTE_ALIASES = {
    "author": "first_author", "authors": "first_author", "lead_author": "first_author",
    "firstauthor": "first_author", "primary_author": "first_author",
    "methods": "method", "approach": "method", "approaches": "method",
    "technique": "method", "techniques": "method",
    "datasets": "dataset", "corpus": "dataset", "corpora": "dataset",
    "benchmark": "dataset", "benchmarks": "dataset",
    "metrics": "metric", "measure": "metric", "measures": "metric",
    "evaluation_metric": "metric",
    "score": "value", "metric_value": "value", "result_value": "value",
    "topics": "topic", "task": "topic", "research_topic": "topic",
    "publication_year": "year",
}


def canonical_attribute(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text).casefold()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return ATTRIBUTE_ALIASES.get(text, text)


def _accepted(value) -> list:
    return value if isinstance(value, list) else [value]


def frozen_claim_reason(claim: dict, facts: dict) -> str:
    cited = list(claim.get("cited_ids") or [])
    if not cited:
        return "no_citation"
    if any(doc_id not in facts for doc_id in cited):
        return "unknown_doc"
    attribute = claim.get("attribute")
    if any(attribute not in facts[doc_id] for doc_id in cited):
        return "attribute_key_mismatch"
    if any(
        not any(frozen._equal(accepted, claim.get("value")) for accepted in _accepted(facts[doc_id][attribute]))
        for doc_id in cited
    ):
        return "value_mismatch"
    return "supported"


def _canonical_fact_values(fact: dict, attribute: str) -> list:
    values = []
    for key, accepted in fact.items():
        if canonical_attribute(key) == attribute:
            values.extend(_accepted(accepted))
    return values


def claim_supported_r1(claim: dict, facts: dict) -> bool:
    cited = list(claim.get("cited_ids") or [])
    if not cited or any(doc_id not in facts for doc_id in cited):
        return False
    attribute = canonical_attribute(claim.get("attribute", ""))
    return all(
        (values := _canonical_fact_values(facts[doc_id], attribute))
        and any(frozen._equal(value, claim.get("value")) for value in values)
        for doc_id in cited
    )


def claim_supported_r2(claim: dict, facts: dict) -> bool:
    cited = list(claim.get("cited_ids") or [])
    if not cited:
        return False
    attribute = canonical_attribute(claim.get("attribute", ""))
    for doc_id in cited:
        if doc_id not in facts:
            continue
        values = _canonical_fact_values(facts[doc_id], attribute)
        if values and any(frozen._equal(value, claim.get("value")) for value in values):
            return True
    return False


def score_a3_grounding(case: dict, response: dict | None) -> dict:
    claims = list((response or {}).get("claims") or [])
    facts = case["facts"]
    reasons = [frozen_claim_reason(claim, facts) for claim in claims]
    r1 = [claim_supported_r1(claim, facts) for claim in claims]
    r2 = [claim_supported_r2(claim, facts) for claim in claims]
    denominator = len(claims)
    gold_keys = {canonical_attribute(key) for fact in facts.values() for key in fact}
    covered = [canonical_attribute(claim.get("attribute", "")) in gold_keys for claim in claims]
    return {
        "claim_count": denominator,
        "frozen_failure_reasons": dict(Counter(reasons)),
        "frozen_recomputed": reasons.count("supported") / denominator if denominator else 0.0,
        "relaxed_r1": sum(r1) / denominator if denominator else 0.0,
        "relaxed_r2": sum(r2) / denominator if denominator else 0.0,
        "attribute_key_coverage": sum(covered) / denominator if denominator else 0.0,
    }


def score_a3_deduplicated(case: dict, response: dict | None) -> dict:
    relevance = case["relevance"]
    ranked = list((response or {}).get("ranked_ids") or [])[:5]
    seen, gains, kept = set(), [], []
    for doc_id in ranked:
        if doc_id in seen:
            continue
        seen.add(doc_id)
        kept.append(doc_id)
        gains.append(relevance.get(doc_id, 0))
    gains.extend([0] * (5 - len(gains)))
    ideal = sorted(relevance.values(), reverse=True)[:5]
    denominator = frozen._dcg(ideal)
    grade2_total = sum(value == 2 for value in relevance.values())
    return {
        "kept_ids": kept,
        "gains": gains,
        "ndcg_at_5": frozen._dcg(gains) / denominator if denominator else 0.0,
        "grade2_recall_at_5": (
            sum(relevance.get(doc_id, 0) == 2 for doc_id in kept) / max(1, grade2_total)
        ),
    }


CONVERSION_FIELDS = {
    "invoice": {"total_due_usd"},
    "clinical": {"dose_mg"},
    "shipment": {"weight_kg"},
    "job": {"salary_usd"},
    "incident": {"duration_minutes"},
    "grant": {"maximum_award_usd"},
    "property": {"monthly_rent_usd", "area_sqm"},
    "conference": {"registration_usd"},
    "subscription": {"monthly_total_usd"},
}
CONFLICT_FIELDS = {
    "invoice": {"invoice_id"},
    "clinical": {"trial_id", "enrollment"},
    "shipment": {"destination_city"},
    "job": {"requisition"},
    "incident": {"severity", "affected_users"},
    "policy": {"coverage_limit_usd", "jurisdiction"},
    "grant": {"agency"},
    "subscription": {"plan", "cancelled"},
}


def classify_a2_error(case: dict, field: str) -> str:
    family = case["document_family"]
    if field in CONVERSION_FIELDS.get(family, set()):
        return "unit_scale_conversion"
    if field in CONFLICT_FIELDS.get(family, set()):
        return "conflict_resolution"
    return "field_omission"


def bootstrap_paired_difference(
    first: list[float], second: list[float], *, seed: int, draws: int = 10_000
) -> dict:
    if len(first) != len(second) or not first:
        raise ValueError("paired bootstrap requires equal non-empty vectors")
    differences = [a - b for a, b in zip(first, second)]
    rng = random.Random(seed)
    n = len(differences)
    samples = sorted(sum(differences[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws))
    return {"difference": sum(differences) / n, "ci95": [samples[250], samples[9749]], "draws": draws}


def exact_mcnemar(first: list[bool], second: list[bool]) -> dict:
    if len(first) != len(second):
        raise ValueError("McNemar inputs must be paired")
    first_only = sum(a and not b for a, b in zip(first, second))
    second_only = sum(b and not a for a, b in zip(first, second))
    n = first_only + second_only
    if not n:
        p_value = 1.0
    else:
        k = min(first_only, second_only)
        lower = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
        p_value = min(1.0, 2 * lower)
    return {"first_only": first_only, "second_only": second_only, "p_value": p_value}


def _average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        average = ((i + 1) + j) / 2
        for index in order[i:j]:
            ranks[index] = average
        i = j
    return ranks


def wilcoxon_approx(first: list[float], second: list[float]) -> dict:
    if len(first) != len(second):
        raise ValueError("Wilcoxon inputs must be paired")
    differences = [a - b for a, b in zip(first, second) if a - b != 0]
    if not differences:
        return {"statistic": 0.0, "p_value": 1.0, "n_nonzero": 0, "z": 0.0}
    absolute = [abs(value) for value in differences]
    ranks = _average_ranks(absolute)
    w_plus = sum(rank for rank, value in zip(ranks, differences) if value > 0)
    w_minus = sum(rank for rank, value in zip(ranks, differences) if value < 0)
    n = len(differences)
    mean = n * (n + 1) / 4
    tie_counts = Counter(absolute)
    tie_correction = sum(count**3 - count for count in tie_counts.values())
    variance = (n * (n + 1) * (2 * n + 1) - tie_correction / 2) / 24
    if variance <= 0:
        return {"statistic": min(w_plus, w_minus), "p_value": 1.0, "n_nonzero": n, "z": 0.0}
    z = (w_plus - mean) / math.sqrt(variance)
    p_value = math.erfc(abs(z) / math.sqrt(2))
    return {"statistic": min(w_plus, w_minus), "p_value": p_value, "n_nonzero": n, "z": z}


def holm_adjust(items: Iterable[tuple[str, float]]) -> dict[str, float]:
    ordered = sorted(items, key=lambda item: (item[1], item[0]))
    m = len(ordered)
    adjusted, running = {}, 0.0
    for index, (key, p_value) in enumerate(ordered):
        running = max(running, min(1.0, (m - index) * p_value))
        adjusted[key] = running
    return adjusted


def comparison_seed(task: str, view: str, pair: str) -> int:
    digest = hashlib.sha256(f"{task}|{view}|{pair}".encode("ascii")).hexdigest()
    return (20261118 + int(digest[:8], 16)) % (2**32)
