"""Task definitions for A1-A3: model response schemas, prompt variables, deterministic scorers.

No LLM judge. Every scorer is a pure function of (gold/case, parsed model response[, sandbox results]).
"""

from __future__ import annotations

import json
import math
import re
from datetime import date

from pydantic import BaseModel, Field


# ============================================================================ A1 debugging
class A1Response(BaseModel):
    fixed_code: str = Field(description="The COMPLETE corrected Python source (all functions), no explanations inside.")
    bug_location: str = Field(description="Function name and a short description of the faulty line.")
    explanation: str = Field(description="One or two sentences explaining the bug and the fix.")


# Runs INSIDE the sandbox: imports the model's fixed code and evaluates hidden test expressions.
A1_HARNESS = r'''
import json, os, signal, sys
IN, OUT = os.environ["INPUT_DIR"], os.environ["OUTPUT_DIR"]
tests = json.load(open(os.path.join(IN, "tests.json")))
src = open(os.path.join(IN, "solution.py")).read()
def _raises(fn, exc):
    try:
        fn()
    except exc:
        return True
    except Exception:
        return False
    return False
class _T(Exception):
    pass
def _alarm(*_):
    raise _T()
signal.signal(signal.SIGALRM, _alarm)
results, load_error = [], None
try:
    signal.alarm(5)
    ns = {"__name__": "solution"}
    exec(compile(src, "solution.py", "exec"), ns)
    signal.alarm(0)
except BaseException as e:
    signal.alarm(0)
    load_error = f"{type(e).__name__}: {e}"[:300]
for t in tests:
    if load_error:
        results.append({"test": t, "passed": False, "error": "load_error"}); continue
    env = dict(ns); env["_raises"] = _raises
    try:
        signal.alarm(2)
        ok = bool(eval(t, env))
        signal.alarm(0)
        results.append({"test": t, "passed": ok, "error": None})
    except _T:
        results.append({"test": t, "passed": False, "error": "timeout"})
    except BaseException as e:
        signal.alarm(0)
        results.append({"test": t, "passed": False, "error": f"{type(e).__name__}: {e}"[:200]})
json.dump({"load_error": load_error, "results": results}, open(os.path.join(OUT, "results.json"), "w"))
'''


def a1_vars(case: dict) -> dict:
    return {"spec": case["spec"], "buggy_code": case["buggy"],
            "visible_tests": "\n".join(f"assert {t}" for t in case["visible"]), "func": case["func"]}


def score_a1(case: dict, resp: A1Response | None, harness_out: dict | None) -> tuple[bool, dict, str | None]:
    """Returns (hard_pass, scores, failure_detail). Hard pass = code loaded and executed (harness ran)."""
    if harness_out is None:
        return False, {}, "no sandbox results"
    res = harness_out.get("results", [])
    n = len(res); k = sum(r["passed"] for r in res)
    vis = set(case["visible"])
    vis_ok = all(r["passed"] for r in res if r["test"] in vis)
    loc = (resp.bug_location if resp else "") or ""
    scores = {"hidden_pass_rate": k / n if n else 0.0, "hidden_passed": k, "hidden_total": n,
              "functional_correct": bool(n and k == n), "visible_tests_pass": vis_ok,
              "load_error": harness_out.get("load_error"),
              "names_buggy_function": case["func"] in loc}
    if harness_out.get("load_error"):
        return False, scores, f"fixed code failed to load: {harness_out['load_error']}"
    return True, scores, None


# ============================================================================ A2 extraction
class A2Response(BaseModel):
    fields: dict = Field(description="Object with EXACTLY the schema's field names as keys; use null when the "
                                     "document does not state the value.")


def _norm(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s.lower() in ("", "null", "none", "n/a", "not stated", "unknown"):
        return None
    if s.lower() in ("true", "yes"):
        return True
    if s.lower() in ("false", "no"):
        return False
    num = re.fullmatch(r"\$?\s*([-\d,]+(?:\.\d+)?)\s*(k)?", s, re.I)
    if num:
        try:
            x = float(num.group(1).replace(",", ""))
            return x * 1000 if num.group(2) else x
        except ValueError:
            pass
    try:
        return date.fromisoformat(s).isoformat()
    except ValueError:
        pass
    return re.sub(r"\s+", " ", s).casefold().strip(" .")


def _eq(gold, pred) -> bool:
    g, p = _norm(gold), _norm(pred)
    if g is None or p is None:
        return g is None and p is None
    if isinstance(g, bool) or isinstance(p, bool):
        return g is p
    if isinstance(g, float) and isinstance(p, float):
        return math.isclose(g, p, rel_tol=0.005, abs_tol=0.011)
    return g == p


def score_a2(case: dict, resp: A2Response | None) -> tuple[bool, dict, str | None]:
    gold, schema = case["gold"], case["schema"]
    if resp is None:
        return False, {}, "no parsed response"
    pred = resp.fields
    missing_keys = [k for k in schema if k not in pred]
    extra_keys = [k for k in pred if k not in schema]
    tp = fp = fn = null_ok = null_total = halluc = 0
    per_field = {}
    for k in schema:
        g, p = gold.get(k), pred.get(k)
        gn, pn = _norm(g) is None, _norm(p) is None
        if gn:
            null_total += 1
            if pn:
                null_ok += 1; per_field[k] = "correct_null"
            else:
                fp += 1; halluc += 1; per_field[k] = "hallucinated"
        elif _eq(g, p):
            tp += 1; per_field[k] = "correct"
        else:
            fn += 1
            if not pn:
                fp += 1; per_field[k] = "wrong_value"
            else:
                per_field[k] = "missed"
    prec = tp / (tp + fp) if tp + fp else 1.0
    rec = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    scores = {"precision": prec, "recall": rec, "f1": f1, "tp": tp, "fp": fp, "fn": fn,
              "null_accuracy": null_ok / null_total if null_total else None, "hallucinated_fields": halluc,
              "all_fields_correct": all(v in ("correct", "correct_null") for v in per_field.values()) and not missing_keys,
              "schema_valid": not missing_keys and not extra_keys, "per_field": per_field}
    if missing_keys or extra_keys:
        return False, scores, f"schema keys mismatch: missing={missing_keys} extra={extra_keys}"
    return True, scores, None


# ============================================================================ A3 literature
class A3Claim(BaseModel):
    attribute: str = Field(description="one of: dataset, metric, value, year, first_author, method, topic")
    value: str | float | int = Field(description="the value as stated in the cited abstract(s)")
    cited_ids: list[str] = Field(description="doc_ids that support this claim")


class A3Response(BaseModel):
    ranked_ids: list[str] = Field(description="Exactly 5 distinct doc_ids from the candidates, most relevant first.")
    summary: str = Field(description="3-6 sentence synthesis; cite doc_ids in square brackets, e.g. [D0012].")
    claims: list[A3Claim] = Field(description="Every factual statement in the summary as a structured claim (at least 3).")


A3_ATTRS = {"dataset", "metric", "value", "year", "first_author", "method", "topic"}


def a3_candidates_text(case: dict) -> str:
    return "\n\n".join(f"[{d['doc_id']}] {d['title']} — {d['authors']} ({d['year']})\n{d['abstract']}"
                       for d in case["candidates"])


def _dcg(gains):
    return sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(gains))


def _claim_ok(claim: A3Claim, facts: dict) -> bool:
    if claim.attribute not in A3_ATTRS or not claim.cited_ids:
        return False
    for cid in claim.cited_ids:
        f = facts.get(cid)
        if f is None:
            return False
        fv = f.get(claim.attribute)
        cv = claim.value
        if isinstance(fv, (int, float)):
            try:
                if not math.isclose(float(cv), float(fv), rel_tol=1e-3, abs_tol=1e-3):
                    return False
            except (TypeError, ValueError):
                return False
        elif str(cv).strip().casefold() not in str(fv).casefold() and str(fv).casefold() not in str(cv).strip().casefold():
            return False
    return True


def score_a3(case: dict, resp: A3Response | None) -> tuple[bool, dict, str | None]:
    if resp is None:
        return False, {}, "no parsed response"
    rel, facts = case["relevance"], case["facts"]
    cand = set(rel)
    ranked = resp.ranked_ids
    problems = []
    if len(ranked) != 5 or len(set(ranked)) != 5:
        problems.append(f"ranked_ids must be 5 distinct ids (got {len(ranked)}, {len(set(ranked))} distinct)")
    unknown_rank = [i for i in ranked if i not in cand]
    cited = {c for cl in resp.claims for c in cl.cited_ids} | set(re.findall(r"\[(D\d{4})\]", resp.summary))
    unknown_cited = sorted(c for c in cited if c not in cand)
    if unknown_rank:
        problems.append(f"ranked ids not in candidates: {unknown_rank}")
    if unknown_cited:
        problems.append(f"cited ids not in candidates: {unknown_cited}")
    top = ranked[:5]
    gains = [rel.get(i, 0) for i in top]
    ideal = sorted(rel.values(), reverse=True)[:5]
    n2 = sum(1 for v in rel.values() if v == 2)
    ok_claims = [c for c in resp.claims if _claim_ok(c, facts)]
    scores = {"precision_at_5": sum(1 for g in gains if g == 2) / 5, "precision_at_5_graded1plus": sum(1 for g in gains if g >= 1) / 5,
              "ndcg_at_5": _dcg(gains) / _dcg(ideal) if _dcg(ideal) else 0.0,
              "recall_grade2_at_5": sum(1 for g in gains if g == 2) / n2 if n2 else None,
              "n_claims": len(resp.claims), "grounding_accuracy": len(ok_claims) / len(resp.claims) if resp.claims else 0.0,
              "citation_consistent": not unknown_cited and all(c.cited_ids for c in resp.claims),
              "cites_outside_ranked": sorted(c for c in cited if c in cand and c not in set(top)),
              "enough_claims": len(resp.claims) >= 3}
    if problems:
        return False, scores, "; ".join(problems)
    return True, scores, None


def keyword_baseline_ndcg(case: dict) -> float:
    """Deterministic non-LLM baseline: rank candidates by query-term overlap (sanity check against trivial labels)."""
    q = set(re.findall(r"[a-z]+", case["query"]["text"].lower())) - {"the", "and", "to", "of", "find", "most", "relevant",
                                                                    "studies", "that", "apply", "which", "they", "used",
                                                                    "what", "results", "report", "summarise"}
    def s(d):
        return len(q & set(re.findall(r"[a-z]+", (d["title"] + " " + d["abstract"]).lower())))
    top = sorted(case["candidates"], key=lambda d: (-s(d), d["doc_id"]))[:5]
    gains = [case["relevance"][d["doc_id"]] for d in top]
    ideal = sorted(case["relevance"].values(), reverse=True)[:5]
    return _dcg(gains) / _dcg(ideal)
