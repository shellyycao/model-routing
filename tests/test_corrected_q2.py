import json

import pytest

from experiments import analyze_corrected_q2 as q2


@pytest.fixture(scope="module")
def result():
    return q2.analyze()


def test_continuation_integrity_and_overlap_are_explicit(result):
    audit = result["integrity_audit"]
    assert audit["status"] == "pass"
    assert audit["continuation_records"] == audit["distinct_continued_from"] == 40
    assert audit["continuation_invocations"] == 40
    assert audit["continuation_void_infra"] == 0
    assert audit["cleaning_recoveries_with_observed_downstream"] == 11
    assert audit["cleaning_and_analysis_recovery_overlap"] == 1
    assert audit["cleaning_recovery_downstream_saw_failed_label"] is True
    assert audit["ledger"]["spent_usd_priced"] == pytest.approx(1.3973876)
    assert audit["ledger"]["failed_attempts"] == 0
    assert audit["ledger"]["pending"] == {}


def test_main_grid_frozen_and_corrected_views_are_side_by_side(result):
    original = result["model_groups"]["original_4096"]
    price = result["model_groups"]["price_matched_16384"]
    assert (original["main_grid"]["frozen_v3"]["n_feasible"],
            original["main_grid"]["corrected_v3"]["n_feasible"]) == (17, 25)
    assert (original["main_grid"]["frozen_v31"]["n_feasible"],
            original["main_grid"]["corrected_v31"]["n_feasible"]) == (21, 30)
    assert (price["main_grid"]["frozen_v3"]["n_feasible"],
            price["main_grid"]["corrected_v3"]["n_feasible"]) == (41, 52)
    assert (price["main_grid"]["frozen_v31"]["n_feasible"],
            price["main_grid"]["corrected_v31"]["n_feasible"]) == (53, 70)
    assert all(group["main_grid"][view]["n"] == 108
               for group in (original, price)
               for view in ("frozen_v3", "corrected_v3", "frozen_v31", "corrected_v31"))


def test_single_cross_denominators_changes_and_first_failures(result):
    expected = {
        "original_4096": {"single": (2, 2), "cross": (15, 23), "changed": 9},
        "price_matched_16384": {"single": (3, 6), "cross": (38, 46), "changed": 17},
    }
    for group, values in expected.items():
        data = result["model_groups"][group]
        single = data["single_model_main_grid"]
        cross = data["cross_model_main_grid"]
        assert single["frozen_v3"]["n"] == single["corrected_v3"]["n"] == 12
        assert cross["frozen_v3"]["n"] == cross["corrected_v3"]["n"] == 96
        assert (single["frozen_v3"]["n_feasible"], single["corrected_v3"]["n_feasible"]) == values["single"]
        assert (cross["frozen_v3"]["n_feasible"], cross["corrected_v3"]["n_feasible"]) == values["cross"]
        assert len(data["project_path_outcomes_main_grid"]) == 108
        assert len(data["changed_paths_main_grid"]) == values["changed"]
        assert all(sum(counts.values()) == 108 for counts in data["first_failure_stage_main_grid"].values())


def test_corrected_costs_add_all_continuation_spend_and_count_failed_calls(result):
    groups = result["model_groups"]
    original = groups["original_4096"]["costs"]["all_effective"]
    price = groups["price_matched_16384"]["costs"]["all_effective"]
    assert original["base_spend_usd"] == pytest.approx(7.6922558)
    assert price["base_spend_usd"] == pytest.approx(23.2234954)
    assert original["continuation_spend_usd"] + price["continuation_spend_usd"] == pytest.approx(1.3973876)
    assert original["corrected_v3"]["n_feasible"] == 36
    assert price["corrected_v3"]["n_feasible"] == 77
    assert original["corrected_v31"]["n_feasible"] == 48
    assert price["corrected_v31"]["n_feasible"] == 100
    assert original["corrected_v3"]["cost_per_feasible_completion_usd"] == pytest.approx(7.9178863 / 36)
    assert original["corrected_v31"]["cost_per_feasible_completion_usd"] == pytest.approx(7.9178863 / 48)
    assert price["corrected_v31"]["cost_per_feasible_completion_usd"] == pytest.approx(24.3952525 / 100)


def test_processed_json_uses_aliases_only_and_router_is_open_item(result):
    encoded = json.dumps(result)
    for display_name in ("Sonnet", "Nova Pro", "gpt-oss", "Kimi", "GLM", "Anthropic", "Amazon"):
        assert display_name not in encoded
    assert result["rules"]["rounding_recovery_applied_to_q2"] is False
    assert "does not recompute" in result["router_validity_open_item"]


def test_saved_outputs_are_reproducible_and_disclose_constraints(result):
    assert result == json.loads(q2.OUT.read_text())
    report = q2.render_report(result)
    assert report == q2.REPORT.read_text()
    assert "POST-HOC / CORRECTED SENSITIVITY" in report
    assert "40/40" in report and "11/11" in report
    assert "upstream `failed` status" in report
    assert "22/50 and 31/64" in report
