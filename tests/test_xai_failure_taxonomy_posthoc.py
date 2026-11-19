"""SYNTHETIC_FIXTURE tests for the failure taxonomy rules, precedence, and review sample."""
from experiments.analyze_failure_taxonomy import CATEGORIES, PER_STRATUM, classify, draw_sample, exception_class
from src.contracts import StageRunRecord
from src.contracts.execution import CheckResult, ExecutionResult, ValidationResult

EV = {"stop": {"inv-trunc": "max_tokens", "inv-ok": "end_turn"}, "rounding": {("g", "part_b", "r-round")},
      "q7": {("g", "part_b", "r-q7")}}
INT64 = "Object of type int64 is not JSON serializable"


def rec(status="failed", ft="execution_error", detail=None, inv=("inv-ok",), execution=None, validation=None,
        stage="analysis", **kw):
    return StageRunRecord(stage=stage, model_alias="A", model_id="x", prompt_version="v3",
                          invocation_ids=list(inv), status=status, failure_type=ft, failure_detail=detail,
                          execution=execution, validation=validation, **kw)


def unit(r, run_id="r1", retained=False):
    return {"group": "g", "part": "part_b", "run_id": run_id, "stage": r.stage.value,
            "stage_rec": r, "retained_void_rerun": retained}


def val(names):
    return ValidationResult(stage="reporting", hard_pass=False,
                            checks=[CheckResult(name=n, passed=False, mandatory=True) for n in names])


def cat(r, **kw):
    return classify(unit(r, **kw), EV)[0]


def test_int64_requires_failed_status_and_invocation():
    assert cat(rec(detail=INT64)) == "int64_serialization"
    blocked = rec(status="blocked_by_invalid_artifact", ft=None, detail="upstream " + INT64, inv=())
    assert cat(blocked) == "blocked_or_not_run_upstream"


def test_stderr_only_int64_falls_through():
    ex = ExecutionResult(status="runtime_error", stderr="Traceback\nTypeError: " + INT64)
    r = rec(detail="execution failed", execution=ex)
    assert cat(r) == "other_execution_error"
    assert exception_class(r) == "TypeError"


def test_truncation_precedes_parse_and_execution():
    assert cat(rec(ft="parse_error", inv=("inv-trunc",))) == "truncation"
    assert cat(rec(ft="truncated")) == "truncation"


def test_infra_and_blocked():
    assert cat(rec(status="infra_error", ft="infra", detail="Docker daemon")) == "infrastructure_void"
    r = rec(status="infra_error", ft="infra", detail="Docker x")
    assert classify(unit(r, retained=True), EV)[1] == "infra+docker+rerun_audit"
    assert cat(rec(ft="api_error")) == "infrastructure_void"
    assert cat(rec(status="not_run_upstream_failure", ft=None, inv=())) == "blocked_or_not_run_upstream"


def test_rounding_and_q7_precede_mismatch():
    r = rec(ft="validation_failed", validation=val(["derived_values_correct"]), stage="reporting")
    assert cat(r, run_id="r-round") == "reporting_rounding_only"
    assert cat(r) == "genuine_validator_mismatch"
    assert classify(unit(r), EV)[1] == "derived_values_not_rounding"
    q = rec(ft="validation_failed", validation=val(["rankings_correct"]), stage="reporting")
    assert cat(q, run_id="r-q7") == "known_q7_false_reject"


def test_parse_mismatch_residual():
    assert cat(rec(ft="parse_error")) == "parse_or_schema_failure"
    assert cat(rec(ft="invalid_output")) == "parse_or_schema_failure"
    assert cat(rec(ft="validation_failed", validation=val(["a", "b"]))) == "genuine_validator_mismatch"
    assert classify(unit(rec(ft="validation_failed", validation=val(["b", "a"]))), EV)[1] == "a+b"
    assert cat(rec(ft="validation_failed")) == "unexplained_residual"


def test_categories_unique_and_ordered():
    assert len(CATEGORIES) == len(set(CATEGORIES)) == 10 and CATEGORIES[-1] == "unexplained_residual"


def test_sample_deterministic_and_stratified():
    units = [{"group": "g", "part": "part_b", "run_id": f"r{a}{i}", "stage": "analysis", "alias": a,
              "category": "unexplained_residual"} for a in "ABC" for i in range(9)]
    units.append({"group": "g", "part": "part_b", "run_id": "other", "stage": "analysis", "alias": "A",
                  "category": "truncation"})
    s1, s2 = draw_sample(units), draw_sample(list(reversed(units)))
    assert s1 == s2 and len(s1["units"]) == 3 * PER_STRATUM
    assert all("category" not in u for u in s1["units"])
