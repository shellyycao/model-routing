"""Tests for the targeted A3 v2 rereview packet and corrected surface form."""

from __future__ import annotations

from collections import Counter

from experiments.prepare_a3_v2_label_rereview import build_packet


def test_targeted_rereview_packet_covers_three_balanced_query_sets():
    query_rows, label_rows, key_rows, manifest = build_packet()
    assert len(query_rows) == 3
    assert len(label_rows) == len(key_rows) == 18
    assert Counter(row["anonymous_query_id"] for row in label_rows) == {
        "A3RQ-001": 6, "A3RQ-002": 6, "A3RQ-003": 6,
    }
    for row in label_rows:
        assert "abusive online content" not in row["candidate_title"].lower()
        assert "abusive online content" not in row["candidate_abstract"].lower()
        assert not row["reviewer_relevance_grade_0_1_2"]
    assert sum("detecting hate speech" in row["candidate_abstract"].lower() for row in label_rows) == 15
    assert Counter(row["proposed_grade"] for row in key_rows) == {2: 12, 1: 3, 0: 3}
    assert manifest["dataset_version"] == "independent-v2-candidate-0.2"
