"""Offline CP4 integrity audit and results analysis for price-matched-v2."""
from __future__ import annotations

import argparse, hashlib, json, statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from experiments import run_price_matched_v2 as runner
from src.bedrock.client import estimate_input_tokens_upper
from src.bedrock.provenance import hash_file
from src.independent.v2_posthoc import (bootstrap_paired_difference, comparison_seed,
    exact_mcnemar, holm_adjust, wilcoxon_approx)

REPO=Path(__file__).resolve().parents[1]; RAW=REPO/"results/raw/price_matched_v2"
RUNS=REPO/"results/raw/runs"
VERIFICATION=REPO/"results/processed/independent_v2/price_matched_model_verification.json"
MANIFEST=REPO/"results/processed/independent_v2/price_matched_v2_protocol_manifest.json"
LEDGER=REPO/"results/raw/ledgers/price_matched_v2.json"
OUT=REPO/"results/processed/independent_v2/price_matched_v2_analysis.json"
REPORT=REPO/"results/reports/price_matched_v2_benchmark.md"
TASK_FILES={t:RAW/f"price_matched_v2_{t}.jsonl" for t in ("a1","a2","a3")}
PRIMARY_QUALITY={"a1":"functional_correct","a2":"content_correct","a3":"ndcg_at_5"}
FINAL_MODEL_ALIASES=("sonnet_4_6","kimi_k3","glm_5")
LABEL={"sonnet_4_6":"Sonnet 4.6","kimi_k3":"Kimi K3","glm_5":"GLM 5"}
PAIRS=(("sonnet_4_6","kimi_k3"),("sonnet_4_6","glm_5"),("kimi_k3","glm_5"))
FAMILIES={
 "a1_primary_mcnemar_majority":"3 pairs; case mean > 0.5 (strict majority); Holm",
 "a1_primary_wilcoxon":"3 pairs; case repeat means; Holm",
 "a2_primary_mcnemar_majority":"3 pairs; case mean > 0.5 (strict majority); Holm",
 "a2_primary_wilcoxon":"3 pairs; case repeat means; Holm",
 "a3_primary_wilcoxon":"3 pairs; case mean strict nDCG@5; Holm"}

def _jsonl(path): return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def _load_records(): return [r for t in TASK_FILES for r in _jsonl(TASK_FILES[t])]
def _prices():
 rows=json.loads(VERIFICATION.read_text())["models"]
 p={r["alias"]:{"input_per_mtok":r["input_per_mtok"],"output_per_mtok":r["output_per_mtok"]} for r in rows}
 if tuple(p)!=FINAL_MODEL_ALIASES: raise ValueError("verification model order changed")
 return p
def _cost(r,p):
 i,o=r.get("input_tokens"),r.get("output_tokens")
 if i is None or o is None:return None
 if i<0 or o<0:raise ValueError("token counts must be non-negative")
 q=r.get("reasoning_tokens")
 if q is not None and not 0<=q<=o:raise ValueError("reasoning_tokens must be included within output_tokens")
 return (i*p["input_per_mtok"]+o*p["output_per_mtok"])/1e6
def _quality(r,void=False):
 if r.get("status")=="void_infra": return 0.0 if void else None
 return float(r.get("scores",{}).get(PRIMARY_QUALITY[r["task"]],0))
def _pct(v,q):
 if not v:return None
 s=sorted(v); x=(len(s)-1)*q; a=int(x); b=min(a+1,len(s)-1)
 return s[a]+(s[b]-s[a])*(x-a)
def pareto_frontier(points:Iterable[dict[str,Any]])->list[str]:
 rows=list(points); out=[]
 for r in rows:
  if not any(o["mean_cost_per_call_usd"]<=r["mean_cost_per_call_usd"] and o["quality_mean"]>=r["quality_mean"] and (o["mean_cost_per_call_usd"]<r["mean_cost_per_call_usd"] or o["quality_mean"]>r["quality_mean"]) for o in rows):out.append(r)
 return [r["model_alias"] for r in sorted(out,key=lambda x:(x["mean_cost_per_call_usd"],-x["quality_mean"],x["model_alias"]))]

def analyze(records,prices):
 """Backward-compatible pure cost analysis used by protocol tests."""
 groups=defaultdict(list)
 for r in records:
  if r["model_alias"] not in prices:raise ValueError(f"no verified price for {r['model_alias']}")
  groups[r["task"],r["model_alias"]].append(r)
 cells=[]
 for (task,alias),rows in sorted(groups.items()):
  costs=[x for r in rows if (x:=_cost(r,prices[alias])) is not None]; qs=[x for r in rows if (x:=_quality(r)) is not None]
  actual=sum(costs); op=sum(bool(r.get("scores",{}).get("operational_success")) for r in rows)
  lat=[float(r["generation_ms"]) for r in rows if r.get("generation_ms") is not None]; reason=[r["reasoning_tokens"] for r in rows if r.get("reasoning_tokens") is not None]
  c={"task":task,"model_alias":alias,"calls":len(rows),"actual_cost_usd":actual,"cost_coverage_calls":len(costs),"cost_unavailable_calls":len(rows)-len(costs),"mean_cost_per_call_usd":actual/len(costs) if costs else None,"primary_quality_metric":PRIMARY_QUALITY[task],"quality_mean":statistics.fmean(qs) if qs else 0,"operational_successes_secondary":op,"cost_per_operational_success_usd_secondary":actual/op if op else None,"input_tokens":sum(r.get("input_tokens") or 0 for r in rows),"output_tokens_including_reasoning":sum(r.get("output_tokens") or 0 for r in rows),"reasoning_tokens_reported":sum(reason) if reason else None,"reasoning_token_coverage_calls":len(reason),"median_latency_ms":statistics.median(lat) if lat else None,"truncation_rate":sum(bool(r.get("truncated")) for r in rows)/len(rows),"format_failure_rate":sum(r.get("parse_ok") is False for r in rows)/len(rows)}
  if task in ("a1","a2"):
   n=sum(bool(r.get("scores",{}).get(PRIMARY_QUALITY[task])) for r in rows); c.update(primary_success_metric=PRIMARY_QUALITY[task],primary_successes=n,cost_per_primary_success_usd=actual/n if n else None)
  else:
   n=sum(bool(r.get("scores",{}).get("ranking_valid")) for r in rows); pts=sum(float(r.get("scores",{}).get("ndcg_at_5",0)) for r in rows); c.update(primary_success_metric=None,valid_responses=n,cost_per_valid_response_usd=actual/n if n else None,strict_ndcg_points=pts,cost_per_strict_ndcg_point_usd=actual/pts if pts else None)
  cells.append(c)
 front={t:{"cost_axis":"mean_cost_per_call_usd","quality_axis":PRIMARY_QUALITY[t],"model_aliases":pareto_frontier([c for c in cells if c["task"]==t and c["mean_cost_per_call_usd"] is not None])} for t in PRIMARY_QUALITY}
 return {"protocol":"price-matched-v2","final_models":list(FINAL_MODEL_ALIASES),"removed_model":{"model_alias":"grok_4_7","reason":"real invoke returned AccessDeniedException; excluded from all final analysis"},"cost_definition":"recorded input tokens * input price + recorded output tokens (including reasoning) * output price","cells":cells,"pareto_frontier_by_task":front}

def _reservations(inv,prices):
 plans={r["run_id"]:r for r in runner.plan_rows()}; cases={t:{c["case_id"]:c for c in runner.load_cases(t)} for t in TASK_FILES}; cells=defaultdict(lambda:{"attempts":0,"input_tokens":0,"output_tokens":0,"cost_usd":0.}); details=[]
 for x in inv:
  n=len(x.get("attempts") or [])
  if not n:continue
  p=plans[x["context"]["run_id"]]; prompt=runner.full_prompt(p["task"],cases[p["task"]][p["case_id"]]); it=estimate_input_tokens_upper([{"role":"user","content":[{"text":prompt}]}],None); pr=prices[p["model"]]; cost=(it*pr["input_per_mtok"]+runner.MAX_TOKENS*pr["output_per_mtok"])/1e6
  c=cells[p["task"],p["model"]]; c["attempts"]+=n;c["input_tokens"]+=n*it;c["output_tokens"]+=n*runner.MAX_TOKENS;c["cost_usd"]+=n*cost
  details.append({"run_id":p["run_id"],"task":p["task"],"case_id":p["case_id"],"model_alias":p["model"],"failed_attempts":n,"error_codes":[a["code"] for a in x["attempts"]],"reserved_cost_usd":n*cost})
 return dict(cells),details

def integrity_audit(records,all_inv,prices):
 errors=[]; plans={r["run_id"]:r for r in runner.plan_rows()}; rec={r["run_id"]:r for r in records}; primary=[x for x in all_inv if x["status"]!="parse_error"]; pinv={x["context"]["run_id"]:x for x in primary}; parse=[x for x in all_inv if x["status"]=="parse_error"]
 if len(records)!=810 or len(rec)!=810 or set(rec)!=set(plans):errors.append("record run IDs differ from frozen plan")
 if len(primary)!=810 or len(pinv)!=810 or set(pinv)!=set(plans):errors.append("invocation run IDs differ from frozen plan")
 mids={m["alias"]:m["callable_model_id"] for m in runner.models()}; temps={m["alias"]:m["temperature"] for m in runner.models()}; cases={t:{c["case_id"]:c for c in runner.load_cases(t)} for t in TASK_FILES}; hm=Counter(); identity=correspond=param=costm=missing=0
 for rid,r in rec.items():
  p=plans[rid]; case=cases[p["task"]][p["case_id"]]
  if (r["task"],r["case_id"],r["model_alias"],r["repeat_index"],r["model_id"])!=(p["task"],p["case_id"],p["model"],p["repeat"],mids[p["model"]]):identity+=1
  expected={"prompt_hash":hashlib.sha256(runner.render(p["task"],case).encode()).hexdigest(),"case_hash":hash_file(runner.DATA/p["task"]/"cases"/f"{p['case_id']}.json"),"config_hash":hashlib.sha256(json.dumps({"protocol":"price-matched-v2","maxTokens":runner.MAX_TOKENS,"temperature":temps[p["model"]],"temperature_field":"omitted" if p["model"]=="kimi_k3" else "sent","model":p["model"],"repeat":p["repeat"]},sort_keys=True).encode()).hexdigest()}
  for k,v in expected.items(): hm[k]+=r[k]!=v
  missing+=sum(not (REPO/a).exists() for a in r.get("artifacts",[]))
  x=pinv[rid]; setting={"maxTokens":runner.MAX_TOKENS};
  if p["model"]!="kimi_k3":setting["temperature"]=0.0
  param+=x["inference_settings"]!=setting; ids=r.get("invocation_ids") or []
  correspond+=not ((r["status"]=="void_infra" and not ids and x["status"]=="throttled_exhausted") or (r["status"]!="void_infra" and ids==[x["invocation_id"]] and x["status"]=="success" and (r["input_tokens"],r["output_tokens"])==(x["input_tokens"],x["output_tokens"])))
  if r["status"]!="void_infra":costm+=abs((_cost(r,prices[r["model_alias"]]) or 0)-r["cost_usd"])>1e-10 or abs(r["cost_usd"]-x["incurred_cost_usd"])>1e-10
 if any((identity,correspond,param,costm,missing)) or sum(hm.values()):errors.append(f"record checks failed identity={identity} correspondence={correspond} parameters={param} costs={costm} missing={missing} hashes={dict(hm)}")
 res,details=_reservations(primary,prices); failed=sum(d["failed_attempts"] for d in details); known=sum(_cost(r,prices[r["model_alias"]]) or 0 for r in records); reserved=sum(c["cost_usd"] for c in res.values()); ledger=json.loads(LEDGER.read_text()); manifest=json.loads(MANIFEST.read_text()); pre=manifest["pre_main_ledger_state"]
 successful_primary=sum(x["status"]=="success" for x in primary)
 checks={"calls":ledger["calls"]==pre["calls"]+successful_primary+failed,"failed_attempts":ledger["failed_attempts"]==4+failed,"cost":abs(ledger["spent_usd_priced"]-(pre["spent_usd_priced"]+known+reserved))<1e-9,"pending_empty":ledger["pending"]=={}}
 if not all(checks.values()):errors.append(f"ledger mismatch {checks}")
 now=runner.protocol_hashes(); frozen=manifest["hashes"]; diff={k for k in set(now)|set(frozen) if now.get(k)!=frozen.get(k) and k!="analysis_sha256"}
 if diff:errors.append(f"scientific hashes changed: {sorted(diff)}")
 duplicate=len(records)-len({(r["task"],r["case_id"],r["model_alias"],r["repeat_index"]) for r in records}); codes=sorted({c for d in details for c in d["error_codes"]})
 if duplicate or codes!=["EndpointConnectionError"]:errors.append("selective/unknown retry evidence")
 ki=sum(r.get("input_tokens") or 0 for r in records);ko=sum(r.get("output_tokens") or 0 for r in records);ri=sum(c["input_tokens"] for c in res.values());ro=sum(c["output_tokens"] for c in res.values())
 audit={"status":"pass" if not errors else "fail","errors":errors,"record_counts":{"records":len(records),"unique_run_ids":len(rec),"status":dict(Counter(r["status"] for r in records))},"correspondence":{"primary_invocations":len(primary),"parse_events":len(parse),"unique_primary_run_ids":len(pinv),"mismatches":correspond},"hashes":{"record_hash_mismatches":dict(hm),"scientific_protocol_hashes_match_frozen_manifest":not diff,"post_freeze_analysis_hash_expected_to_change":frozen.get("analysis_sha256")!=now.get("analysis_sha256")},"parameters":{"mismatches":param,"maxTokens":16384,"kimi_temperature_field":"omitted","sonnet_temperature":0.0,"glm_temperature":0.0},"retry_policy":{"logical_cell_duplicates":duplicate,"logical_cells_rerun":0,"automatic_failed_attempts":failed,"affected_logical_calls":len(details),"error_codes":codes,"details":details},"cost_reconciliation":{"checks":checks,"known_response_cost_usd":known,"failed_attempt_reservations_usd":reserved,"main_experiment_ledger_cost_usd":known+reserved,"pre_main_pilot_cost_usd":pre["spent_usd_priced"],"shared_ledger_cost_usd":ledger["spent_usd_priced"],"known_response_input_tokens":ki,"known_response_output_tokens":ko,"failed_attempt_reserved_input_tokens":ri,"failed_attempt_reserved_output_tokens":ro,"derived_pre_main_input_tokens":ledger["input_tokens"]-ki-ri,"derived_pre_main_output_tokens":ledger["output_tokens"]-ko-ro,"shared_ledger_calls":ledger["calls"],"shared_ledger_failed_attempts":ledger["failed_attempts"],"shared_ledger_pending":ledger["pending"]}}
 return audit,res

def _cells(records,prices,res,void=False):
 groups=defaultdict(list)
 for r in records:groups[r["task"],r["model_alias"]].append(r)
 out=[]
 for task in PRIMARY_QUALITY:
  for alias in FINAL_MODEL_ALIASES:
   scheduled=groups[task,alias]; rows=scheduled if void else [r for r in scheduled if r["status"]!="void_infra"]; q=[_quality(r,void=void) for r in rows]; scores=[r.get("scores",{}) for r in rows]; known=sum(_cost(r,prices[alias]) or 0 for r in scheduled); retry=res.get((task,alias),{"cost_usd":0,"attempts":0,"input_tokens":0,"output_tokens":0}); cost=known+retry["cost_usd"]; lat=[r["generation_ms"] for r in rows if r.get("generation_ms") is not None]; op=sum(bool(s.get("operational_success")) for s in scores); pts=sum(q)
   c={"task":task,"model_alias":alias,"model_label":LABEL[alias],"scheduled":90,"analyzed_denominator":len(rows),"void_infra":sum(r["status"]=="void_infra" for r in scheduled),"primary_metric":PRIMARY_QUALITY[task],"primary_sum":pts,"primary_mean":statistics.fmean(q),"operational_successes":op,"operational_rate":op/len(rows),"parse_failures":sum(r.get("parse_ok") is False for r in rows),"format_failure_rate":sum(r.get("parse_ok") is False for r in rows)/len(rows),"truncations":sum(bool(r.get("truncated")) for r in rows),"truncation_rate":sum(bool(r.get("truncated")) for r in rows)/len(rows),"known_response_cost_usd":known,"retry_reservation_cost_usd":retry["cost_usd"],"actual_execution_cost_usd":cost,"mean_cost_per_call_usd":cost/90,"input_tokens_known":sum(r.get("input_tokens") or 0 for r in scheduled),"output_tokens_including_reasoning_known":sum(r.get("output_tokens") or 0 for r in scheduled),"failed_attempt_reserved_input_tokens":retry["input_tokens"],"failed_attempt_reserved_output_tokens":retry["output_tokens"],"reasoning_tokens_reported":sum(r.get("reasoning_tokens") or 0 for r in scheduled),"reasoning_token_coverage_calls":sum(r.get("reasoning_tokens") is not None for r in scheduled),"latency_ms":{"n":len(lat),"median":statistics.median(lat),"p95":_pct(lat,.95),"mean":statistics.fmean(lat)}}
   if task=="a1": sec={"hidden_pass_rate":statistics.fmean(float(s.get("hidden_pass_rate",0)) for s in scores),"bug_location_recall":statistics.fmean(float(s.get("bug_location_recall",0)) for s in scores)}; n=sum(bool(s.get("functional_correct")) for s in scores);c.update(secondary_metrics=sec,primary_successes=n,cost_per_correct_answer_usd=cost/n if n else None)
   elif task=="a2": sec={"content_f1":statistics.fmean(float(s.get("content_f1",0)) for s in scores),"schema_compliant":statistics.fmean(float(bool(s.get("schema_compliant"))) for s in scores)};n=sum(bool(s.get("content_correct")) for s in scores);c.update(secondary_metrics=sec,primary_successes=n,cost_per_correct_answer_usd=cost/n if n else None)
   else: sec={"deduplicated_ndcg_at_5":statistics.fmean(float(s.get("deduplicated_ndcg_at_5",0)) for s in scores),"grade2_recall_at_5":statistics.fmean(float(s.get("grade2_recall_at_5",0)) for s in scores),"grounding_r1_all_citations":statistics.fmean(float(s.get("evidence_grounding",0)) for s in scores),"grounding_r2_any_citation":statistics.fmean(float(s.get("evidence_grounding_any_citation",0)) for s in scores),"citation_validity":statistics.fmean(float(s.get("citation_validity",0)) for s in scores)};n=sum(bool(s.get("ranking_valid")) for s in scores);sec["ranking_valid_rate"]=n/len(rows);c.update(secondary_metrics=sec,valid_responses=n,cost_per_valid_response_usd=cost/n if n else None,cost_per_strict_ndcg_point_usd=cost/pts if pts else None)
   out.append(c)
 return out

def _stability(records):
 groups=defaultdict(list)
 for r in records:groups[r["task"],r["model_alias"]].append(r)
 out=[]
 for (task,alias),rows in sorted(groups.items()):
  reps=[];by=defaultdict(list)
  for i in range(3):
   v=[x for r in rows if r["repeat_index"]==i and (x:=_quality(r)) is not None];reps.append({"repeat_index":i,"n":len(v),"mean":statistics.fmean(v)})
  for r in rows:
   if (x:=_quality(r)) is not None:by[r["case_id"]].append(x)
  complete=[v for v in by.values() if len(v)==3]; sds=[statistics.pstdev(v) for v in complete];means=[x["mean"] for x in reps]
  out.append({"task":task,"model_alias":alias,"repeats":reps,"between_repeat_mean_range":max(means)-min(means),"cases_total":len(by),"complete_three_repeat_cases":len(complete),"incomplete_cases":len(by)-len(complete),"exactly_consistent_complete_cases":sum(max(v)-min(v)<1e-12 for v in complete),"exact_consistency_rate":sum(max(v)-min(v)<1e-12 for v in complete)/len(complete),"mean_within_case_population_sd":statistics.fmean(sds),"max_within_case_population_sd":max(sds)})
 return out

def _output_composition(records):
 """Describe returned text composition; char/4 values are approximations, not usage tokens."""
 groups=defaultdict(list)
 for r in records:groups[r["task"],r["model_alias"]].append(r)
 rows=[]
 for task in PRIMARY_QUALITY:
  for alias in FINAL_MODEL_ALIASES:
   scheduled=groups[task,alias];reasoning=[r["reasoning_chars"] for r in scheduled if r.get("reasoning_chars") is not None];answers=[];billed=[]
   for r in scheduled:
    p=RUNS/r["run_id"]/"response.txt"
    if p.exists():answers.append(len(p.read_text()))
    if r.get("output_tokens") is not None:billed.append(r["output_tokens"])
   mr=statistics.median(reasoning) if reasoning else None;ma=statistics.median(answers) if answers else None
   rows.append({"task":task,"model_alias":alias,"scheduled":len(scheduled),"reasoning_chars_coverage":len(reasoning),"final_answer_chars_coverage":len(answers),"billed_output_tokens_coverage":len(billed),"median_reasoning_chars":mr,"median_final_answer_chars":ma,"median_billed_output_tokens":statistics.median(billed) if billed else None,"median_reasoning_chars_approx_tokens_at_4_chars_per_token":mr/4 if mr is not None else None,"median_final_answer_chars_approx_tokens_at_4_chars_per_token":ma/4 if ma is not None else None,"sum_of_component_medians_approx_tokens_at_4_chars_per_token":(mr+ma)/4 if mr is not None and ma is not None else None,"reasoning_share_of_component_median_chars":mr/(mr+ma) if mr is not None and ma is not None and mr+ma else None})
 by={(r["task"],r["model_alias"]):r for r in rows};comparison=[]
 for task in PRIMARY_QUALITY:
  k=by[task,"kimi_k3"];s=by[task,"sonnet_4_6"]
  comparison.append({"task":task,"kimi_reasoning_chars_coverage":k["reasoning_chars_coverage"],"kimi_scheduled":k["scheduled"],"kimi_median_reasoning_chars":k["median_reasoning_chars"],"kimi_median_final_answer_chars":k["median_final_answer_chars"],"sonnet_median_final_answer_chars":s["median_final_answer_chars"],"kimi_to_sonnet_final_answer_median_char_ratio":k["median_final_answer_chars"]/s["median_final_answer_chars"],"kimi_sum_of_component_medians_approx_tokens":k["sum_of_component_medians_approx_tokens_at_4_chars_per_token"],"kimi_median_billed_output_tokens":k["median_billed_output_tokens"]})
 return {"evidence":"reasoning_chars from saved records; final answer characters from immutable response.txt artifacts","char_to_token_approximation":4.0,"approximation_warning":"Character-derived token values are descriptive approximations. Bedrock did not report a separate reasoning-token count; billed output_tokens remains authoritative.","rows":rows,"kimi_vs_sonnet":comparison}

def _stats(records,void=False):
 fam=defaultdict(list)
 for task in PRIMARY_QUALITY:
  vals={a:defaultdict(list) for a in FINAL_MODEL_ALIASES}
  for r in records:
   if r["task"]==task and (x:=_quality(r,void=void)) is not None:vals[r["model_alias"]][r["case_id"]].append(x)
  means={a:{c:statistics.fmean(v) for c,v in d.items()} for a,d in vals.items()}
  for a,b in PAIRS:
   cases=sorted(set(means[a])&set(means[b]));x=[means[a][c] for c in cases];y=[means[b][c] for c in cases];pair=f"{a}_vs_{b}";boot=bootstrap_paired_difference(x,y,seed=comparison_seed(task,"void" if void else "main",pair));w=wilcoxon_approx(x,y);base={"pair":pair,"first":a,"second":b,"n_cases":len(cases),"first_mean":statistics.fmean(x),"second_mean":statistics.fmean(y),"paired_bootstrap":boot}
   fam[f"{task}_primary_wilcoxon"].append({**base,"test":"Wilcoxon signed-rank normal approximation",**w})
   if task in ("a1","a2"):fam[f"{task}_primary_mcnemar_majority"].append({**base,"test":"exact McNemar on strict case majority (mean > 0.5)",**exact_mcnemar([v>.5 for v in x],[v>.5 for v in y])})
 for f,rows in fam.items():
  adj=holm_adjust((r["pair"],r["p_value"]) for r in rows)
  for r in rows:r["holm_adjusted_p_value"]=adj[r["pair"]]
 return {"view":"void_as_failure" if void else "void_excluded","unit":"case-level mean across available repeats","families_defined_before_testing":FAMILIES,"families":{f:fam[f] for f in FAMILIES}}

def build_full_analysis():
 records=_load_records();prices=_prices();audit,res=integrity_audit(records,_jsonl(RAW/"invocations.jsonl"),prices)
 if audit["status"]!="pass":raise ValueError(audit["errors"])
 main=_cells(records,prices,res);sens=_cells(records,prices,res,True);front={}
 for t in PRIMARY_QUALITY:
  points=[{"model_alias":c["model_alias"],"mean_cost_per_call_usd":c["mean_cost_per_call_usd"],"quality_mean":c["primary_mean"]} for c in main if c["task"]==t];front[t]={"cost_axis":"actual execution cost / 90 scheduled calls","quality_axis":PRIMARY_QUALITY[t],"model_aliases":pareto_frontier(points),"points":points}
 old=json.loads((REPO/"results/processed/independent_v2/analysis.json").read_text());post=json.loads((REPO/"results/processed/independent_v2/posthoc.json").read_text());oldv={"a1":old["cells"]["a1|A"]["primary"]["rate"],"a2":old["cells"]["a2|A"]["primary"]["rate"],"a3":post["cells"]["a3|A"]["ranking_ndcg"]["strict_invalid_zero"]};new={(c["task"],c["model_alias"]):c for c in main}
 return {"analysis_version":"price-matched-v2-cp4-1.1","analysis_date":"2026-11-19","protocol":"price-matched-v2","frozen_tag":"price-matched-v2-frozen-v1.1","scope":{"models":list(FINAL_MODEL_ALIASES),"scheduled_records":810,"tasks":3,"cases_per_task":30,"repeats":3,"account_constraint":"three specific callable models; no vendor-wide claim","price_range_disclosure":"approximately 4.3x","selection_disclosures":["GLM 5 chosen for generation match","Kimi K3 omitted temperature after pilot rejection","Grok 4.7 removed after real-invoke AccessDeniedException"]},"integrity_audit":audit,"void_infra_policy":{"frozen_protocol_explicit_rule_found":False,"main_analysis":"exclude two infrastructure-void cells with denominators shown","sensitivity":"count void cells as primary and operational failures","rerun_performed":False,"rerun_recommendation":"do not rerun for the frozen primary analysis"},"void_infra_records":[{k:r.get(k) for k in ("run_id","task","case_id","model_alias","repeat_index","failure_detail")} for r in records if r["status"]=="void_infra"],"main_analysis_void_excluded":{"cells":main,"pareto_frontier_by_task":front,"paired_statistics":_stats(records)},"sensitivity_void_as_failure":{"cells":sens,"paired_statistics":_stats(records,True)},"repeat_stability":_stability(records),"output_composition":_output_composition(records),"version_comparison_original_v1":{"warning":"Different protocols; descriptive and not directly comparable.","bridge_model":"Sonnet 4.6","rows":[{"task":t,"metric":PRIMARY_QUALITY[t],"original_v1_single_run":oldv[t],"price_matched_v2_three_repeat_mean":new[t,"sonnet_4_6"]["primary_mean"]} for t in PRIMARY_QUALITY]}}

def _f(x,d=3):return "—" if x is None else f"{x:.{d}f}"
def render_report(r):
 a=r["integrity_audit"];cells=r["main_analysis_void_excluded"]["cells"];sens={(c["task"],c["model_alias"]):c for c in r["sensitivity_void_as_failure"]["cells"]};L=["# Price-matched-v2 benchmark results","","This compares three specific models callable under this account, not vendors. The selected set spans approximately 4.3× in price. GLM 5 was chosen for generation match; Kimi K3 ran without temperature after the pilot rejected that field; Grok 4.7 was removed after a real-invoke AccessDeniedException.","","## Integrity audit","",f"**{a['status'].upper()}** — 810 records matched 810 primary invocations and the frozen plan; no logical cell was selectively rerun. The ledger has {a['cost_reconciliation']['shared_ledger_calls']} attempts and totals ${a['cost_reconciliation']['shared_ledger_cost_usd']:.6f} including pilot.","","| Component | USD |","|---|---:|",f"| Main known responses | {a['cost_reconciliation']['known_response_cost_usd']:.6f} |",f"| Main failed-attempt reserves | {a['cost_reconciliation']['failed_attempt_reservations_usd']:.6f} |",f"| Main total | {a['cost_reconciliation']['main_experiment_ledger_cost_usd']:.6f} |",f"| Pilot/re-pilot | {a['cost_reconciliation']['pre_main_pilot_cost_usd']:.6f} |",f"| Shared total | {a['cost_reconciliation']['shared_ledger_cost_usd']:.6f} |","","Hashes, IDs and parameters matched: maxTokens 16384; Sonnet/GLM temperature 0; Kimi temperature omitted. Only EndpointConnectionError caused automatic retries.","","## Main results (voids excluded)","","| Task | Model | n/90 | Primary | Operational | Key secondary | Cost | Cost/success or point | Median latency |","|---|---|---:|---:|---:|---|---:|---:|---:|"]
 for c in cells:
  s=c["secondary_metrics"]
  if c["task"]=="a1":sec=f"hidden pass {_f(s['hidden_pass_rate'])}; bug location {_f(s['bug_location_recall'])}";cp=c["cost_per_correct_answer_usd"]
  elif c["task"]=="a2":sec=f"content F1 {_f(s['content_f1'])}; schema {_f(s['schema_compliant'])}";cp=c["cost_per_correct_answer_usd"]
  else:sec=f"dedup {_f(s['deduplicated_ndcg_at_5'])}; R1 {_f(s['grounding_r1_all_citations'])}; R2 {_f(s['grounding_r2_any_citation'])}; citations {_f(s['citation_validity'])}";cp=c["cost_per_strict_ndcg_point_usd"]
  L.append(f"| {c['task'].upper()} | {c['model_label']} | {c['analyzed_denominator']}/90 | {_f(c['primary_mean'])} | {_f(c['operational_rate'])} | {sec} | ${c['actual_execution_cost_usd']:.3f} | ${cp:.4f} | {_f(c['latency_ms']['median']/1000)} s |")
 L += ["","A3 cost per valid response and all token/latency fields are in the JSON.","","## Output composition (descriptive)","","Kimi returned reasoning text for all 90/90 records in each task. Its extra billed output mainly consists of that returned reasoning text; Bedrock did not provide a separate reasoning-token count. The token equivalents below use an explicitly approximate 4 characters/token conversion, while billed output tokens remain authoritative. Kimi's final-answer length is close to Sonnet's.","","| Task | Kimi reasoning chars (median) | Kimi final-answer chars (median) | Sonnet final-answer chars (median) | Kimi answer + reasoning, approx tokens | Kimi billed output tokens (median) |","|---|---:|---:|---:|---:|---:|"]
 for x in r["output_composition"]["kimi_vs_sonnet"]:L.append(f"| {x['task'].upper()} | {x['kimi_median_reasoning_chars']:,.1f} | {x['kimi_median_final_answer_chars']:,.1f} | {x['sonnet_median_final_answer_chars']:,.1f} | {x['kimi_sum_of_component_medians_approx_tokens']:,.1f} | {x['kimi_median_billed_output_tokens']:,.1f} |")
 L += ["","Source: `output_composition`; character-derived token values are approximations, not provider-reported reasoning tokens.","","## Void sensitivity","","The protocol did not specify post-run handling. Main results exclude the two A1 infrastructure voids; sensitivity counts them as failures. They were not rerun, and no rerun is recommended for the frozen primary analysis.","","| A1 model | Excluded | Failure sensitivity |","|---|---:|---:|"]
 for m in FINAL_MODEL_ALIASES:
  x=next(c for c in cells if c["task"]=="a1" and c["model_alias"]==m);y=sens["a1",m];L.append(f"| {LABEL[m]} | {_f(x['primary_mean'])} (n={x['analyzed_denominator']}) | {_f(y['primary_mean'])} (n=90) |")
 L += ["","## Repeat stability","","| Task | Model | Repeat means (n) | Range | Complete cases | Exact consistency |","|---|---|---|---:|---:|---:|"]
 for x in r["repeat_stability"]:L.append(f"| {x['task'].upper()} | {LABEL[x['model_alias']]} | "+", ".join(f"{_f(z['mean'])} ({z['n']})" for z in x["repeats"])+f" | {_f(x['between_repeat_mean_range'])} | {x['complete_three_repeat_cases']} | {_f(x['exact_consistency_rate'])} |")
 L += ["","## Paired case-level statistics","","Families were defined before testing; Holm correction is within each three-pair family. Effects use case-level repeat means; bootstrap intervals use 10,000 paired draws.","","| Family | Pair | Difference | 95% CI | raw p | Holm p |","|---|---|---:|---|---:|---:|"]
 for f,rows in r["main_analysis_void_excluded"]["paired_statistics"]["families"].items():
  for x in rows:
   b=x["paired_bootstrap"];L.append(f"| {f} | {LABEL[x['first']]} − {LABEL[x['second']]} | {b['difference']:+.3f} | [{b['ci95'][0]:+.3f}, {b['ci95'][1]:+.3f}] | {x['p_value']:.4f} | {x['holm_adjusted_p_value']:.4f} |")
 L += ["","## Quality–cost Pareto frontiers",""]
 for t,x in r["main_analysis_void_excluded"]["pareto_frontier_by_task"].items():L.append(f"- {t.upper()}: "+", ".join(LABEL[m] for m in x["model_aliases"]))
 L += ["","## Original-v1 bridge (descriptive only)","","Different protocols are not directly comparable; Sonnet 4.6 is the bridge.","","| Task | Metric | original-v1 | price-matched-v2 |","|---|---|---:|---:|"]
 for x in r["version_comparison_original_v1"]["rows"]:L.append(f"| {x['task'].upper()} | {x['metric']} | {_f(x['original_v1_single_run'])} | {_f(x['price_matched_v2_three_repeat_mean'])} |")
 return "\n".join(L)+"\n"

def main(argv=None):
 argparse.ArgumentParser(description=__doc__).parse_args(argv);r=build_full_analysis();OUT.parent.mkdir(parents=True,exist_ok=True);REPORT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n");REPORT.write_text(render_report(r));print(json.dumps({"analysis":str(OUT.relative_to(REPO)),"report":str(REPORT.relative_to(REPO)),"audit":r["integrity_audit"]["status"]},indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
