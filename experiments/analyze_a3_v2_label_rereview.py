"""Validate and incorporate the targeted Independent-v2 A3 human rereview."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

from experiments.analyze_a3_v2_label_review import (
    LABEL_JUDGMENT_FIELDS,
    QUERY_JUDGMENT_FIELDS,
    _validate_completed,
    _validate_values,
)


REPO = Path(__file__).resolve().parents[1]
REVIEW = REPO / "results/review"
PROCESSED = REPO / "results/processed/independent"
REPORTS = REPO / "results/reports"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(query_path: Path, label_path: Path) -> tuple[dict, str]:
    query_rows = _validate_completed(
        query_path,
        REVIEW / "a3_v2_query_rereview_worksheet.csv",
        "anonymous_query_id",
        QUERY_JUDGMENT_FIELDS,
        3,
    )
    label_rows = _validate_completed(
        label_path,
        REVIEW / "a3_v2_label_rereview_worksheet.csv",
        "anonymous_label_id",
        LABEL_JUDGMENT_FIELDS,
        18,
    )
    _validate_values(query_rows, label_rows)
    key_rows = _rows(REVIEW / "a3_v2_label_rereview_key.csv")
    key = {row["anonymous_label_id"]: row for row in key_rows}
    if set(key) != {row["anonymous_label_id"] for row in label_rows}:
        raise ValueError("completed rereview label IDs do not match the locked key")

    disagreements = []
    for row in label_rows:
        proposed = key[row["anonymous_label_id"]]
        expected_topic = "yes" if proposed["proposed_topic_match"] == "true" else "no"
        expected_method = "yes" if proposed["proposed_method_match"] == "true" else "no"
        differences = {
            "grade": row["reviewer_relevance_grade_0_1_2"] != proposed["proposed_grade"],
            "topic": row["reviewer_topic_match_yes_no"] != expected_topic,
            "method": row["reviewer_method_match_yes_no"] != expected_method,
        }
        if any(differences.values()):
            disagreements.append({
                "anonymous_label_id": row["anonymous_label_id"],
                "case_id": proposed["case_id"],
                "doc_id": proposed["doc_id"],
                "differences": differences,
                "proposed_grade": int(proposed["proposed_grade"]),
                "human_grade": int(row["reviewer_relevance_grade_0_1_2"]),
                "reviewer_notes": row["reviewer_notes"],
            })

    ambiguous_queries = sorted(
        row["anonymous_query_id"]
        for row in query_rows
        if row["reviewer_direct_relevance_rule_is_unambiguous_yes_no"] != "yes"
    )
    complete = not disagreements and not ambiguous_queries
    results = {
        "review_status": "complete_locked_unblinded" if complete else "unresolved",
        "review_date": "2026-11-18",
        "dataset_version": "independent-v2-candidate-0.2",
        "query_count": len(query_rows),
        "label_count": len(label_rows),
        "query_rule_ambiguities": ambiguous_queries,
        "grade_agreement": len(label_rows) - len(disagreements),
        "grade_disagreement": len(disagreements),
        "human_grade_counts": dict(sorted(Counter(row["reviewer_relevance_grade_0_1_2"] for row in label_rows).items())),
        "query_confidence": dict(sorted(Counter(row["reviewer_confidence_high_medium_low"] for row in query_rows).items())),
        "label_confidence": dict(sorted(Counter(row["reviewer_confidence_high_medium_low"] for row in label_rows).items())),
        "disagreements": disagreements,
        "source_hashes": {
            "query_completed_sha256": _sha256(query_path),
            "label_completed_sha256": _sha256(label_path),
        },
    }
    report = "\n".join([
        "# Independent v2 A3 Targeted Human Rereview",
        "",
        "## Validation",
        "",
        "Both supplemental worksheets passed schema, row-count, anonymous-ID, immutable-source-field, allowed-value, completeness, and grade/axis consistency checks.",
        "",
        "## Result",
        "",
        f"- Corrected query rules accepted as unambiguous: {len(query_rows) - len(ambiguous_queries)}/{len(query_rows)}.",
        f"- Corrected candidate labels agreeing with the proposed labels: {len(label_rows) - len(disagreements)}/{len(label_rows)}.",
        f"- Remaining disagreements: {len(disagreements)}.",
        "",
        "The targeted rereview confirms that `detecting hate speech` is an acceptable surface form for `hate speech detection`. Combined with the locked first pass, the required A3 human label adjudication is complete." if complete else "The A3 human label adjudication remains open.",
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
    shutil.copyfile(args.query_completed, REVIEW / "a3_v2_query_rereview_completed.csv")
    shutil.copyfile(args.label_completed, REVIEW / "a3_v2_label_rereview_completed.csv")
    (PROCESSED / "a3_v2_label_rereview_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (REPORTS / "a3_v2_label_rereview_results.md").write_text(report, encoding="utf-8")
    print(json.dumps({
        "validated_queries": results["query_count"],
        "validated_labels": results["label_count"],
        "grade_agreement": results["grade_agreement"],
        "status": results["review_status"],
    }, indent=2))
    if results["review_status"] != "complete_locked_unblinded":
        raise SystemExit("targeted rereview has unresolved items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
