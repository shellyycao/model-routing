import json

from experiments import analyze_corrected_view as corrected


def _row(result, group, part, stage, alias):
    return result["model_groups"][group]["parts"][part]["stages"][stage]["models"][alias]


def test_evidence_sets_are_disjoint_and_all_attributions_sum():
    result = corrected.analyze()
    assertions = result["assertions"]
    assert assertions["rounding_recoveries"] == 15
    assert assertions["q7_v3_1_recoveries"] == 30
    assert assertions["rounding_q7_disjoint"] is True
    assert assertions["total_attribution_counts"] == {
        "frozen_pass": 518,
        "int64_recovered": 55,
        "rounding_recovered": 15,
        "v3_1_recovered": 30,
        "not_recovered": 390,
    }
    assert sum(assertions["total_attribution_counts"].values()) == 1008
    for group in result["model_groups"].values():
        for part in group["parts"].values():
            for stage in part["stages"].values():
                for row in stage["models"].values():
                    assert sum(row["attribution_counts"].values()) == row["denominator"]


def test_selected_corrected_stage_counts_match_frozen_evidence():
    result = corrected.analyze()
    glm_a = _row(result, "price_matched_16384", "part_a", "analysis", "C")
    assert (glm_a["frozen"]["passed"], glm_a["combined"]["passed"], glm_a["denominator"]) == (0, 4, 4)
    glm_b = _row(result, "price_matched_16384", "part_b", "analysis", "C")
    assert (glm_b["frozen"]["passed"], glm_b["combined"]["passed"], glm_b["denominator"]) == (27, 56, 60)
    nova_b = _row(result, "original_4096", "part_b", "analysis", "B")
    assert nova_b["int64_recovered"]["unique_additions"] == 9
    gpt_clean = _row(result, "original_4096", "part_b", "cleaning", "C")
    assert gpt_clean["int64_recovered"]["unique_additions"] == 9


def test_part_b_uses_effective_cells_and_does_not_compute_workflow_feasibility():
    result = corrected.analyze()
    audit = result["assertions"]["effective_part_b"]
    assert audit["original_4096"] == {"raw_records": 156, "effective_records": 156, "replacements": 0}
    assert audit["price_matched_16384"] == {"raw_records": 161, "effective_records": 156, "replacements": 5}
    assert result["assertions"]["corrected_part_b_feasibility_computed"] is False
    assert "feasibility" not in json.dumps(result["model_groups"])


def test_processed_json_contains_aliases_not_model_names():
    result = corrected.analyze()
    serialized = json.dumps(result)
    for forbidden in ("Sonnet", "Nova Pro", "gpt-oss", "Kimi", "GLM 5", "Anthropic", "Amazon", "OpenAI"):
        assert forbidden not in serialized
    for group in result["model_groups"].values():
        for part in group["parts"].values():
            for stage in part["stages"].values():
                assert set(stage["models"]) == {"A", "B", "C"}


def test_saved_outputs_equal_fresh_offline_analysis():
    saved = json.loads(corrected.OUT.read_text())
    fresh = corrected.analyze()
    assert saved == fresh
    report = corrected.REPORT.read_text()
    assert "POST-HOC / SENSITIVITY" in report
    assert "GLM 5" in report
    assert "does not compute corrected Part B workflow feasibility" in report

