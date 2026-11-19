"""SYNTHETIC_FIXTURE tests: leakage guard, label views, void handling, gate-failure write block."""
from types import SimpleNamespace

import pytest

from experiments import analyze_router_relabel as rr
from experiments.analyze_corrected_q2 import _status_outcome


def _rows():
    def mk(p, a, f):
        return SimpleNamespace(project_id=p, run_id=f"{p}-{a}-{f}", stage="cleaning", model_alias=a,
                               frozen=f, combined=True)
    return [mk("P1", "A", True), mk("p2 ", "A", False), mk(" P3", "A", True), mk("P3", "B", True)]


def test_leakage_guard_variants_and_unknown_project():
    rows = _rows()
    for variant in ("P1", " p1 ", "p1"):  # P1 never contributes; rates from p2 (0) and P3 (1) only
        assert rr.stage_rates(rows, variant, "frozen")[("cleaning", "A")] == 0.5
    assert rr.stage_rates(rows, "p3", "frozen")[("cleaning", "A")] == 0.5  # P1 True, p2 False
    assert ("cleaning", "B") not in rr.stage_rates(rows, "p3", "frozen")
    with pytest.raises(ValueError):
        rr.stage_rates(rows, "unknown_project", "frozen")


def test_with_outcomes_and_void_handling():
    class Feas:
        def __init__(self, outcome):
            self.outcome = outcome

        def model_copy(self, update):
            return Feas(update["outcome"])

    class Run:
        def __init__(self, rid, outcome):
            self.run_id, self.feasibility = rid, Feas(outcome)

        def model_copy(self, update):
            return Run(self.run_id, update["feasibility"].outcome)

    runs = [Run("a", "infeasible"), Run("b", "feasible")]
    out = rr.with_outcomes(runs, {"a": {"v": "feasible"}, "b": {"v": "void_infra"}}, "v")
    assert [r.feasibility.outcome for r in out] == ["feasible", "void_infra"]
    same = rr.with_outcomes(runs, {"a": {"v": "infeasible"}, "b": {"v": "feasible"}}, "v")
    assert same[0] is runs[0] and same[1] is runs[1]
    assert _status_outcome(["passed", "passed", "passed"])[0] == "feasible"
    assert _status_outcome(["passed", "infra_error", "not_run_upstream_failure"])[0] == "void_infra"
    assert _status_outcome(["passed", "failed", "blocked_by_invalid_artifact"]) == ("infeasible", "analysis")


def test_gate_failure_blocks_writes(tmp_path):
    out, rep = tmp_path / "o.json", tmp_path / "r.md"
    assert rr.write_outputs({"status": "GATE_FAILED", "reproduction_gate": {}}, out, rep) is False
    assert not out.exists() and not rep.exists()
