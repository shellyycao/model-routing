"""Post-hoc / exploratory failure-cause taxonomy of non-passed stage records.

Rules: docs/FAILURE_TAXONOMY_RULES.md (committed before any count). Reads saved records only.
Writes only: results/processed/failure_taxonomy_posthoc.json, results/reports/failure_taxonomy_posthoc.md,
results/review/failure_taxonomy_residual_sample_ids.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from experiments.analyze_corrected_q2 import CONTINUATIONS, read_jsonl
from experiments.analyze_diagnostics_posthoc import GROUPS as DGROUPS, INT64_ERROR
from experiments.analyze_corrected_view import load_records
from experiments.analyze_router_relabel import wilson
from src.bedrock.provenance import hash_file

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "docs/FAILURE_TAXONOMY_RULES.md"
DIAGNOSTICS = REPO / "results/processed/diagnostics_posthoc.json"
OUT = REPO / "results/processed/failure_taxonomy_posthoc.json"
REPORT = REPO / "results/reports/failure_taxonomy_posthoc.md"
SAMPLE = REPO / "results/review/failure_taxonomy_residual_sample_ids.json"
SEED = "failure-taxonomy-residual-review-v1"
PER_STRATUM = 6
NON_PASSED = {"failed", "infra_error", "blocked_by_invalid_artifact", "not_run_upstream_failure"}
CATEGORIES = ["int64_serialization", "truncation", "infrastructure_void", "blocked_or_not_run_upstream",
              "reporting_rounding_only", "known_q7_false_reject", "other_execution_error",
              "parse_or_schema_failure", "genuine_validator_mismatch", "unexplained_residual"]
ARTIFACT_LIKE = {"int64_serialization", "infrastructure_void", "blocked_or_not_run_upstream",
                 "reporting_rounding_only", "known_q7_false_reject"}
MODEL_LIKE = {"truncation", "other_execution_error", "parse_or_schema_failure", "genuine_validator_mismatch"}
EXC_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Exit))\b")
STAGE_ORDER = {"cleaning": 0, "analysis": 1, "reporting": 2}


def val(x):
    return getattr(x, "value", x)


def failed_mandatory(validation) -> set[str]:
    if validation is None:
        return set()
    return {c.name for c in validation.checks if c.mandatory and not c.passed}


def exception_class(stage) -> str:
    texts = []
    if stage.execution is not None and stage.execution.stderr:
        texts.append(stage.execution.stderr)
    if stage.failure_detail:
        texts.append(stage.failure_detail)
    for t in texts:
        lines = [ln for ln in t.splitlines() if ln.strip() and ":" in ln]
        if lines:
            m = EXC_RE.match(lines[-1].strip())
            if m:
                return m.group(1)
    return "no_exception_class"


def matches(unit: dict, ev: dict) -> list[tuple[int, str]]:
    """All (rule_number, subclass) whose conditions match, in rule order."""
    s = unit["stage_rec"]
    status, ft = val(s.status), val(s.failure_type)
    detail = s.failure_detail or ""
    failed = status == "failed"
    out: list[tuple[int, str]] = []
    key3 = (unit["group"], unit["part"], unit["run_id"])
    if failed and s.invocation_ids and INT64_ERROR in detail:
        out.append((1, "int64"))
    stops = [ev["stop"].get(i) for i in s.invocation_ids]
    if failed and (ft == "truncated" or "max_tokens" in stops):
        out.append((2, "failure_type_truncated" if ft == "truncated" else "stop_reason_max_tokens"))
    exec_status = val(s.execution.status) if s.execution is not None else None
    if status == "infra_error" or ft in ("infra", "api_error") or exec_status == "sandbox_unavailable":
        sub = [ft or status]
        if "docker" in detail or "Docker" in detail:
            sub.append("docker")
        if unit.get("retained_void_rerun"):
            sub.append("rerun_audit")
        out.append((3, "+".join(sub)))
    if status in ("blocked_by_invalid_artifact", "not_run_upstream_failure"):
        out.append((4, status))
    fm = failed_mandatory(s.validation)
    if (unit["stage"] == "reporting" and failed and s.validation is not None
            and fm == {"derived_values_correct"} and key3 in ev["rounding"]):
        out.append((5, "stated_precision_half_up"))
    if key3 in ev["q7"]:
        out.append((6, "q7"))
    if failed and (ft in ("execution_error", "timeout", "security_violation")
                   or exec_status in ("runtime_error", "test_failure", "timeout", "security_violation")):
        sub = ft if ft in ("timeout", "security_violation") else exception_class(s)
        out.append((7, sub))
    if failed and (ft in ("parse_error", "invalid_output") or s.parse_ok is False or s.structural_ok is False):
        out.append((8, ft if ft in ("parse_error", "invalid_output")
                    else ("parse_ok_false" if s.parse_ok is False else "structural_ok_false")))
    if failed and ft == "validation_failed" and s.validation is not None and not s.validation.hard_pass and fm:
        out.append((9, "derived_values_not_rounding" if fm == {"derived_values_correct"} else "+".join(sorted(fm))))
    return out


def classify(unit: dict, ev: dict) -> tuple[str, str, list[int]]:
    m = matches(unit, ev)
    if not m:
        return "unexplained_residual", "unmatched", []
    rule, sub = m[0]
    return CATEGORIES[rule - 1], sub, [r for r, _ in m]


def load_evidence(group: str) -> dict:
    d = json.loads(DIAGNOSTICS.read_text())
    rs = d["rounding_sensitivity"]
    def key(r):
        return (group, "part_a" if r["part"] == "A" else "part_b", r["run_id"])
    rounding = {key(r) for r in rs["derived_values_only_candidates"] if r["recoverable"] and r["group"] == group}
    q7 = {key(r) for r in rs["known_q7_v31_false_rejects"] if r["group"] == group}
    replay = {(r["group"], "part_a" if r["part"] == "A" else "part_b", r["run_id"], r["stage"])
              for r in d["serialization_replay"]["records"] if r["would_pass_without_serialization_bug"]}
    cfg = DGROUPS[group]
    stop = {}
    for row in read_jsonl(cfg["invocations"]):
        if row["context"]["experiment_id"] in cfg["experiments"]:
            stop[row["invocation_id"]] = row.get("stop_reason")
    return {"rounding": rounding, "q7": q7, "replay": replay, "stop": stop}


def build_units(group: str, ev: dict, continued: set[str]):
    part_a, raw_b, eff_b, audit = load_records(group)
    opp = Counter()
    units, run_stage_units = [], defaultdict(list)
    retained_voids = set(audit.get("rerun_voids_not_used_as_replacements", [])) if group == "price_matched_16384" else set()
    replaced = {r["original_run_id"]: r["effective_run_id"] for r in audit.get("replacements", [])}

    def add(part, run_id, project, path, repeat, srec):
        alias = srec.model_alias
        stage = val(srec.stage)
        opp[(part, stage, alias)] += 1
        if val(srec.status) not in NON_PASSED:
            return
        u = {"group": group, "part": part, "run_id": run_id, "project_id": project, "path_id": path,
             "repeat_index": repeat, "stage": stage, "alias": alias, "stage_rec": srec,
             "retained_void_rerun": run_id in retained_voids}
        units.append(u)
        if part == "part_b":
            run_stage_units[run_id].append(u)

    for r in part_a:
        add("part_a", r.run_id, r.project_id, None, r.repeat_index, r.record)
    for r in eff_b:
        for s in r.stages:
            add("part_b", r.run_id, r.project_id, r.path_id, r.repeat_index, s)
    # replaced void originals: audit only
    raw_by = {r.run_id: r for r in raw_b}
    rerun_audit = []
    for orig, new in sorted(replaced.items()):
        o = raw_by[orig]
        rerun_audit.append({"original_run_id": orig, "replaced_by": new,
                            "original_nonpassed_stages": [[val(s.stage), s.model_alias, val(s.status)]
                                                          for s in o.stages if val(s.status) != "passed"]})
    # reconciliation: units == non-passed effective stage records
    raw_nonpassed = sum(val(s.status) != "passed" for r in raw_b for s in r.stages) + \
        sum(val(r.record.status) != "passed" for r in part_a)
    replaced_nonpassed = sum(len(a["original_nonpassed_stages"]) for a in rerun_audit)
    # raw includes rerun records too; retained rerun voids are in raw but not effective
    retained_nonpassed = sum(val(s.status) != "passed" for r in raw_b if r.run_id in retained_voids for s in r.stages)
    recon = {"units": len(units), "raw_nonpassed": raw_nonpassed,
             "replaced_original_nonpassed": replaced_nonpassed,
             "retained_rerun_void_nonpassed_not_effective": retained_nonpassed}
    if len(units) != raw_nonpassed - replaced_nonpassed - retained_nonpassed:
        raise ValueError(f"reconciliation failed for {group}: {recon}")
    # per-run check vs Feasibility.stage_status
    for r in eff_b:
        n_feas = sum(v.value != "passed" if hasattr(v, "value") else v != "passed"
                     for v in r.feasibility.stage_status.values())
        if n_feas != len(run_stage_units.get(r.run_id, [])):
            raise ValueError(f"unit count differs from Feasibility.stage_status: {r.run_id}")
    return units, opp, rerun_audit, recon


def run(rerun_only: bool = False) -> dict[str, Any]:
    cont = read_jsonl(CONTINUATIONS)
    continued = {c["continued_from"] for c in cont}
    result: dict[str, Any] = {"label": "post-hoc / exploratory failure taxonomy; frozen labels unchanged",
                              "categories": CATEGORIES, "model_groups": {}}
    all_units = []
    for group in DGROUPS:
        ev = load_evidence(group)
        units, opp, audit, recon = build_units(group, ev, continued)
        overlaps = Counter()
        missing = 0
        for u in units:
            cat, sub, rules = classify(u, ev)
            u["category"], u["sub"], u["rules"] = cat, sub, rules
            if len(rules) > 1:
                overlaps["+".join(map(str, rules))] += 1
            missing += sum(i not in ev["stop"] for i in u["stage_rec"].invocation_ids)
            u["status"] = val(u["stage_rec"].status)
            key4 = (group, u["part"], u["run_id"], u["stage"])
            if key4 in ev["replay"]:
                u["later"] = f"{u['stage']}_replay_pass"
            elif u["part"] == "part_b" and u["run_id"] in continued and u["stage"] == "reporting":
                u["later"] = "continuation_reporting_exists"
            else:
                u["later"] = "none"
        # upstream root for blocked units
        by_run = defaultdict(list)
        for u in units:
            if u["part"] == "part_b":
                by_run[u["run_id"]].append(u)
        for us in by_run.values():
            us.sort(key=lambda x: STAGE_ORDER[x["stage"]])
            for i, u in enumerate(us):
                if u["category"] == "blocked_or_not_run_upstream":
                    u["root"] = next((p["category"] for p in us[:i] if p["category"] != "blocked_or_not_run_upstream"),
                                     "none_found")
        stderr_only = sum(1 for u in units if u["status"] == "failed" and u["stage_rec"].execution is not None
                          and INT64_ERROR in (u["stage_rec"].execution.stderr or "")
                          and INT64_ERROR not in (u["stage_rec"].failure_detail or ""))
        result["model_groups"][group] = {"units": units, "opp": opp, "audit": audit, "recon": recon,
                                         "overlaps": overlaps, "missing": missing, "stderr_only": stderr_only,
                                         "r5r6_overlap": sum(1 for u in units if 5 in u["rules"] and 6 in u["rules"])}
        all_units += units
    return result


def sample_key(u):
    return hashlib.sha256(f"{SEED}|{u['group']}|{u['part']}|{u['run_id']}|{u['stage']}".encode()).hexdigest()


def draw_sample(units) -> dict:
    strata = defaultdict(list)
    for u in units:
        if u["category"] == "unexplained_residual":
            strata[(u["group"], u["alias"])].append(u)
    chosen, sizes = [], {}
    for k in sorted(strata):
        us = sorted(strata[k], key=sample_key)
        sizes[f"{k[0]}|{k[1]}"] = len(us)
        for u in us[:PER_STRATUM]:
            chosen.append({"group": u["group"], "part": u["part"], "run_id": u["run_id"], "stage": u["stage"],
                           "alias": u["alias"], "stratum": f"{k[0]}|{k[1]}", "sampling_key_sha256": sample_key(u)})
    body = {"label": "post-hoc / exploratory residual review list; identifiers only, no answers",
            "seed": SEED, "per_stratum_max": PER_STRATUM, "stratum_sizes": sizes, "units": chosen}
    body["integrity_sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    return body


def ci(k, n):
    w = wilson(k, n)
    return {"k": k, "n": n, "share": k / n if n else None, "wilson95": list(w) if w else None}


def summarise(res: dict) -> dict:
    out = {"label": res["label"], "categories": CATEGORIES,
           "artifact_like": sorted(ARTIFACT_LIKE), "model_behaviour_like": sorted(MODEL_LIKE), "model_groups": {}}
    tot_all, tot_res_all, tot_failed, tot_res_failed = 0, 0, 0, 0
    for g, d in res["model_groups"].items():
        us = d["units"]
        cell = defaultdict(Counter)
        for u in us:
            cell[(u["part"], u["stage"], u["alias"])][u["category"]] += 1
        counts = {}
        for (part, stage, alias), c in sorted(cell.items()):
            counts.setdefault(part, {}).setdefault(stage, {})[alias] = {
                "stage_opportunities": d["opp"][(part, stage, alias)], "n_nonpassed": sum(c.values()),
                "by_category": {k: c[k] for k in CATEGORIES}}
        by_alias, by_alias_res = {}, {}
        for a in "ABC":
            au = [u for u in us if u["alias"] == a]
            by_alias[a] = {"n_units": len(au), "by_category": {k: sum(u["category"] == k for u in au) for k in CATEGORIES},
                           "residual_all_units": ci(sum(u["category"] == "unexplained_residual" for u in au), len(au)),
                           "residual_failed_only": ci(sum(u["category"] == "unexplained_residual" and u["status"] == "failed" for u in au),
                                                      sum(u["status"] == "failed" for u in au))}
        n, nres = len(us), sum(u["category"] == "unexplained_residual" for u in us)
        nf = sum(u["status"] == "failed" for u in us)
        nrf = sum(u["category"] == "unexplained_residual" and u["status"] == "failed" for u in us)
        tot_all += n; tot_res_all += nres; tot_failed += nf; tot_res_failed += nrf
        subs = defaultdict(Counter)
        for u in us:
            if u["category"] in ("other_execution_error", "genuine_validator_mismatch",
                                 "infrastructure_void", "parse_or_schema_failure", "blocked_or_not_run_upstream"):
                subs[u["category"]][u["sub"]] += 1
        roots = Counter(u["root"] for u in us if u["category"] == "blocked_or_not_run_upstream")
        out["model_groups"][g] = {
            "counts": counts, "by_alias": by_alias,
            "by_category": {k: sum(u["category"] == k for u in us) for k in CATEGORIES},
            "residual_all_units": ci(nres, n), "residual_failed_only": ci(nrf, nf),
            "artifact_like": ci(sum(u["category"] in ARTIFACT_LIKE for u in us), n),
            "model_behaviour_like": ci(sum(u["category"] in MODEL_LIKE for u in us), n),
            "artifact_like_excluding_blocked": ci(sum(u["category"] in ARTIFACT_LIKE - {"blocked_or_not_run_upstream"}
                                                      for u in us), n),
            "blocked_share": ci(sum(u["category"] == "blocked_or_not_run_upstream" for u in us), n),
            "subclasses": {k: dict(sorted(v.items())) for k, v in sorted(subs.items())},
            "blocked_upstream_root": dict(sorted(roots.items())),
            "later_recovered_by": dict(Counter(u["later"] for u in us)),
            "overlap_matrix_multi_match_rules": dict(sorted(d["overlaps"].items())),
            "overlap_rule5_rule6": d["r5r6_overlap"], "n_invocation_join_missing": d["missing"],
            "n_int64_stderr_only": d["stderr_only"], "docker_rerun_audit": d["audit"],
            "reconciliation": d["recon"]}
    out["overall_both_groups_descriptive"] = {"residual_all_units": ci(tot_res_all, tot_all),
                                              "residual_failed_only": ci(tot_res_failed, tot_failed)}
    return out


def render(s: dict) -> str:
    names = {"original_4096": {"A": "Sonnet 4.6", "B": "Nova Pro", "C": "gpt-oss-120b"},
             "price_matched_16384": {"A": "Sonnet 4.6", "B": "Kimi K3", "C": "GLM 5"}}
    L = ["# Failure-cause taxonomy", "",
         "**POST-HOC / EXPLORATORY.** Mutually exclusive categories by the precedence in "
         "`docs/FAILURE_TAXONOMY_RULES.md`. Source: `results/processed/failure_taxonomy_posthoc.json`. "
         "Categories describe saved evidence, not proven root causes. Blocked/not-run units are their own "
         "category and inflate the all-units denominator; the failed-only residual share is the co-headline.", "",
         "**Caveats (read before the tables).**", "",
         "1. `genuine_validator_mismatch` is a broad catch-all keyed on `failure_type == validation_failed` with a "
         "failed mandatory check. It does **not** assign fault to the model or to the validator; the "
         "'model-behaviour-like' grouping below is by failure type only, not a finding that the model was wrong.",
         "2. The 0 unexplained residual follows from the precedence rules and the `failure_type` mapping: every "
         "failed record carries a `failure_type` that maps to rules 7-9. It is **not** evidence that every "
         "failure is understood, and the review sample is empty for that reason.",
         "3. The artifact-like share includes `blocked_or_not_run_upstream` records, whose upstream roots differ by "
         "group (see each group's root list: mostly non-artifact roots in the original group, mostly int64 in the "
         "price-matched group). The share without that category is shown beside it.", ""]

    def c(d):
        return "n/a" if not d["n"] else f"{d['k']}/{d['n']} = {d['share']:.3f} [{d['wilson95'][0]:.3f}, {d['wilson95'][1]:.3f}]"

    L += ["## Unexplained residual share", "", "| scope | all units | failed units only |", "|---|---|---|"]
    for g, b in s["model_groups"].items():
        L.append(f"| {g} | {c(b['residual_all_units'])} | {c(b['residual_failed_only'])} |")
        for a, x in b["by_alias"].items():
            L.append(f"| {g} / {names[g][a]} (`{a}`) | {c(x['residual_all_units'])} | {c(x['residual_failed_only'])} |")
    o = s["overall_both_groups_descriptive"]
    L += [f"| both groups (descriptive sum) | {c(o['residual_all_units'])} | {c(o['residual_failed_only'])} |", ""]
    for g, b in s["model_groups"].items():
        L += [f"## {g}", "", "Category totals: " + "; ".join(f"{k}={v}" for k, v in b["by_category"].items()), "",
              f"Artifact-like share (includes blocked/not-run) {c(b['artifact_like'])}; artifact-like share **excluding** blocked/not-run {c(b['artifact_like_excluding_blocked'])}; blocked/not-run share {c(b['blocked_share'])}; model-behaviour-like by failure type only, not fault {c(b['model_behaviour_like'])}.", "",
              "| part | stage | model | opportunities | non-passed | " + " | ".join(CATEGORIES) + " |",
              "|---|---|---|---:|---:|" + "---:|" * len(CATEGORIES)]
        for part, st in b["counts"].items():
            for stage, al in st.items():
                for a, x in al.items():
                    L.append(f"| {part} | {stage} | {names[g][a]} (`{a}`) | {x['stage_opportunities']} | {x['n_nonpassed']} | "
                             + " | ".join(str(x["by_category"][k]) for k in CATEGORIES) + " |")
        L += ["", "Sub-classes:", ""]
        for k, v in b["subclasses"].items():
            L.append(f"- {k}: " + "; ".join(f"{a}={n}" for a, n in v.items()))
        L += ["", f"- blocked/not-run upstream root: {b['blocked_upstream_root']}",
              f"- later_recovered_by annotation: {b['later_recovered_by']}",
              f"- multi-rule matches before precedence: {b['overlap_matrix_multi_match_rules']}; rule5/rule6 overlap {b['overlap_rule5_rule6']}",
              f"- invocation-join misses: {b['n_invocation_join_missing']}; int64 stderr-only: {b['n_int64_stderr_only']}",
              f"- Docker rerun audit: {len(b['docker_rerun_audit'])} replaced void originals (excluded from units): "
              f"{b['docker_rerun_audit']}",
              f"- reconciliation: {b['reconciliation']}", ""]
    return "\n".join(L) + "\n"


def main() -> int:
    res = run()
    s = summarise(res)
    units = [u for d in res["model_groups"].values() for u in d["units"]]
    sample = draw_sample(units)
    again = draw_sample(units)
    assert sample == again, "sample not deterministic"
    s["source_hashes"] = {str(p.relative_to(REPO)): hash_file(p) for p in
                          [RULES, DIAGNOSTICS, CONTINUATIONS] + [DGROUPS[g][k] for g in DGROUPS
                                                                  for k in ("part_a", "part_b", "invocations")]}
    OUT.write_text(json.dumps(s, indent=1, sort_keys=True) + "\n")
    REPORT.write_text(render(s))
    SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    SAMPLE.write_text(json.dumps(sample, indent=1, sort_keys=True) + "\n")
    print(json.dumps({g: b["by_category"] for g, b in s["model_groups"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
