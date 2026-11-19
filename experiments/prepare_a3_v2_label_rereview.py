"""Prepare the blinded supplemental review for corrected A3 hate-speech cases."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from experiments.prepare_a3_v2_label_review import KEY_FIELDS, LABEL_FIELDS, QUERY_FIELDS, _write_csv


REPO = Path(__file__).resolve().parents[1]
CASES = REPO / "datasets/independent_v2/a3/cases"
OUT = REPO / "results/review"
AFFECTED_QUERY_IDS = ["A3Q-005", "A3Q-015", "A3Q-025"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_packet() -> tuple[list[dict], list[dict], list[dict], dict]:
    with (OUT / "a3_v2_label_review_key.csv").open(newline="", encoding="utf-8") as handle:
        original_key = list(csv.DictReader(handle))
    selected = [row for row in original_key if row["anonymous_query_id"] in AFFECTED_QUERY_IDS]
    if len(selected) != 18:
        raise ValueError(f"expected 18 original review rows for affected queries, found {len(selected)}")

    query_rows: list[dict] = []
    label_rows: list[dict] = []
    key_rows: list[dict] = []
    for query_index, original_query_id in enumerate(AFFECTED_QUERY_IDS, 1):
        key_subset = [row for row in selected if row["anonymous_query_id"] == original_query_id]
        case_ids = {row["case_id"] for row in key_subset}
        if len(key_subset) != 6 or len(case_ids) != 1:
            raise ValueError(f"bad original review subset for {original_query_id}")
        case_id = next(iter(case_ids))
        case = json.loads((CASES / f"{case_id}.json").read_text(encoding="utf-8"))
        query_id = f"A3RQ-{query_index:03d}"
        query_rows.append({
            "anonymous_query_id": query_id,
            "review_batch": 1,
            "query_text": case["query"]["text"],
            "query_topic": case["query"]["topic"],
            "query_method": case["query"]["method"],
            "reviewer_query_is_clear_yes_no": "",
            "reviewer_direct_relevance_rule_is_unambiguous_yes_no": "",
            "reviewer_topic_representation_acceptable_yes_no": "",
            "reviewer_method_representation_acceptable_yes_no": "",
            "reviewer_confidence_high_medium_low": "",
            "reviewer_notes": "",
        })
        candidates = {row["doc_id"]: row for row in case["candidates"]}
        for original in sorted(key_subset, key=lambda row: row["anonymous_label_id"]):
            candidate = candidates[original["doc_id"]]
            label_id = f"A3RL-{len(label_rows) + 1:03d}"
            label_rows.append({
                "anonymous_label_id": label_id,
                "anonymous_query_id": query_id,
                "review_batch": 1,
                "query_text": case["query"]["text"],
                "candidate_title": candidate["title"],
                "candidate_authors": candidate["authors"],
                "candidate_year": candidate["year"],
                "candidate_abstract": candidate["abstract"],
                "reviewer_relevance_grade_0_1_2": "",
                "reviewer_topic_match_yes_no": "",
                "reviewer_method_match_yes_no": "",
                "reviewer_prior_work_only_yes_no": "",
                "reviewer_confidence_high_medium_low": "",
                "reviewer_notes": "",
            })
            rationale = case["label_rationale"][original["doc_id"]]
            key_rows.append({
                "anonymous_label_id": label_id,
                "anonymous_query_id": query_id,
                "case_id": case_id,
                "doc_id": original["doc_id"],
                "difficulty": case["difficulty"],
                "proposed_grade": rationale["grade"],
                "proposed_topic_match": str(rationale["topic_match"]).lower(),
                "proposed_method_match": str(rationale["method_match"]).lower(),
                "selection_stratum": original["selection_stratum"],
                "negative_subtype": original["negative_subtype"],
                "source_label_status": "candidate_pending_human_review",
                "original_anonymous_label_id": original["anonymous_label_id"],
                "original_anonymous_query_id": original_query_id,
            })

    manifest = {
        "protocol": "independent-v2 A3 targeted blinded rereview after topic-surface correction",
        "dataset_version": "independent-v2-candidate-0.2",
        "query_count": len(query_rows),
        "label_count": len(label_rows),
        "affected_original_query_ids": AFFECTED_QUERY_IDS,
        "correction": "detecting abusive online content -> detecting hate speech",
        "warning": "Do not open or join the rereview key until both supplemental worksheets are complete and locked.",
    }
    return query_rows, label_rows, key_rows, manifest


def main() -> int:
    query_rows, label_rows, key_rows, manifest = build_packet()
    query_path = OUT / "a3_v2_query_rereview_worksheet.csv"
    label_path = OUT / "a3_v2_label_rereview_worksheet.csv"
    key_path = OUT / "a3_v2_label_rereview_key.csv"
    manifest_path = OUT / "a3_v2_label_rereview_manifest.json"
    rereview_key_fields = KEY_FIELDS + ["original_anonymous_label_id", "original_anonymous_query_id"]
    _write_csv(query_path, QUERY_FIELDS, query_rows)
    _write_csv(label_path, LABEL_FIELDS, label_rows)
    _write_csv(key_path, rereview_key_fields, key_rows)
    manifest.update({
        "query_worksheet_sha256": _sha256(query_path),
        "label_worksheet_sha256": _sha256(label_path),
        "key_sha256": _sha256(key_path),
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "query_worksheet": str(query_path.relative_to(REPO)),
        "label_worksheet": str(label_path.relative_to(REPO)),
        "queries": len(query_rows),
        "labels": len(label_rows),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
