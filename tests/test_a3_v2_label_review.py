"""Tests for the blinded Independent-v2 A3 label-review packet."""

from __future__ import annotations

from collections import Counter, defaultdict

from experiments.prepare_a3_v2_label_review import build_packet


def test_review_packet_is_complete_blinded_and_balanced():
    query_rows, label_rows, key_rows, manifest = build_packet()
    assert len(query_rows) == 30
    assert len(label_rows) == len(key_rows) == 180
    assert Counter(row["review_batch"] for row in query_rows) == {1: 10, 2: 10, 3: 10}
    assert Counter(row["review_batch"] for row in label_rows) == {1: 60, 2: 60, 3: 60}
    per_query = defaultdict(list)
    for row in key_rows:
        per_query[row["anonymous_query_id"]].append(row)
    assert all(Counter(row["proposed_grade"] for row in rows) == {2: 4, 1: 1, 0: 1} for rows in per_query.values())
    assert Counter(row["selection_stratum"] for row in key_rows) == {
        "all_proposed_grade_2": 120, "sampled_proposed_grade_1": 30, "sampled_proposed_grade_0": 30,
    }
    grade_zero = [row for row in key_rows if row["proposed_grade"] == 0]
    assert Counter(row["negative_subtype"] for row in grade_zero) == {
        "prior_work_only": 20, "ordinary_unrelated": 10,
    }
    forbidden = {"case_id", "doc_id", "difficulty", "proposed_grade", "selection_stratum"}
    assert forbidden.isdisjoint(query_rows[0])
    assert forbidden.isdisjoint(label_rows[0])
    assert all(not row["reviewer_query_is_clear_yes_no"] for row in query_rows)
    assert all(not row["reviewer_relevance_grade_0_1_2"] for row in label_rows)
    assert manifest["query_count"] == 30
    assert manifest["label_count"] == 180
