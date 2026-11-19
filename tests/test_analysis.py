"""Golden, offline tests for the M6 analysis pipeline on SYNTHETIC_FIXTURE records (hand-checked)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.analysis.io import REPO_ROOT, sha256_file
from src.analysis.pipeline import AnalysisConfig, run_analysis
from tests.fixtures.analysis import SYNTHETIC_FIXTURE_records as fx

GEN_AT, CODE = "2026-01-01T00:00:00+00:00", "test-code-version"


def _cfg(tmp: Path, out: str = "out", **kw) -> AnalysisConfig:
    recs = fx.write_jsonl(tmp / f"{fx.MARK}_expB.jsonl", fx.base_runs())
    kw.setdefault("workflow_records", [str(recs)])
    return AnalysisConfig(out_dir=str(tmp / out), generated_at=GEN_AT, code_version=CODE, **kw)


def _load(out: Path, name: str) -> dict:
    return json.loads((out / f"{name}.json").read_text())


def _rows(out, name, **match):
    return [r for r in _load(out, name)["rows"] if all(r.get(k) == v for k, v in match.items())]


@pytest.fixture
def analysed(tmp_path):
    run_analysis(_cfg(tmp_path))
    return tmp_path / "out"


def test_path_summary_feasibility_void_exclusion_and_quality(analysed):
    aa, = _rows(analysed, "path_summary", path_id="A-A")
    assert (aa["n_runs"], aa["n_void_infra"], aa["n_feasible"], aa["feasibility_rate"]) == (2, 0, 2, 1.0)
    assert aa["gt.analysis.numerical_accuracy"] == pytest.approx(0.8)
    assert aa["end_to_end_ms_mean"] == 1200 and aa["api_latency_ms_mean"] == 650     # kept separate
    assert aa["same_model"] is True and aa["n_switches"] == 0
    ab, = _rows(analysed, "path_summary", path_id="A-B")
    # one infeasible + one void: void counted but excluded from the strict rate, quality and efficiency
    assert (ab["n_runs"], ab["n_void_infra"], ab["n_valid"], ab["feasibility_rate"]) == (2, 1, 1, 0.0)
    assert ab["outcome_label"] == "infeasible" and ab["same_model"] is False
    assert ab["gt.analysis.numerical_accuracy"] == 0.5 and ab["cond.analysis.numerical_accuracy"] == 0.8
    assert ab["end_to_end_ms_mean"] == 900
    bbb, = _rows(analysed, "path_summary", path_id="B-B-B")
    assert bbb["feasibility_rate"] is None and bbb["outcome_label"] == "void_infra"
    assert "void_infra" in bbb["status_detail"]
    for r in _load(analysed, "path_summary")["rows"]:          # missing price: never 0
        assert r["cost_usd_mean"] is None and r["cost_status"] == "unavailable"
        assert r["experiment_id"] == fx.EXP_B and r["benchmark_version"] == "unrecorded"
        assert r["prompt_version"] in ("v2", None)
    csv = (analysed / "path_summary.csv").read_text()
    assert ",unavailable," in csv and "# status: partial" in csv


def test_propagation_is_descriptive(analysed):
    rows = _rows(analysed, "propagation", path_id="A-B", quantity="propagation_impact")
    assert len(rows) == 1 and rows[0]["mean"] == pytest.approx(0.3) and rows[0]["n"] == 1   # void run excluded
    assert all(r["interpretation"] == "descriptive_decomposition_not_causal_switching_cost"
               for r in _load(analysed, "propagation")["rows"] if r["quantity"])
    ex, = _rows(analysed, "propagation", path_id="A-B", quantity="downstream_executable", stage="analysis")
    assert ex["mean"] == 1.0 and ex["n"] == 1
    assert "NOT a causal" in " ".join(_load(analysed, "propagation")["metadata"]["notes"])


def test_pareto_golden(analysed):
    two = {r["path_id"]: r for r in _rows(analysed, "pareto", n_stages=2)}
    assert set(two) == {"A-A", "B-A", "B-B"}                     # A-B has no feasible run
    assert two["A-A"]["pareto_optimal"] and two["B-A"]["pareto_optimal"]
    assert not two["B-B"]["pareto_optimal"] and two["B-B"]["dominated_by"] == "A-A"
    assert two["A-A"]["total_tokens"] == pytest.approx(165.0)
    assert "cost_usd:min" not in two["A-A"]["objectives"]        # cost unverified -> inactive
    assert "analysis.numerical_accuracy:max" in two["A-A"]["objectives"]
    three = _rows(analysed, "pareto", n_stages=3)
    assert [r["path_id"] for r in three] == ["A-A-A"] and three[0]["pareto_optimal"]


def test_pareto_no_feasible_path_row(tmp_path):
    runs = [fx.run("x", "A-A", ["failed", "blocked"], {"cleaning": {"cleaning_correctness": 0.1}})]
    recs = fx.write_jsonl(tmp_path / "r.jsonl", runs)
    run_analysis(_cfg(tmp_path, workflow_records=[str(recs)]))
    rows = _load(tmp_path / "out", "pareto")["rows"]
    assert len(rows) == 1 and rows[0]["row_type"] == "no_feasible_path" and rows[0]["path_id"] is None


def test_insufficient_evidence_tables(analysed):
    for name in ("matched_baseline", "strategies", "counterfactual_validity", "faithfulness"):
        t = _load(analysed, name)
        assert t["metadata"]["status"] == "insufficient_evidence", name
        assert len(t["rows"]) == 1 and t["rows"][0]["status_detail"].startswith("insufficient_evidence")
    assert not (analysed / "fig_counterfactual_deltas.png").exists()


def test_matched_baseline_with_experiment_a(tmp_path):
    a = fx.write_jsonl(tmp_path / "a.jsonl", [fx.stage_record("ea0", "A", 1.0)])
    run_analysis(_cfg(tmp_path, stage_benchmark_records=[str(a)]))
    out = tmp_path / "out"
    r, = _rows(out, "matched_baseline", analysis_model="A", upstream_cleaning_model="A", n_stages=2,
               metric="numerical_accuracy")
    assert r["canonical_mean"] == 1.0 and r["actual_upstream_mean"] == pytest.approx(0.8)
    assert r["difference_actual_minus_canonical"] == pytest.approx(-0.2)
    assert r["canonical_experiment_id"] == fx.EXP_A and r["experiment_id"] == fx.EXP_B
    r, = _rows(out, "matched_baseline", analysis_model="A", upstream_cleaning_model="B", n_stages=2,
               metric="numerical_accuracy")
    assert r["difference_actual_minus_canonical"] == pytest.approx(-0.05)
    miss, = _rows(out, "matched_baseline", analysis_model="B", upstream_cleaning_model="A")
    assert miss["status_detail"].startswith("insufficient_evidence")     # no Exp A record for model B
    three, = _rows(out, "matched_baseline", analysis_model="A", upstream_cleaning_model="A", n_stages=3,
                   metric="numerical_accuracy")
    assert three["actual_upstream_mean"] == 1.0 and three["actual_upstream_n"] == 2   # never pooled with 2-stage
    assert _load(out, "matched_baseline")["metadata"]["status"] == "partial"


def test_variability_repeats_without_significance(analysed):
    r, = _rows(analysed, "variability", path_id="A-A", quantity="gt.analysis.numerical_accuracy")
    assert (r["n"], r["min"], r["max"]) == (2, 0.7, 0.9) and r["spread"] == pytest.approx(0.2)
    assert r["repeat_indices"] == [0, 1]
    assert {x["path_id"] for x in _load(analysed, "variability")["rows"]} == {"A-A"}
    assert "No significance" in " ".join(_load(analysed, "variability")["metadata"]["notes"])


def test_reporting_scores_side_by_side_never_pooled(tmp_path):
    cfg = _cfg(tmp_path)
    rs = fx.rescore(tmp_path / f"{fx.MARK}_rescore.json", sha256_file(cfg.workflow_records[0]))
    cfg.reporting_rescores = [str(rs)]
    run_analysis(cfg)
    out = tmp_path / "out"
    runs = _rows(out, "reporting_scores", row_type="run", run_id=f"{fx.MARK}-aab0")
    assert {(r["validator_version"], r["origin"], r["hard_pass"]) for r in runs} == {
        ("2.0", "raw_record", False), ("3.0-post-freeze", "post_hoc_rescore", True)}
    summ = {r["validator_version"]: r for r in _rows(out, "reporting_scores", row_type="version_summary")}
    assert (summ["2.0"]["n_reports"], summ["2.0"]["n_hard_pass"]) == (2, 1)
    assert (summ["3.0-post-freeze"]["n_reports"], summ["3.0-post-freeze"]["n_hard_pass"]) == (1, 1)
    for r in _load(out, "reporting_scores")["rows"]:          # every row carries exactly one version
        assert r["validator_version"] in ("2.0", "3.0-post-freeze")
    assert _load(out, "reporting_scores")["metadata"]["validator_versions"] == ["2.0", "3.0-post-freeze"]


def test_reporting_rescore_disagreeing_with_raw_is_refused(tmp_path):
    cfg = _cfg(tmp_path)
    cfg.reporting_rescores = [str(fx.rescore(tmp_path / "rs.json", "x", aab_v2_pass=True))]
    with pytest.raises(ValueError, match="disagrees"):
        run_analysis(cfg)


def test_determinism_byte_identical(tmp_path):
    run_analysis(_cfg(tmp_path, "o1"))
    run_analysis(_cfg(tmp_path, "o2"))
    f1, f2 = sorted((tmp_path / "o1").iterdir()), sorted((tmp_path / "o2").iterdir())
    assert [p.name for p in f1] == [p.name for p in f2] and any(p.suffix == ".png" for p in f1)
    for a, b in zip(f1, f2):
        assert a.read_bytes() == b.read_bytes(), a.name


def test_mixed_experiments_refused_unless_grouped(tmp_path):
    other = fx.write_jsonl(tmp_path / "other.jsonl", [
        fx.run("o-aa0", "A-A", ["passed", "passed"], {"cleaning": {"cleaning_correctness": 1.0}},
               exp=f"{fx.MARK}_expB_other")])
    cfg = _cfg(tmp_path)
    cfg.workflow_records.append(str(other))
    with pytest.raises(ValueError, match="several experiment_ids"):
        run_analysis(cfg)
    cfg.experiment_group = [fx.EXP_B, f"{fx.MARK}_expB_other"]
    run_analysis(cfg)
    rows = _rows(tmp_path / "out", "path_summary", path_id="A-A")
    assert sorted(r["experiment_id"] for r in rows) == sorted(cfg.experiment_group)   # separate, not pooled


def test_output_guard_refuses_synthetic_under_results(tmp_path):
    target = REPO_ROOT / "results" / "processed" / "should_not_exist_synthetic"
    cfg = _cfg(tmp_path)
    cfg.out_dir = str(target)
    with pytest.raises(ValueError, match="SYNTHETIC_FIXTURE"):
        run_analysis(cfg)
    assert not target.exists()


def test_pilot_status_override_and_labels(tmp_path):
    run_analysis(_cfg(tmp_path, status_override="pilot_only"))
    out = tmp_path / "out"
    m = json.loads((out / "manifest.json").read_text())
    assert all(t["status"] == "pilot_only" for t in m["tables"].values())
    assert m["tables"]["path_summary"]["evidence_status"] == "partial"
    assert m["synthetic_fixture"] is True and m["schema_version"] == "analysis-1.0"
    for name, h in m["files"].items():
        assert sha256_file(out / name) == h


def test_routing_outputs_feed_strategy_validity_and_faithfulness_separately(tmp_path):
    from experiments.evaluate_routing import run_predict
    from experiments.validate_counterfactuals import run_validate
    from src.routing.config import load_routing_config
    from src.routing.data import load_records

    recs = REPO_ROOT / "tests" / "fixtures" / "xai" / "SYNTHETIC_FIXTURE_records.jsonl"
    store, cfg = load_records(recs), load_routing_config()
    rdir = tmp_path / "routing"
    run_predict(store, cfg, rdir, created_at=GEN_AT)
    run_validate(store, cfg, rdir, validated_at=GEN_AT)
    run_analysis(AnalysisConfig(workflow_records=[str(recs)], out_dir=str(tmp_path / "out"),
                                routing_dir=str(rdir), generated_at=GEN_AT, code_version=CODE))
    out = tmp_path / "out"
    st = _load(out, "strategies")
    assert st["metadata"]["evidence_status"] == "complete" and st["rows"]
    assert all(r["oracle_role"] == "S4_retrospective_reference_not_deployable" for r in st["rows"])
    assert "S4_oracle" not in {r["strategy"] for r in st["rows"]}             # S4 is never a strategy row
    cf, fa = _load(out, "counterfactual_validity"), _load(out, "faithfulness")
    assert cf["rows"] and fa["rows"] and set(cf["columns"]).isdisjoint({"claims_checked", "replay_matches_selection"})
    assert "abs_error" not in fa["columns"]
    assert (out / "fig_counterfactual_deltas.png").exists()
