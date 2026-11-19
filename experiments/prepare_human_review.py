"""Create the deterministic, blinded 18-item independent-v1 review packet."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
OUT=REPO/"results/review"
SEED=20261118
FILES={"a1":"indepA1_debug_v1.jsonl","a2":"indepA2_extract_v1.jsonl","a3":"indepA3_lit_v1.jsonl"}
MODEL_NAMES={"A":"Claude Sonnet 4.6","B":"Amazon Nova Pro","C":"OpenAI gpt-oss-120b"}
ROSTER={
    "a1":{"A":["a1_05_append_item","a1_10_merge_intervals"],"B":["a1_09_top_k","a1_10_merge_intervals"],"C":["a1_03_median","a1_08_parse_duration"]},
    "a2":{"A":["a2_04_purchase_order","a2_05_rental_listing"],"B":["a2_04_purchase_order","a2_05_rental_listing"],"C":["a2_01_clinical_trial","a2_02_incident_report"]},
    "a3":{"A":["a3_01","a3_09"],"B":["a3_03","a3_08"],"C":["a3_05","a3_06"]},
}


def _records(task):
    path=REPO/"results/raw/independent"/FILES[task]
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _case(task, case_id):
    return json.loads((REPO/f"datasets/independent/{task}/cases/{case_id}.json").read_text())


def _reference(task, case):
    if task=="a1":
        return json.dumps({"spec":case["spec"],"reference_solution":case["reference"],"hidden_checks":case["hidden"]},indent=2)
    if task=="a2":
        return json.dumps({"gold_fields":case["gold"],"missing_fields":case["missing_fields"]},indent=2)
    ideal=sorted(case["relevance"],key=lambda doc:(-case["relevance"][doc],doc))[:5]
    return json.dumps({"ideal_top_five_by_grade_then_id":ideal,"relevance_grades":case["relevance"],"document_facts":case["facts"]},indent=2)


def main() -> int:
    selected=[]
    for task,models in ROSTER.items():
        lookup={(r["model_alias"],r["case_id"]):r for r in _records(task)}
        for model,cases in models.items():
            for case_id in cases: selected.append((task,model,lookup[(model,case_id)]))
    random.Random(SEED).shuffle(selected)
    worksheet=[]; key=[]
    for index,(task,model,record) in enumerate(selected,1):
        sample_id=f"HR-{index:03d}"; case=_case(task,record["case_id"]); run_dir=REPO/"results/raw/runs"/record["run_id"]
        worksheet.append({
            "anonymous_sample_id":sample_id,
            "task_category":{"a1":"Python debugging","a2":"Information extraction","a3":"Controlled literature review"}[task],
            "task_instructions":(run_dir/"prompt.txt").read_text(),
            "relevant_input":json.dumps({k:v for k,v in case.items() if k not in {"gold","reference","hidden","facts","relevance","verification"}},indent=2),
            "model_output":(run_dir/"response.txt").read_text(),
            "reference_answer_or_supporting_evidence":_reference(task,case),
            "human_overall_judgment":"",
            "human_content_correct":"",
            "human_schema_compliant":"",
            "human_operationally_usable":"",
            "human_ranking_quality_0_to_3":"",
            "human_grounding_quality_0_to_3":"",
            "human_citation_accuracy_0_to_3":"",
            "error_classification":"",
            "reviewer_notes":"",
        })
        selection_reason=("functional failure or diagnostic localization" if task=="a1" else
                          "content/schema separation and unit handling" if task=="a2" else
                          "ranking, truncation, or v1/v1.1 scorer disagreement")
        key.append({"anonymous_sample_id":sample_id,"task":task,"case_id":record["case_id"],"model_alias":model,
                    "model_name":MODEL_NAMES[model],"model_id":record["model_id"],"run_id":record["run_id"],
                    "original_status":record["status"],"original_failure_type":record.get("failure_type"),
                    "original_scores_json":json.dumps(record.get("scores") or {},sort_keys=True),"selection_reason":selection_reason})
    OUT.mkdir(parents=True,exist_ok=True)
    for name,rows in (("human_review_worksheet.csv",worksheet),("human_review_key.csv",key)):
        with (OUT/name).open("w",newline="") as handle:
            writer=csv.DictWriter(handle,fieldnames=list(rows[0]),lineterminator="\n");writer.writeheader();writer.writerows(rows)
    manifest={"protocol":"independent-v1 blinded spot-check","seed":SEED,"sample_count":len(selected),
              "strata":{"tasks":3,"models":3,"per_task_model_cell":2},"roster":ROSTER,
              "worksheet_sha256":hashlib.sha256((OUT/"human_review_worksheet.csv").read_bytes()).hexdigest(),
              "key_sha256":hashlib.sha256((OUT/"human_review_key.csv").read_bytes()).hexdigest(),
              "warning":"Do not join the key to the worksheet until human judgments are locked."}
    (OUT/"human_review_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"worksheet":str((OUT/'human_review_worksheet.csv').relative_to(REPO)),"items":len(selected)},indent=2));return 0


if __name__=="__main__":
    raise SystemExit(main())
