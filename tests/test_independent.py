"""Tests for the Part A extension (A1-A3): datasets, scorers, sandbox path, plan safety, isolation from routing."""

import json
from pathlib import Path

import pytest

from datasets.independent import generate
from experiments import run_independent_benchmark as rib
from src.independent.tasks import (A1_HARNESS, A1Response, A2Response, A3Claim, A3Response, score_a1, score_a2,
                                   score_a3)

REPO = Path(__file__).resolve().parents[1]


def _cases(task):
    return rib.load_cases(task)


def test_datasets_reproducible_and_counts():
    assert generate.main(["--check"]) == 0
    assert [len(_cases(t)) for t in ("a1", "a2", "a3")] == [10, 10, 10]


@pytest.mark.parametrize("case", _cases("a1"), ids=lambda c: c["case_id"])
def test_a1_reference_scores_correct_and_buggy_does_not(case):
    ok, s, _ = score_a1(case, A1Response(fixed_code=case["reference"], bug_location=case["func"], explanation="x"),
                        generate.run_harness_locally(case["reference"], case["hidden"]))
    assert ok and s["functional_correct"] and s["hidden_pass_rate"] == 1.0
    ok, s, _ = score_a1(case, A1Response(fixed_code=case["buggy"], bug_location="?", explanation="x"),
                        generate.run_harness_locally(case["buggy"], case["hidden"]))
    assert ok and not s["functional_correct"]


def test_a1_syntax_error_is_hard_fail():
    case = _cases("a1")[0]
    ok, s, detail = score_a1(case, None, generate.run_harness_locally("def oops(:\n", case["hidden"]))
    assert not ok and "failed to load" in detail and s["hidden_pass_rate"] == 0.0


def test_a1_runs_in_real_sandbox():
    from src.workflow.executor import DockerExecutor
    ex = DockerExecutor()
    if not ex.availability()[0]:
        pytest.skip("sandbox unavailable")
    case = _cases("a1")[4]                       # mutable default case
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        sol, tests = Path(t) / "solution.py", Path(t) / "tests.json"
        sol.write_text(case["reference"]); tests.write_text(json.dumps(case["hidden"]))
        res = ex.execute(A1_HARNESS, {"solution.py": str(sol), "tests.json": str(tests)}, str(Path(t) / "out"))
        assert res.status.value == "success", res.stderr
        ok, s, _ = score_a1(case, None, json.loads((Path(t) / "out" / "results.json").read_text()))
        assert ok and s["functional_correct"]


def test_a2_gold_is_perfect_and_errors_are_counted():
    case = _cases("a2")[0]
    ok, s, _ = score_a2(case, A2Response(fields=dict(case["gold"])))
    assert ok and s["f1"] == 1.0 and s["all_fields_correct"] and s["hallucinated_fields"] == 0
    null_field = case["missing_fields"][0]
    bad = dict(case["gold"]); bad[null_field] = "invented"
    ok, s, _ = score_a2(case, A2Response(fields=bad))
    assert ok and s["hallucinated_fields"] == 1 and s["precision"] < 1.0
    wrong_key = next(k for k, v in case["gold"].items() if v is not None)
    bad = dict(case["gold"]); bad[wrong_key] = "WRONG"
    assert score_a2(case, A2Response(fields=bad))[1]["f1"] < 1.0
    bad = dict(case["gold"]); bad.pop(wrong_key)
    ok, s, detail = score_a2(case, A2Response(fields=bad))
    assert not ok and not s["schema_valid"]


def _ideal_a3(case):
    rel, facts = case["relevance"], case["facts"]
    top = sorted(rel, key=lambda d: (-rel[d], d))[:5]
    claims = [A3Claim(attribute="dataset", value=facts[d]["dataset"], cited_ids=[d]) for d in top[:3]]
    return A3Response(ranked_ids=top, summary=" ".join(f"[{d}]" for d in top), claims=claims)


def test_a3_ideal_answer_is_perfect_and_errors_detected():
    case = _cases("a3")[0]
    ok, s, _ = score_a3(case, _ideal_a3(case))
    assert ok and s["ndcg_at_5"] == pytest.approx(1.0) and s["grounding_accuracy"] == 1.0 and s["citation_consistent"]
    r = _ideal_a3(case)
    r.claims[0] = A3Claim(attribute="dataset", value="NotADataset", cited_ids=r.claims[0].cited_ids)
    assert score_a3(case, r)[1]["grounding_accuracy"] < 1.0
    r = _ideal_a3(case); r.ranked_ids[0] = "D9999"
    ok, _, detail = score_a3(case, r)
    assert not ok and "not in candidates" in detail
    hard_neg = [d for d, g in case["relevance"].items() if g == 0][:5]
    assert score_a3(case, A3Response(ranked_ids=hard_neg, summary="", claims=[]))[1]["ndcg_at_5"] == 0.0


def test_prompts_render_without_hidden_ground_truth():
    for task in ("a1", "a2", "a3"):
        for case in _cases(task):
            p = rib.render(task, case)
            if task == "a1":
                assert case["reference"].strip() not in p
                assert all(t in p for t in case["visible"])
                hidden_only = [t for t in case["hidden"] if t not in case["visible"]]
                assert not any(t in p for t in hidden_only)
            if task == "a2":
                assert "missing_fields" not in p and "gold" not in p
            if task == "a3":
                assert '"relevance"' not in p and "grade" not in p.lower() and "facts" not in p


def test_plan_makes_no_aws_client(monkeypatch):
    import boto3
    monkeypatch.setattr(boto3, "Session", lambda *a, **k: (_ for _ in ()).throw(AssertionError("AWS touched")))
    assert rib.main(["--task", "all", "--plan"]) == 0


def test_independent_records_cannot_enter_routing(tmp_path):
    from src.routing.data import load_records
    rec = {"schema_version": "indep-1.0", "record_kind": "independent_task", "run_id": "x", "experiment_id": "indepA1_debug_v1",
           "task": "a1", "case_id": "c", "model_alias": "A", "status": "passed"}
    p = tmp_path / "indep.jsonl"
    p.write_text(json.dumps(rec) + "\n")
    try:
        loaded = load_records(p)
    except Exception:
        return                                  # rejected outright: fine
    runs = getattr(loaded, "workflow_runs", None) or getattr(loaded, "workflow", None) or []
    benches = getattr(loaded, "stage_benchmarks", None) or getattr(loaded, "stage", None) or []
    assert not runs and not benches
