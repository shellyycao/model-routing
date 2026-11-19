from decimal import Decimal

import pytest

from experiments import analyze_diagnostics_posthoc as diag


def test_numpy_patch_is_narrow_and_precedes_saved_code():
    patched = diag.patched_code("import json\njson.dump({'x': 1}, open('/tmp/x', 'w'))")
    assert patched.startswith("# POST-HOC DIAGNOSTIC PATCH")
    assert 'module == "numpy"' in patched
    assert ".item()" not in patched  # implementation calls the captured method; prose is not executable repair
    assert "_diag_json.dump = _diag_dump" in patched
    assert patched.endswith("json.dump({'x': 1}, open('/tmp/x', 'w'))")


def test_reported_precision_rounding_uses_literal_decimal_places():
    assert diag.rounded_match(Decimal("1.3"), 1.3224)
    assert diag.rounded_match(Decimal("3.5"), 3.458)
    assert not diag.rounded_match(Decimal("1.2"), 1.3224)
    assert diag.decimal_places(Decimal("1.30")) == 2


def test_int64_inventory_covers_both_groups_and_analysis_and_cleaning():
    rows = diag.int64_candidates()
    assert len(rows) == 63
    assert sum(r["stage"] == "analysis" for r in rows) == 49
    assert sum(r["stage"] == "cleaning" for r in rows) == 14
    assert sum(r["model_name"] == "GLM 5" and r["stage"] == "analysis" for r in rows) == 35
    assert sum(r["model_name"] == "GLM 5" and r["part"] == "A" for r in rows) == 4


def test_replay_fails_fast_without_pinned_image_and_never_falls_back(monkeypatch, tmp_path):
    seen = {}

    class FakeExecutor:
        def __init__(self, image):
            seen["image"] = image

        def availability(self):
            return False, "image missing"

    monkeypatch.setattr(diag, "DockerExecutor", FakeExecutor)
    with pytest.raises(RuntimeError, match="pinned diagnostic sandbox unavailable: image missing"):
        diag.run_replays(tmp_path / "replays")
    assert seen["image"] == diag.PINNED_IMAGE


def test_rounding_and_q7_are_separate_sensitivities():
    result = diag.reporting_rounding()
    candidates = result["derived_values_only_candidates"]
    assert len(candidates) == 15
    assert sum(r["recoverable"] for r in candidates) == 15
    assert len(result["known_q7_v31_false_rejects"]) == 30
    rounding_ids = {r["run_id"] for r in candidates if r["recoverable"]}
    q7_ids = {r["run_id"] for r in result["known_q7_v31_false_rejects"]}
    assert rounding_ids.isdisjoint(q7_ids)


def test_truncation_uses_invocation_and_frozen_failure_fields():
    result = diag.truncation()
    assert result["original_4096"]["n_distinct_workflows_affected"] == 5
    assert result["price_matched_16384"]["n_distinct_workflows_affected"] == 0
    assert sum(v["stop_reason_max_tokens"] for v in
               result["original_4096"]["per_model_stage"].values()) >= 5


def test_cost_sanity_matches_saved_cp7f_numbers_and_exposes_gap_distribution():
    result = diag.cost_sanity()
    assert result["token_cost_direction"] == {"matches": 64, "n": 64}
    assert result["naive_unit_price_direction"] == {"matches": 56, "n": 64}
    assert result["abs_actual_delta_usd"]["min"] > 0
    assert result["abs_actual_delta_usd"]["median"] > 0.05
    assert result["direction_counts"]["actual"] == {
        "alternative more expensive": 56,
        "alternative cheaper": 8,
    }

