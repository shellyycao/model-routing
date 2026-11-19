"""Read-only reproducibility audit of the frozen independent-v1 benchmark.

Only additive processed evidence is written.  Raw records, saved outputs, prompts,
datasets, validators, and frozen scores are never modified.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from experiments.rescore_independent_posthoc import claim_ok_v11
from src.independent.tasks import A1Response, A2Response, A3Response, score_a1, score_a2, score_a3

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "results/raw/independent"
CASES = REPO / "datasets/independent"
RUNS = REPO / "results/raw/runs"
OUT = REPO / "results/processed/independent/audit_v1.json"
FILES = {"a1": "indepA1_debug_v1.jsonl", "a2": "indepA2_extract_v1.jsonl", "a3": "indepA3_lit_v1.jsonl"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _same(left, right) -> bool:
    if isinstance(left, float) or isinstance(right, float):
        return math.isclose(float(left), float(right), rel_tol=1e-12, abs_tol=1e-12)
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(_same(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return left == right


def _load_records(task: str) -> list[dict]:
    return [json.loads(line) for line in (RAW / FILES[task]).read_text().splitlines() if line.strip()]


def _case(task: str, case_id: str) -> dict:
    return json.loads((CASES / task / "cases" / f"{case_id}.json").read_text())


def _rescore(record: dict) -> tuple[dict, str | None]:
    task, run_id = record["task"], record["run_id"]
    case, run_dir = _case(task, record["case_id"]), RUNS / run_id
    if not record["parse_ok"]:
        return {}, record.get("failure_detail")
    if task == "a1":
        response = A1Response.model_validate_json((run_dir / "parsed.json").read_text())
        harness = json.loads((run_dir / "output/results.json").read_text())
        _, scores, detail = score_a1(case, response, harness)
    elif task == "a2":
        response = A2Response.model_validate_json((run_dir / "parsed.json").read_text())
        _, scores, detail = score_a2(case, response)
    else:
        response = A3Response.model_validate_json((run_dir / "parsed.json").read_text())
        _, scores, detail = score_a3(case, response)
    return scores, detail


def _a1_sentinel_checks() -> list[dict]:
    """Concrete pass-the-suite-but-violate-the-spec demonstrations."""
    examples = {
        "a1_01_moving_average": (
            """def moving_average(xs, k):
    if k <= 0 or k > len(xs): return []
    if 1 < k < len(xs) and k != 2: return []
    return [sum(xs[i:i+k]) / k for i in range(len(xs)-k+1)]
""",
            "moving_average([1,2,3,4,5], 3) == [2.0,3.0,4.0]",
        ),
        "a1_02_is_leap": (
            """def is_leap(year):
    if year in (2000, 2400): return True
    return year % 4 == 0 and year % 100 != 0
""",
            "is_leap(2800) is True",
        ),
    }
    output=[]
    for case_id,(source,unseen) in examples.items():
        case=_case("a1",case_id); namespace={"__name__":"audit"}
        def _raises(fn, exc):
            try: fn()
            except exc: return True
            except Exception: return False
            return False
        namespace["_raises"]=_raises; exec(source,namespace)
        hidden=[bool(eval(test,namespace)) for test in case["hidden"]]
        output.append({"case_id":case_id,"hidden_passed":sum(hidden),"hidden_total":len(hidden),
                       "unseen_spec_check":unseen,"unseen_spec_check_passed":bool(eval(unseen,namespace)),
                       "interpretation":"finite hidden tests can be gamed; passing is evidence, not proof of semantic equivalence"})
    return output


def main() -> int:
    report={"audit_scope":"frozen independent-v1 saved data and implementation","raw_modified":False,"tasks":{},
            "a1_pass_but_incorrect_demonstrations":_a1_sentinel_checks(),"issues":[]}
    all_run_ids=[]
    for task in ("a1","a2","a3"):
        records=_load_records(task); all_run_ids += [record["run_id"] for record in records]
        mismatches=[]; missing=[]; case_hash_mismatches=[]; prompt_hash_mismatches=[]
        for record in records:
            run_dir=RUNS/record["run_id"]
            needed=[run_dir/"prompt.txt",run_dir/"response.txt"]
            if record["parse_ok"]: needed.append(run_dir/"parsed.json")
            missing += [str(path.relative_to(REPO)) for path in needed if not path.exists()]
            case_path=CASES/task/"cases"/f"{record['case_id']}.json"
            if _sha(case_path)!=record["case_hash"]: case_hash_mismatches.append(record["run_id"])
            if _sha(run_dir/"prompt.txt")!=record["prompt_hash"]: prompt_hash_mismatches.append(record["run_id"])
            scores,_=_rescore(record)
            if record["parse_ok"] and not _same(scores,record["scores"]): mismatches.append(record["run_id"])
        by_model={}
        for model in sorted({record["model_alias"] for record in records}):
            selected=[record for record in records if record["model_alias"]==model]
            by_model[model]={"n":len(selected),"status":dict(Counter(record["status"] for record in selected)),
                             "failure_type":dict(Counter(record.get("failure_type") or "none" for record in selected))}
        report["tasks"][task]={"records":len(records),"unique_cases":len({r['case_id'] for r in records}),"models":by_model,
                               "saved_artifacts_missing":missing,"case_hash_mismatches":case_hash_mismatches,
                               "prompt_hash_mismatches":prompt_hash_mismatches,"frozen_rescore_mismatches":mismatches}
    report["run_id_duplicates"]=[run_id for run_id,count in Counter(all_run_ids).items() if count>1]

    a2_recovered=[]
    for record in _load_records("a2"):
        if record["parse_ok"] or "fields\n  Field required" not in (record.get("failure_detail") or ""): continue
        raw=(RUNS/record["run_id"]/"response.txt").read_text(); match=re.search(r"\{.*\}",raw,re.S)
        if not match: continue
        fields=json.loads(match.group(0)); _,scores,_=score_a2(_case("a2",record["case_id"]),A2Response(fields=fields))
        a2_recovered.append({"run_id":record["run_id"],"model_alias":record["model_alias"],"case_id":record["case_id"],
                             "frozen_operational_pass":False,"recovered_content_f1":scores["f1"],"content_correct":scores["all_fields_correct"]})
    report["a2_unwrapped_recovery"]=a2_recovered

    a3=[]
    for record in _load_records("a3"):
        if not record["parse_ok"]: continue
        case=_case("a3",record["case_id"]); response=A3Response.model_validate_json((RUNS/record["run_id"]/"parsed.json").read_text())
        v11=sum(claim_ok_v11(claim,case["facts"]) for claim in response.claims)/len(response.claims) if response.claims else 0
        a3.append({"run_id":record["run_id"],"model_alias":record["model_alias"],"case_id":record["case_id"],
                   "grounding_v1":record["scores"]["grounding_accuracy"],"grounding_v1_1":v11,
                   "claims_reclassified":round((v11-record["scores"]["grounding_accuracy"])*len(response.claims))})
    report["a3_grounding_reclassification"]=a3
    report["issues"]=[
        {"id":"A1-CEILING","severity":"major","finding":"29/30 model outputs are functionally correct; two explicit non-equivalent implementations pass every hidden test."},
        {"id":"A1-STATUS","severity":"major","finding":"A1 record status/hard gate means code loaded, not that all tests passed; one functionally incorrect output is still status=passed."},
        {"id":"A2-CONFLATION","severity":"major","finding":"Seven gpt-oss failures are wrapper failures with recoverable perfect content, so operational and content scores must be separate."},
        {"id":"A2-DIVERSITY","severity":"major","finding":"Only five synthetic document families with paired templates limit external validity."},
        {"id":"A3-GROUNDING","severity":"major","finding":"Frozen v1 compares canonical labels against paraphrased abstracts; v1.1 reclassifies documented surface forms post hoc."},
        {"id":"A3-CONTROLLED","severity":"clarification","finding":"A3 is controlled selection over synthetic candidates, not live web search."},
        {"id":"AUTHOR-BIAS","severity":"major","finding":"Mechanical labels avoid direct evaluated-model judging, but Claude-family authorship can still affect task style, difficulty, and preferred phrasing."},
    ]
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT.relative_to(REPO)),"records":sum(x["records"] for x in report["tasks"].values()),
                      "rescore_mismatches":sum(len(x["frozen_rescore_mismatches"]) for x in report["tasks"].values()),
                      "missing_artifacts":sum(len(x["saved_artifacts_missing"]) for x in report["tasks"].values())},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
