"""SYNTHETIC_FIXTURE tests for the post-hoc router relabel analyzer (statistics, ties, baselines, leakage)."""
from experiments.analyze_router_relabel import (
    acc, binom_two_sided, mcnemar_exact, rate_sign, stage_rates, wilson,
)


def _sgn(x):
    return 0 if abs(x) <= 1e-12 else (1 if x > 0 else -1)


def test_wilson_known_values():
    lo, hi = wilson(0, 10)
    assert lo == 0.0 and abs(hi - 0.2775) < 1e-3
    lo, hi = wilson(5, 10)
    assert abs(lo + hi - 1.0) < 1e-9 and abs(lo - 0.2366) < 1e-3
    assert wilson(0, 0) is None


def test_binomial_exact():
    assert abs(binom_two_sided(5, 10) - 1.0) < 1e-12
    assert abs(binom_two_sided(0, 10) - 2 / 1024) < 1e-12
    assert abs(binom_two_sided(9, 10) - 22 / 1024) < 1e-12
    assert binom_two_sided(0, 0) is None
    assert mcnemar_exact(0, 0) is None
    assert abs(mcnemar_exact(3, 0) - 0.25) < 1e-12


def test_acc_fields():
    a = acc([True, True, False, False])
    assert (a["k"], a["n"], a["accuracy"]) == (2, 4, 0.5)
    assert a["p_binomial_vs_0.5"] == 1.0 and len(a["wilson95"]) == 2


def test_rate_sign_ties_and_single_stage():
    rates = {(s, m): 0.5 for s in ("cleaning", "analysis", "reporting") for m in "ABC"}
    assert rate_sign(rates, "A-A-A", "A-A-B") == 0  # tie predicts 0
    rates[("reporting", "B")] = 0.9
    assert rate_sign(rates, "A-A-A", "A-A-B") == 1
    rates[("analysis", "B")] = 0.1
    assert rate_sign(rates, "A-A-A", "A-B-A") == -1
    assert rate_sign(rates, "A-A-A", "B-B-B") == _sgn(0.5 * 0.1 * 0.9 - 0.125)


def test_stage_rates_exclude_held_out():
    from types import SimpleNamespace as N
    rows = [N(project_id="P1", stage="cleaning", model_alias="A", frozen=True, combined=True),
            N(project_id="P2", stage="cleaning", model_alias="A", frozen=False, combined=False),
            N(project_id="P2", stage="cleaning", model_alias="A", frozen=False, combined=True)]
    assert stage_rates(rows, "p1", "frozen")[("cleaning", "A")] == 0.0
    assert stage_rates(rows, "p2", "combined")[("cleaning", "A")] == 1.0
