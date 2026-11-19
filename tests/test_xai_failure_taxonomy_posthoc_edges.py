"""SYNTHETIC_FIXTURE edge tests: rule 7 vs 8 collision, exception-class fallback, empty/small strata."""
from experiments.analyze_failure_taxonomy import classify, draw_sample, exception_class
from tests.test_xai_failure_taxonomy_posthoc import EV, ExecutionResult, rec, unit


def test_rule7_vs_rule8_collision_goes_to_rule7():
    r = rec(ft="execution_error", structural_ok=False, parse_ok=False)
    c, _, rules = classify(unit(r), EV)
    assert c == "other_execution_error" and rules == [7, 8]


def test_exception_class_fallbacks():
    ex = ExecutionResult(status="runtime_error", stderr="something odd happened\nno class here: x")
    assert exception_class(rec(detail="KeyError: 'a'", execution=ex)) == "KeyError"
    r2 = rec(detail="unstructured failure", execution=ex)
    assert exception_class(r2) == "no_exception_class"
    assert classify(unit(r2), EV)[0] == "other_execution_error"


def test_sample_empty_and_small_strata():
    assert draw_sample([])["units"] == []
    units = [{"group": "g", "part": "part_b", "run_id": f"r{i}", "stage": "analysis", "alias": "A",
              "category": "unexplained_residual"} for i in range(2)]
    s = draw_sample(units)
    assert len(s["units"]) == 2 and s["stratum_sizes"] == {"g|A": 2}
