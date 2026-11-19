"""Offline sensitivity views for the frozen independent-v1 saved outputs."""

from __future__ import annotations

import json
import math
import statistics as stats
from collections import defaultdict
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
RAW=REPO/"results/raw/independent"
AUDIT=REPO/"results/processed/independent/audit_v1.json"
OUT=REPO/"results/processed/independent/scoring_sensitivity.json"
FILES={"a1":"indepA1_debug_v1.jsonl","a2":"indepA2_extract_v1.jsonl","a3":"indepA3_lit_v1.jsonl"}


def _rows(task):
    return [json.loads(line) for line in (RAW/FILES[task]).read_text().splitlines() if line.strip()]


def _mean(values): return sum(values)/len(values) if values else None
def _median(values): return stats.median(values) if values else None


def _wilson(k,n,z=1.96):
    if not n:return [None,None]
    p=k/n;den=1+z*z/n;center=(p+z*z/(2*n))/den;margin=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [center-margin,center+margin]


def _rank(values, reverse=True):
    return [model for model,_ in sorted(values.items(),key=lambda pair:((-pair[1] if reverse else pair[1]),pair[0]))]


def main() -> int:
    audit=json.loads(AUDIT.read_text()); result={"mode":"offline saved-output sensitivity","warning":"Alternative views are post-hoc and never replace frozen v1.","tasks":{}}
    for task in ("a1","a2","a3"):
        rows=_rows(task); models=sorted({r["model_alias"] for r in rows}); table={}
        for model in models:
            selected=[r for r in rows if r["model_alias"]==model]; n=len(selected)
            common={"n":n,"latency_median_s":_median([r["generation_ms"]/1000 for r in selected]),
                    "input_tokens_median":_median([r["input_tokens"] for r in selected]),"output_tokens_median":_median([r["output_tokens"] for r in selected])}
            if task=="a1":
                functional=sum(bool((r.get("scores") or {}).get("functional_correct")) for r in selected)
                common.update({"operational_status_rate":sum(r["status"]=="passed" for r in selected)/n,
                               "functional_rate":functional/n,"functional_wilson95":_wilson(functional,n),
                               "mean_hidden_pass_rate":_mean([(r.get("scores") or {}).get("hidden_pass_rate",0) for r in selected]),
                               "bug_location_rate":_mean([float((r.get("scores") or {}).get("names_buggy_function",False)) for r in selected])})
            elif task=="a2":
                recovered={(x["run_id"]):x for x in audit["a2_unwrapped_recovery"]}
                strict=sum(bool((r.get("scores") or {}).get("all_fields_correct")) for r in selected)
                content=[]
                for r in selected:
                    if r["parse_ok"]:content.append(float((r.get("scores") or {}).get("all_fields_correct",False)))
                    elif r["run_id"] in recovered:content.append(float(recovered[r["run_id"]]["content_correct"]))
                    else:content.append(0.0)
                common.update({"schema_operational_rate":sum(r["parse_ok"] for r in selected)/n,
                               "strict_all_fields_rate":strict/n,"strict_wilson95":_wilson(strict,n),
                               "recoverable_content_rate":_mean(content),"recoverable_content_correct":int(sum(content)),
                               "content_given_parse_f1":_mean([(r.get("scores") or {}).get("f1") for r in selected if r["parse_ok"]])})
            else:
                parsed=[r for r in selected if r["parse_ok"]]; v11={x["run_id"]:x["grounding_v1_1"] for x in audit["a3_grounding_reclassification"]}
                common.update({"operational_valid_rate":sum(r["status"]=="passed" for r in selected)/n,
                               "parsed_rate":len(parsed)/n,"ndcg_parsed_mean":_mean([r["scores"]["ndcg_at_5"] for r in parsed]),
                               "ndcg_all_calls_failure_zero":_mean([r["scores"]["ndcg_at_5"] if r["parse_ok"] else 0 for r in selected]),
                               "grounding_v1_parsed_mean":_mean([r["scores"]["grounding_accuracy"] for r in parsed]),
                               "grounding_v1_1_parsed_mean":_mean([v11[r["run_id"]] for r in parsed]),
                               "citation_consistency_all_calls":_mean([float((r.get("scores") or {}).get("citation_consistent",False)) for r in selected])})
            table[model]=common
        if task=="a1":rankings={"functional":_rank({m:v["functional_rate"] for m,v in table.items()}),"efficiency_latency":_rank({m:v["latency_median_s"] for m,v in table.items()},False)}
        elif task=="a2":rankings={"strict_operational_content":_rank({m:v["strict_all_fields_rate"] for m,v in table.items()}),"recoverable_content":_rank({m:v["recoverable_content_rate"] for m,v in table.items()}),"schema_operational":_rank({m:v["schema_operational_rate"] for m,v in table.items()})}
        else:rankings={"ndcg_parsed_only":_rank({m:v["ndcg_parsed_mean"] for m,v in table.items()}),"ndcg_all_calls":_rank({m:v["ndcg_all_calls_failure_zero"] for m,v in table.items()}),"grounding_v1":_rank({m:v["grounding_v1_parsed_mean"] for m,v in table.items()}),"grounding_v1_1":_rank({m:v["grounding_v1_1_parsed_mean"] for m,v in table.items()}),"operational":_rank({m:v["operational_valid_rate"] for m,v in table.items()})}
        result["tasks"][task]={"models":table,"rankings":rankings}
    result["conclusions"]=["A1 ranking is not stable enough to distinguish A from C; 10/10 versus 9/10 is within wide n=10 intervals.",
                           "A2 gpt-oss changes from last under strict pipeline success to tied-best content after recovering the missing wrapper; this is interface sensitivity, not improved extraction.",
                           "A3 parsed-only ranking hides truncation. Counting invalid outputs as zero changes the practical ranking sharply.",
                           "A3 grounding winner changes between frozen v1 and post-hoc v1.1 because documented paraphrases are reclassified."]
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT.relative_to(REPO)),"tasks":list(result["tasks"])},indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
