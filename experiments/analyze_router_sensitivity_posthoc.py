"""Post-hoc metric-preference sensitivity over saved v3 decision candidates.

The frozen Router and traces are not called or changed.  This script applies explicit
alternative selection rules to candidate estimates already stored in each trace.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
ROUTING=REPO/"results/routing/v3_primary"
OUT=REPO/"results/processed/router_sensitivity_posthoc.json"

CRITERIA={
    "frozen_v3":{"min_feasibility":0.5,"analysis_min":0.9,"unsupported_max":1.0,"preference":["end_to_end_ms","total_tokens"]},
    "feasibility_only":{"min_feasibility":0.5,"analysis_min":None,"unsupported_max":None,"preference":["end_to_end_ms","total_tokens"]},
    "strict_quality":{"min_feasibility":2/3,"analysis_min":1.0,"unsupported_max":0.0,"preference":["end_to_end_ms","total_tokens"]},
    "token_first":{"min_feasibility":0.5,"analysis_min":0.9,"unsupported_max":1.0,"preference":["total_tokens","end_to_end_ms"]},
    "maximum_reliability":{"min_feasibility":0.0,"analysis_min":None,"unsupported_max":None,"preference":["neg_feasibility","end_to_end_ms","total_tokens"]},
}


def _eligible(candidate, rule):
    if candidate.get("feasibility_prob",0)<rule["min_feasibility"]:return False
    if rule["analysis_min"] is not None and candidate.get("quality",{}).get("analysis.numerical_accuracy",-1)<rule["analysis_min"]:return False
    if rule["unsupported_max"] is not None and candidate.get("quality",{}).get("reporting.unsupported_claim_count",float("inf"))>rule["unsupported_max"]:return False
    return True


def _select(candidates,rule):
    eligible=[candidate for candidate in candidates if _eligible(candidate,rule)]
    if not eligible:return None
    def key(candidate):
        values=[]
        for metric in rule["preference"]:
            if metric=="neg_feasibility":values.append(-candidate.get("feasibility_prob",0));continue
            value=candidate.get(metric);values.append(float("inf") if value is None else value)
        return tuple(values)+(candidate["path_id"],)
    return min(eligible,key=key)["path_id"]


def main() -> int:
    traces=[json.loads(line) for line in (ROUTING/"traces.jsonl").read_text().splitlines() if line.strip()]
    rows=[]
    for trace in traces:
        selections={name:(trace["selected_path_id"] if name=="frozen_v3" else _select(trace["candidates"],rule)) for name,rule in CRITERIA.items()}
        rows.append({"trace_id":trace["trace_id"],"strategy":trace["strategy"],"target_project":trace["target_project"],"selections":selections,
                     "changed_vs_frozen":{name:value!=selections["frozen_v3"] for name,value in selections.items() if name!="frozen_v3"}})
    summary={}
    for name in CRITERIA:
        selected=[row["selections"][name] for row in rows]
        summary[name]={"selected":len(selected)-selected.count(None),"no_feasible":selected.count(None),"path_counts":dict(Counter(value for value in selected if value is not None)),
                       "changes_vs_frozen":sum(row["selections"][name]!=row["selections"]["frozen_v3"] for row in rows)}
    faith=[json.loads(line) for line in (ROUTING/"computational_faithfulness.jsonl").read_text().splitlines() if line.strip()]
    empirical=json.loads((ROUTING/"empirical_validity.json").read_text())
    counterfactual={strategy:{quantity:stats for quantity,stats in body["per_quantity"].items() if quantity in {"feasible","feasibility_agreement:selected","feasibility_agreement:alternative","n_switches"}}
                    for strategy,body in empirical["by_strategy"].items()}
    v31a=json.loads((REPO/"results/processed/v3_1_rescore/expA_stage_v3_reporting.json").read_text())
    v31b=json.loads((REPO/"results/processed/v3_1_rescore/expB_paths_v3_reporting.json").read_text())
    report={"mode":"post-hoc sensitivity; not prospective validation","frozen_router_modified":False,"criteria":CRITERIA,"summary":summary,"trace_comparison":rows,
            "computational_faithfulness":{"checks":len(faith),"all_claims_consistent":all(x["claims_consistent"]==x["claims_checked"] for x in faith),"all_replay_matches":all(x["replay_matches_selection"] for x in faith)},
            "counterfactual_robustness":counterfactual,
            "validator_v3_to_v3_1":{"experiment_A":v31a["summary"],"experiment_B":v31b["summary"],
                                     "interpretation":"v3.1 changes reporting pass labels, so any route based on strict end-to-end feasibility may change; frozen prospective traces and counterfactuals remain primary and were not recomputed."},
            "limitations":["Alternative selections reuse frozen candidate estimates; they are not new prospective traces.","v3.1 was designed after outputs were observed and is shown only as a secondary sensitivity view.","Counterfactual quality metrics are often undefined when executed paths are infeasible; feasibility conclusions are substantially less accurate than switch-count conclusions."]}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT.relative_to(REPO)),"traces":len(rows),"changes":{k:v["changes_vs_frozen"] for k,v in summary.items()}},indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
