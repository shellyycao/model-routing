"""Create the deterministic, blinded Independent-v2 A3 label-review packet.

This offline preparation step never calls a model or changes the candidate dataset.
Human judgments remain blank by construction.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CASES = REPO / "datasets/independent_v2/a3/cases"
OUT = REPO / "results/review"
SEED = 20261118
HISTORICAL_SOURCE_CASE_TREE_SHA256 = "47f0c77e008594377699b36f85c49320ccfae4525befa9b4fdda255e1c4463b0"
HISTORICAL_LABEL_STATUS = "candidate_pending_human_review"

QUERY_FIELDS = [
    "anonymous_query_id", "review_batch", "query_text", "query_topic", "query_method",
    "reviewer_query_is_clear_yes_no", "reviewer_direct_relevance_rule_is_unambiguous_yes_no",
    "reviewer_topic_representation_acceptable_yes_no", "reviewer_method_representation_acceptable_yes_no",
    "reviewer_confidence_high_medium_low", "reviewer_notes",
]

LABEL_FIELDS = [
    "anonymous_label_id", "anonymous_query_id", "review_batch", "query_text", "candidate_title",
    "candidate_authors", "candidate_year", "candidate_abstract", "reviewer_relevance_grade_0_1_2",
    "reviewer_topic_match_yes_no", "reviewer_method_match_yes_no", "reviewer_prior_work_only_yes_no",
    "reviewer_confidence_high_medium_low", "reviewer_notes",
]

KEY_FIELDS = [
    "anonymous_label_id", "anonymous_query_id", "case_id", "doc_id", "difficulty", "proposed_grade",
    "proposed_topic_match", "proposed_method_match", "selection_stratum", "negative_subtype",
    "source_label_status",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _negative_subtype(candidate: dict) -> str:
    abstract = candidate["abstract"].lower()
    if "prior work discussed" in abstract and "different problem" in abstract:
        return "prior_work_only"
    return "ordinary_unrelated"


def _choose_review_docs(case: dict, rng: random.Random) -> list[tuple[dict, str, str]]:
    candidates = {candidate["doc_id"]: candidate for candidate in case["candidates"]}
    by_grade = {
        grade: sorted(doc_id for doc_id, value in case["relevance"].items() if value == grade)
        for grade in (0, 1, 2)
    }
    selected: list[tuple[dict, str, str]] = [
        (candidates[doc_id], "all_proposed_grade_2", "not_applicable") for doc_id in by_grade[2]
    ]
    grade_one_id = rng.choice(by_grade[1])
    selected.append((candidates[grade_one_id], "sampled_proposed_grade_1", "not_applicable"))
    prior_work_ids = [doc_id for doc_id in by_grade[0] if _negative_subtype(candidates[doc_id]) == "prior_work_only"]
    grade_zero_id = rng.choice(prior_work_ids or by_grade[0])
    grade_zero_candidate = candidates[grade_zero_id]
    selected.append((grade_zero_candidate, "sampled_proposed_grade_0", _negative_subtype(grade_zero_candidate)))
    rng.shuffle(selected)
    return selected


def build_packet() -> tuple[list[dict], list[dict], list[dict], dict]:
    case_paths = sorted(CASES.glob("*.json"))
    cases = [json.loads(path.read_text(encoding="utf-8")) for path in case_paths]
    if len(cases) != 30:
        raise ValueError(f"expected 30 A3 cases, found {len(cases)}")

    query_rows: list[dict] = []
    label_rows: list[dict] = []
    key_rows: list[dict] = []
    for case_index, case in enumerate(cases, 1):
        query_id = f"A3Q-{case_index:03d}"
        batch = 1 + ((case_index - 1) % 3)
        query_rows.append({
            "anonymous_query_id": query_id, "review_batch": batch, "query_text": case["query"]["text"],
            "query_topic": case["query"]["topic"], "query_method": case["query"]["method"],
            "reviewer_query_is_clear_yes_no": "", "reviewer_direct_relevance_rule_is_unambiguous_yes_no": "",
            "reviewer_topic_representation_acceptable_yes_no": "", "reviewer_method_representation_acceptable_yes_no": "",
            "reviewer_confidence_high_medium_low": "", "reviewer_notes": "",
        })
        rng = random.Random(SEED + case_index)
        for candidate, selection_stratum, negative_subtype in _choose_review_docs(case, rng):
            # Preserve the evidence exactly as shown in the locked first-pass packet.
            # The live dataset was corrected only after that review identified this
            # overly broad surface form.
            candidate = dict(candidate)
            for field in ("title", "abstract"):
                candidate[field] = candidate[field].replace("detecting hate speech", "detecting abusive online content")
            label_id = f"A3L-{len(label_rows) + 1:03d}"
            label_rows.append({
                "anonymous_label_id": label_id, "anonymous_query_id": query_id, "review_batch": batch,
                "query_text": case["query"]["text"], "candidate_title": candidate["title"],
                "candidate_authors": candidate["authors"], "candidate_year": candidate["year"],
                "candidate_abstract": candidate["abstract"], "reviewer_relevance_grade_0_1_2": "",
                "reviewer_topic_match_yes_no": "", "reviewer_method_match_yes_no": "",
                "reviewer_prior_work_only_yes_no": "", "reviewer_confidence_high_medium_low": "",
                "reviewer_notes": "",
            })
            rationale = case["label_rationale"][candidate["doc_id"]]
            key_rows.append({
                "anonymous_label_id": label_id, "anonymous_query_id": query_id, "case_id": case["case_id"],
                "doc_id": candidate["doc_id"], "difficulty": case["difficulty"],
                "proposed_grade": rationale["grade"], "proposed_topic_match": str(rationale["topic_match"]).lower(),
                "proposed_method_match": str(rationale["method_match"]).lower(),
                "selection_stratum": selection_stratum, "negative_subtype": negative_subtype,
                "source_label_status": HISTORICAL_LABEL_STATUS,
            })

    query_rows.sort(key=lambda row: (int(row["review_batch"]), row["anonymous_query_id"]))
    label_rows.sort(key=lambda row: (int(row["review_batch"]), row["anonymous_query_id"], row["anonymous_label_id"]))
    key_rows.sort(key=lambda row: row["anonymous_label_id"])
    manifest = {
        "protocol": "independent-v2 A3 blinded relevance-label adjudication", "seed": SEED,
        "query_count": len(query_rows), "label_count": len(label_rows), "review_batches": 3,
        "sampling": {
            "per_query": {"all_proposed_grade_2": 4, "sampled_proposed_grade_1": 1, "sampled_proposed_grade_0": 1},
            "grade_0_rule": "prefer a prior-work-only hard negative when available; otherwise sample an ordinary unrelated candidate",
        },
        "expected_counts": {
            "all_proposed_grade_2": 120, "sampled_proposed_grade_1": 30, "sampled_proposed_grade_0": 30,
            "prior_work_only_grade_0": 20, "ordinary_unrelated_grade_0": 10,
        },
        "source_case_tree_sha256": HISTORICAL_SOURCE_CASE_TREE_SHA256,
        "warning": "Do not open or join the key until both human worksheets are complete and locked.",
    }
    return query_rows, label_rows, key_rows, manifest


def main() -> int:
    query_rows, label_rows, key_rows, manifest = build_packet()
    OUT.mkdir(parents=True, exist_ok=True)
    query_path = OUT / "a3_v2_query_review_worksheet.csv"
    label_path = OUT / "a3_v2_label_review_worksheet.csv"
    key_path = OUT / "a3_v2_label_review_key.csv"
    manifest_path = OUT / "a3_v2_label_review_manifest.json"
    _write_csv(query_path, QUERY_FIELDS, query_rows)
    _write_csv(label_path, LABEL_FIELDS, label_rows)
    _write_csv(key_path, KEY_FIELDS, key_rows)
    manifest.update({
        "query_worksheet_sha256": _sha256(query_path), "label_worksheet_sha256": _sha256(label_path),
        "key_sha256": _sha256(key_path),
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "query_worksheet": str(query_path.relative_to(REPO)),
        "label_worksheet": str(label_path.relative_to(REPO)), "queries": len(query_rows), "labels": len(label_rows),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
