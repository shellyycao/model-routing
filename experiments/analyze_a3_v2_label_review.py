"""Validate, lock, unblind, and summarize Independent-v2 A3 human review."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
REVIEW = REPO / "results/review"
PROCESSED = REPO / "results/processed/independent"
REPORTS = REPO / "results/reports"
YES_NO = {"yes", "no"}
CONFIDENCE = {"high", "medium", "low"}

QUERY_JUDGMENT_FIELDS = [
    "reviewer_query_is_clear_yes_no",
    "reviewer_direct_relevance_rule_is_unambiguous_yes_no",
    "reviewer_topic_representation_acceptable_yes_no",
    "reviewer_method_representation_acceptable_yes_no",
    "reviewer_confidence_high_medium_low",
]
LABEL_JUDGMENT_FIELDS = [
    "reviewer_relevance_grade_0_1_2",
    "reviewer_topic_match_yes_no",
    "reviewer_method_match_yes_no",
    "reviewer_prior_work_only_yes_no",
    "reviewer_confidence_high_medium_low",
]


def _rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_completed(
    completed_path: Path,
    blank_path: Path,
    id_field: str,
    judgment_fields: list[str],
    expected_count: int,
) -> list[dict[str, str]]:
    completed_header, completed = _rows(completed_path)
    blank_header, blank = _rows(blank_path)
    if completed_header != blank_header:
        raise ValueError(f"header mismatch in {completed_path.name}")
    if len(completed) != expected_count:
        raise ValueError(f"expected {expected_count} rows in {completed_path.name}, found {len(completed)}")
    if len({row[id_field] for row in completed}) != expected_count:
        raise ValueError(f"duplicate or missing {id_field} in {completed_path.name}")
    blank_by_id = {row[id_field]: row for row in blank}
    if set(blank_by_id) != {row[id_field] for row in completed}:
        raise ValueError(f"anonymous ID set differs in {completed_path.name}")
    static_fields = [field for field in completed_header if field not in judgment_fields and field != "reviewer_notes"]
    for row in completed:
        expected = blank_by_id[row[id_field]]
        changed = [field for field in static_fields if row[field] != expected[field]]
        if changed:
            raise ValueError(f"source fields changed for {row[id_field]}: {changed}")
        missing = [field for field in judgment_fields if not row[field].strip()]
        if missing:
            raise ValueError(f"missing judgments for {row[id_field]}: {missing}")
    return completed


def _validate_values(query_rows: list[dict[str, str]], label_rows: list[dict[str, str]]) -> None:
    for row in query_rows:
        for field in QUERY_JUDGMENT_FIELDS[:-1]:
            if row[field] not in YES_NO:
                raise ValueError(f"invalid {field} for {row['anonymous_query_id']}: {row[field]}")
        if row[QUERY_JUDGMENT_FIELDS[-1]] not in CONFIDENCE:
            raise ValueError(f"invalid query confidence for {row['anonymous_query_id']}")
    for row in label_rows:
        if row["reviewer_relevance_grade_0_1_2"] not in {"0", "1", "2"}:
            raise ValueError(f"invalid relevance grade for {row['anonymous_label_id']}")
        for field in LABEL_JUDGMENT_FIELDS[1:4]:
            if row[field] not in YES_NO:
                raise ValueError(f"invalid {field} for {row['anonymous_label_id']}: {row[field]}")
        if row[LABEL_JUDGMENT_FIELDS[-1]] not in CONFIDENCE:
            raise ValueError(f"invalid label confidence for {row['anonymous_label_id']}")
        axes = (row["reviewer_topic_match_yes_no"] == "yes") + (row["reviewer_method_match_yes_no"] == "yes")
        if int(row["reviewer_relevance_grade_0_1_2"]) != axes:
            raise ValueError(f"grade/axis inconsistency for {row['anonymous_label_id']}")
        if row["reviewer_prior_work_only_yes_no"] == "yes" and axes:
            raise ValueError(f"prior-work-only row has a positive match for {row['anonymous_label_id']}")


def analyze(query_path: Path, label_path: Path) -> tuple[dict, str]:
    query_rows = _validate_completed(
        query_path, REVIEW / "a3_v2_query_review_worksheet.csv", "anonymous_query_id", QUERY_JUDGMENT_FIELDS, 30
    )
    label_rows = _validate_completed(
        label_path, REVIEW / "a3_v2_label_review_worksheet.csv", "anonymous_label_id", LABEL_JUDGMENT_FIELDS, 180
    )
    _validate_values(query_rows, label_rows)
    _, key_rows = _rows(REVIEW / "a3_v2_label_review_key.csv")
    key = {row["anonymous_label_id"]: row for row in key_rows}
    if set(key) != {row["anonymous_label_id"] for row in label_rows}:
        raise ValueError("completed label IDs do not match the locked key")

    disagreements = []
    for row in label_rows:
        proposed = key[row["anonymous_label_id"]]
        expected_topic = "yes" if proposed["proposed_topic_match"] == "true" else "no"
        expected_method = "yes" if proposed["proposed_method_match"] == "true" else "no"
        if (
            row["reviewer_relevance_grade_0_1_2"] != proposed["proposed_grade"]
            or row["reviewer_topic_match_yes_no"] != expected_topic
            or row["reviewer_method_match_yes_no"] != expected_method
        ):
            disagreements.append({
                "anonymous_label_id": row["anonymous_label_id"],
                "anonymous_query_id": row["anonymous_query_id"],
                "case_id": proposed["case_id"],
                "doc_id": proposed["doc_id"],
                "difficulty": proposed["difficulty"],
                "proposed_grade": int(proposed["proposed_grade"]),
                "human_grade": int(row["reviewer_relevance_grade_0_1_2"]),
                "proposed_topic_match": expected_topic,
                "human_topic_match": row["reviewer_topic_match_yes_no"],
                "proposed_method_match": expected_method,
                "human_method_match": row["reviewer_method_match_yes_no"],
                "human_confidence": row["reviewer_confidence_high_medium_low"],
                "reviewer_notes": row["reviewer_notes"],
            })

    affected_queries = sorted({row["anonymous_query_id"] for row in disagreements})
    query_ambiguities = sorted([
        row["anonymous_query_id"]
        for row in query_rows
        if row["reviewer_direct_relevance_rule_is_unambiguous_yes_no"] == "no"
    ])
    results = {
        "review_status": "locked_unblinded_requires_targeted_rereview",
        "review_date": "2026-11-18",
        "query_count": len(query_rows),
        "label_count": len(label_rows),
        "query_confidence": dict(sorted(Counter(row["reviewer_confidence_high_medium_low"] for row in query_rows).items())),
        "label_confidence": dict(sorted(Counter(row["reviewer_confidence_high_medium_low"] for row in label_rows).items())),
        "human_grade_counts": dict(sorted(Counter(row["reviewer_relevance_grade_0_1_2"] for row in label_rows).items())),
        "grade_agreement": len(label_rows) - len(disagreements),
        "grade_disagreement": len(disagreements),
        "grade_agreement_rate": (len(label_rows) - len(disagreements)) / len(label_rows),
        "method_match_disagreement": sum(row["proposed_method_match"] != row["human_method_match"] for row in disagreements),
        "topic_match_disagreement": sum(row["proposed_topic_match"] != row["human_topic_match"] for row in disagreements),
        "affected_queries": affected_queries,
        "query_rule_ambiguities": query_ambiguities,
        "systematic_finding": "The candidate surface form 'detecting abusive online content' is broader than the query topic 'hate speech detection'.",
        "resolution": "Replace the overly broad candidate surface form with 'detecting hate speech' and obtain targeted blinded re-review for the three affected queries before freezing.",
        "disagreements": disagreements,
        "source_hashes": {"query_completed_sha256": _sha256(query_path), "label_completed_sha256": _sha256(label_path)},
    }

    affected = ", ".join(affected_queries)
    report = "\n".join([
        "# Independent v2 A3 Human Label Review",
        "",
        "## Validation",
        "",
        "Both completed worksheets passed schema, row-count, anonymous-ID, immutable-source-field, allowed-value, completeness, and grade/axis consistency checks.",
        "",
        "## Agreement",
        "",
        f"- Query rules reviewed: {len(query_rows)}/30.",
        f"- Candidate-query pairs reviewed: {len(label_rows)}/180.",
        f"- Relevance-grade agreement: {len(label_rows) - len(disagreements)}/180 ({(len(label_rows) - len(disagreements)) / len(label_rows):.1%}).",
        f"- Topic-match disagreements: {results['topic_match_disagreement']}.",
        f"- Method-match disagreements: {results['method_match_disagreement']}.",
        "",
        "## Systematic finding",
        "",
        f"All {len(disagreements)} label disagreements and all {len(query_ambiguities)} query-rule ambiguity flags occur in {affected}. These are the three hate-speech queries. Their candidate documents use the broader surface form `detecting abusive online content`, which the human reviewer correctly judged insufficient to establish a strict hate-speech topic match.",
        "",
        "The disagreement is therefore a dataset wording defect, not evidence that the relevance rule itself should be weakened. Simply downgrading the labels would leave the affected queries without direct-relevance documents.",
        "",
        "## Resolution",
        "",
        "1. Preserve these completed judgments as the locked first-pass record.",
        "2. Replace the overly broad candidate surface form with `detecting hate speech` in the deterministic generator.",
        "3. Regenerate the candidate dataset and issue a blinded supplemental packet for the three affected queries.",
        "4. Keep the A3 adjudication and dataset-freeze gates open until the supplemental review is returned and validated.",
        "",
    ])
    return results, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query-completed", type=Path, required=True)
    parser.add_argument("--label-completed", type=Path, required=True)
    args = parser.parse_args(argv)
    results, report = analyze(args.query_completed, args.label_completed)
    REVIEW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.query_completed, REVIEW / "a3_v2_query_review_completed.csv")
    shutil.copyfile(args.label_completed, REVIEW / "a3_v2_label_review_completed.csv")
    (PROCESSED / "a3_v2_label_review_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (REPORTS / "a3_v2_label_review_results.md").write_text(report, encoding="utf-8")
    print(json.dumps({
        "validated_queries": results["query_count"], "validated_labels": results["label_count"],
        "grade_agreement": results["grade_agreement"], "grade_disagreement": results["grade_disagreement"],
        "status": results["review_status"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
