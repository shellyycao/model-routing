"""Post-hoc / exploratory / retrospective re-scoring of frozen router counterfactual predictions
against corrected executed outcomes. Rules: docs/ROUTER_RELABEL_RULES.md (committed first).

Re-scores only: predictions are read from the verified append-only logs and never changed. Writes
only results/processed/router_relabel_posthoc.json and results/reports/router_relabel_posthoc.md.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from experiments.analyze_corrected_q2 import (
    CONTINUATIONS, Q1 as _Q1, _base_costs, _cleaning_recoveries, _rescore_continuation_reporting,
    _status_outcome, _v31_records, read_jsonl,
)
from experiments.analyze_corrected_view import GROUPS, evidence, load_records, opportunities
from src.bedrock.provenance import hash_file
from src.contracts import STAGES, StageStatus, parse_path_id
from src.explainability.validation import _sign, validate_prediction
from src.routing.counterfactual import PredictionLog
from src.routing.data import RecordStore, build_training_view, norm_project

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "docs/ROUTER_RELABEL_RULES.md"
Q2_JSON = REPO / "results/processed/corrected_q2.json"
OUT = REPO / "results/processed/router_relabel_posthoc.json"
REPORT = REPO / "results/reports/router_relabel_posthoc.md"
ROUTING = {"original_4096": REPO / "results/routing/v3_primary",
           "price_matched_16384": REPO / "results/routing/price_matched_workflow_v3_primary"}
EXPECTED = {"original_4096": (22, 50), "price_matched_16384": (31, 64)}
VIEWS = ("frozen_v3", "corrected_v3", "frozen_v31", "corrected_v31")
VALIDATORS = {"v3_primary": ("frozen_v3", "corrected_v3"), "v31_secondary": ("frozen_v31", "corrected_v31")}
METHODS = ("router", "a_always_less", "b_always_more", "c_stage_rate_frozen", "c_stage_rate_corrected",
           "d_always_tie")
NAMES = {"original_4096": {"A": "Sonnet 4.6", "B": "Nova Pro", "C": "gpt-oss-120b"},
         "price_matched_16384": {"A": "Sonnet 4.6", "B": "Kimi K3", "C": "GLM 5"}}
Z = 1.959964
EPS = 1e-12
VALIDATED_AT = "2026-11-19T00:00:00+00:00"  # fixed; used only for the in-memory validation records


# ---------------------------------------------------------------------------------- statistics
def wilson(k: int, n: int, z: float = Z) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def binom_two_sided(k: int, n: int, p0: float = 0.5) -> float | None:
    """Exact two-sided binomial p-value (sum of outcomes no more likely than the observed)."""
    if n == 0:
        return None
    pm = [math.comb(n, i) * p0 ** i * (1 - p0) ** (n - i) for i in range(n + 1)]
    obs = pm[k]
    return min(1.0, sum(x for x in pm if x <= obs * (1 + 1e-7)))


def mcnemar_exact(b: int, c: int) -> float | None:
    """Two-sided exact McNemar on discordant counts b, c."""
    return binom_two_sided(min(b, c), b + c) if b + c else None


def acc(flags: list[bool]) -> dict[str, Any]:
    k, n = sum(flags), len(flags)
    w = wilson(k, n)
    return {"k": k, "n": n, "accuracy": k / n if n else None,
            "wilson95": list(w) if w else None, "p_binomial_vs_0.5": binom_two_sided(k, n)}


# ---------------------------------------------------------------------------------- label views
def build_run_labels(group: str, effective) -> dict[str, dict[str, str]]:
    """run_id -> {view: outcome} for every effective run, same logic as analyze_corrected_q2."""
    continuation_rows = read_jsonl(CONTINUATIONS)
    by_original = {r["continued_from"]: r for r in continuation_rows}
    if len(continuation_rows) != 40 or len(by_original) != 40:
        raise ValueError("continuation store is not 40 distinct cells")
    voids = {r["continued_from"] for r in continuation_rows
             if r["outcome"] != "complete_for_corrected_view" or r["remaining_stages"][0]["status"] == "infra_error"}
    v31c = {}
    for r in continuation_rows:
        v31c[r["continued_from"]] = None if r["continued_from"] in voids else _rescore_continuation_reporting(r)
    cleaning = _cleaning_recoveries()
    v31_existing = _v31_records(group)
    labels: dict[str, dict[str, str]] = {}
    for run in effective:
        orig = [s.status.value for s in run.stages]
        frozen_v3, _ = _status_outcome(orig)
        if frozen_v3 != run.feasibility.outcome:
            raise ValueError(f"stored frozen feasibility mismatch: {run.run_id}")
        rep = v31_existing.get(run.run_id)
        f31 = list(orig)
        if all(v == "passed" for v in orig[:2]) and rep and rep["v31_ground_truth"]["hard_pass"]:
            f31[2] = "passed"
        corr, c31 = list(orig), list(f31)
        cont = by_original.get(run.run_id)
        if cont is not None:
            rstage = cont["remaining_stages"][0]
            if run.run_id in voids:
                corr = ["passed", "passed", "infra_error"]
                c31 = list(corr)
            else:
                corr = ["passed", "passed", rstage["status"]]
                rs = v31c[run.run_id]
                c31 = ["passed", "passed", "passed" if rs and rs["v31_pass"] else rstage["status"]]
        elif (group, run.run_id) in cleaning:
            corr[0] = "passed"
        if cont is None:
            c31 = list(corr)
            if all(v == "passed" for v in corr[:2]) and rep and rep["v31_ground_truth"]["hard_pass"]:
                c31[2] = "passed"
        labels[run.run_id] = {"frozen_v3": frozen_v3, "corrected_v3": _status_outcome(corr)[0],
                              "frozen_v31": _status_outcome(f31)[0], "corrected_v31": _status_outcome(c31)[0],
                              "_repeat": run.repeat_index, "_project": run.project_id, "_path": run.path_id}
    return labels


def with_outcomes(runs, labels, view):
    out = []
    for r in runs:
        o = labels[r.run_id][view]
        out.append(r if o == r.feasibility.outcome else
                   r.model_copy(update={"feasibility": r.feasibility.model_copy(update={"outcome": o})}))
    return out


# ---------------------------------------------------------------------------------- baselines
def stage_rates(part_a, held_out: str, flag: str) -> dict[tuple[str, str], float]:
    """Pooled stage pass rate per (stage, alias) from TRAINING projects only.

    Uses the router's own leakage guard: build_training_view physically filters the held-out project
    (normalised with norm_project) and raises for an unknown project. `part_a` items need
    project_id, stage, model_alias and the boolean attribute named by `flag`.
    """
    view = build_training_view(RecordStore(stage_records=tuple(part_a), workflow_runs=()), norm_project(held_out))
    tot: Counter = Counter()
    ok: Counter = Counter()
    for r in view.stage_records:
        key = (getattr(r.stage, "value", r.stage), r.model_alias)
        tot[key] += 1
        ok[key] += bool(getattr(r, flag))
    return {k: ok[k] / tot[k] for k in tot}


def _sgn(x: float) -> int:
    return 0 if abs(x) <= EPS else (1 if x > 0 else -1)


def rate_sign(rates, sel_path: str, alt_path: str) -> int:
    sel, alt = parse_path_id(sel_path), parse_path_id(alt_path)
    diff = [i for i in range(len(STAGES)) if sel[i] != alt[i]]
    if len(diff) == 1:
        i = diff[0]
        s = STAGES[i].value
        return _sgn(rates[(s, alt[i])] - rates[(s, sel[i])])
    ps = math.prod(rates[(STAGES[i].value, sel[i])] for i in range(len(STAGES)))
    pa = math.prod(rates[(STAGES[i].value, alt[i])] for i in range(len(STAGES)))
    return _sgn(pa - ps)


# ---------------------------------------------------------------------------------- main analysis
def load_part_a_rows(group: str):
    replay, rounding, q7, v31 = evidence()
    rows = []
    for row in opportunities(group):
        if row["part"] != "part_a":
            continue
        rec = row["record"]
        frozen = rec.status == StageStatus.PASSED
        rk = (group, "part_a", row["run_id"], row["stage"])
        rep = (group, "part_a", row["run_id"])
        combined = (frozen or rk in replay or (row["stage"] == "reporting" and rep in rounding)
                    or (row["stage"] == "reporting" and v31.get(rep, False)))
        rows.append(SimpleNamespace(project_id=row["project_id"], run_id=row["run_id"], stage=row["stage"],
                                    model_alias=row["alias"], frozen=bool(frozen), combined=bool(combined)))
    return rows


def gate_and_score(group: str, labels_cache: dict | None = None) -> dict[str, Any]:
    gdir = ROUTING[group]
    log = PredictionLog(gdir / "counterfactual_predictions.jsonl")
    rep = log.verify()
    if not rep.ok:
        raise ValueError(f"prediction log chain broken: {rep.errors}")
    preds = log.predictions()
    saved = {}
    for line in (gdir / "counterfactual_validations.jsonl").read_text().splitlines():
        if line.strip():
            rec = json.loads(line)["record"]
            saved[rec["prediction_id"]] = rec
    _, raw, effective, _ = load_records(group)
    labels = build_run_labels(group, effective)

    # ---- reproduction gate (frozen_v3 labels) ----
    mism = []
    flags = []
    for p in preds:
        v = validate_prediction(p, effective, VALIDATED_AT)
        s = saved[p.prediction_id]
        for key in ("actual_selected", "actual_alternative"):
            if getattr(v, key).get("feasible") != s[key].get("feasible"):
                mism.append((p.prediction_id, key))
        if v.direction_correct != s["direction_correct"]:
            mism.append((p.prediction_id, "direction_correct"))
        if v.direction_correct.get("feasible") is not None:
            flags.append(bool(v.direction_correct["feasible"]))
    got = (sum(flags), len(flags))
    gate = {"n_predictions": len(preds), "records_reproduced_exactly": len(preds) - len({m[0] for m in mism}),
            "mismatches": mism[:20], "pooled_k_n": list(got), "expected_k_n": list(EXPECTED[group]),
            "passed": (not mism) and got == EXPECTED[group] and len(preds) == len(saved)}
    return {"preds": preds, "effective": effective, "labels": labels, "gate": gate}


def score_group(group: str, ctx: dict[str, Any]) -> dict[str, Any]:
    preds, effective, labels = ctx["preds"], ctx["effective"], ctx["labels"]
    part_a = load_part_a_rows(group)
    rates_cache: dict[tuple[str, str], dict] = {}

    def rates(project: str, kind: str):
        key = (project, kind)
        if key not in rates_cache:
            rates_cache[key] = stage_rates(part_a, project, "frozen" if kind == "frozen" else "combined")
        return rates_cache[key]

    per_view: dict[str, list[dict]] = {}
    for view in VIEWS:
        runs = with_outcomes(effective, labels, view)
        rows = []
        for p in preds:
            v = validate_prediction(p, runs, VALIDATED_AT)
            pd_ = p.predicted_delta.get("feasible")
            ad = v.actual_delta.get("feasible")
            row = {"id": p.prediction_id, "strategy": p.strategy.value, "project": p.held_out_project,
                   "agree_sel": v.direction_correct.get("feasibility_agreement:selected"),
                   "agree_alt": v.direction_correct.get("feasibility_agreement:alternative"),
                   "pred_sign": None if pd_ is None else _sign(pd_),
                   "actual_sign": None if ad is None else _sign(ad)}
            if row["pred_sign"] is not None and row["actual_sign"] is not None:
                ps = row["pred_sign"]
                row["method"] = {
                    "router": ps, "a_always_less": -1, "b_always_more": 1, "d_always_tie": 0,
                    "c_stage_rate_frozen": rate_sign(rates(p.held_out_project, "frozen"),
                                                      p.selected_path_id, p.alternative_path_id),
                    "c_stage_rate_corrected": rate_sign(rates(p.held_out_project, "combined"),
                                                         p.selected_path_id, p.alternative_path_id)}
            rows.append(row)
        per_view[view] = rows

    out: dict[str, Any] = {}
    for vname, (fv, cv) in VALIDATORS.items():
        block = {}
        for label_kind, view in (("frozen", fv), ("corrected", cv)):
            rows = per_view[view]
            scored = [r for r in rows if "method" in r]
            slices = {"pooled": scored}
            for s in sorted({r["strategy"] for r in scored}):
                slices[s] = [r for r in scored if r["strategy"] == s]
            for proj in sorted({r["project"] for r in scored}):
                slices[f"project:{proj}"] = [r for r in scored if r["project"] == proj]
            sl_out = {}
            for sname, srows in slices.items():
                entry = {"n_excluded_no_outcome": sum(1 for r in rows if "method" not in r
                                                      and (sname == "pooled" or r["strategy"] == sname
                                                           or f"project:{r['project']}" == sname)),
                         "methods": {}}
                for m in METHODS:
                    entry["methods"][m] = acc([r["method"][m] == r["actual_sign"] for r in srows])
                entry["mcnemar_router_vs"] = {}
                for m in METHODS[1:]:
                    b = sum(1 for r in srows if r["method"]["router"] == r["actual_sign"] and r["method"][m] != r["actual_sign"])
                    c = sum(1 for r in srows if r["method"]["router"] != r["actual_sign"] and r["method"][m] == r["actual_sign"])
                    entry["mcnemar_router_vs"][m] = {"router_only_correct": b, "baseline_only_correct": c,
                                                     "p_exact": mcnemar_exact(b, c)}
                entry["agreement_selected"] = acc([bool(r["agree_sel"]) for r in srows if r["agree_sel"] is not None])
                entry["agreement_alternative"] = acc([bool(r["agree_alt"]) for r in srows if r["agree_alt"] is not None])
                sl_out[sname] = entry
            table = {f"{ps}|{as_}": sum(1 for r in scored if r["pred_sign"] == ps and r["actual_sign"] == as_)
                     for ps in (-1, 0, 1) for as_ in (-1, 0, 1)}
            by_strat = {st: {f"{ps}|{as_}": sum(1 for r in scored if r["strategy"] == st and r["pred_sign"] == ps
                                               and r["actual_sign"] == as_)
                             for ps in (-1, 0, 1) for as_ in (-1, 0, 1)}
                        for st in sorted({r["strategy"] for r in scored})}
            block[label_kind] = {"view": view, "slices": sl_out, "pred_sign_by_actual_sign": table,
                                 "pred_sign_by_actual_sign_by_strategy": by_strat}
        fr = {r["id"]: r for r in per_view[fv]}
        changed = []
        for r in per_view[cv]:
            f = fr[r["id"]]
            if (f["actual_sign"], f["pred_sign"]) != (r["actual_sign"], r["pred_sign"]) or \
                    (f["actual_sign"] == f["pred_sign"]) != (r["actual_sign"] == r["pred_sign"]):
                changed.append({"id": r["id"], "strategy": r["strategy"], "predicted_sign": r["pred_sign"],
                                "frozen_actual_sign": f["actual_sign"], "corrected_actual_sign": r["actual_sign"],
                                "frozen_correct": None if f["actual_sign"] is None else f["actual_sign"] == f["pred_sign"],
                                "corrected_correct": None if r["actual_sign"] is None else r["actual_sign"] == r["pred_sign"]})
        block["changed_predictions"] = changed
        out[vname] = block
    return out


def labels_audit(group: str, ctx) -> dict[str, Any]:
    """Assert repeat-0 rows equal the saved corrected_q2.json main-grid rows."""
    saved = json.loads(Q2_JSON.read_text())["model_groups"][group]["project_path_outcomes_main_grid"]
    got = {(v["_project"], v["_path"]): v for v in ctx["labels"].values() if v["_repeat"] == 0}
    if len(saved) != len(got):
        raise ValueError("main-grid row count differs from corrected_q2.json")
    for row in saved:
        g = got[(row["project_id"], row["path_id"])]
        for view in VIEWS:
            if g[view] != row[view]:
                raise ValueError(f"label differs from corrected_q2.json: {row['project_id']} {row['path_id']} {view}")
    return {"effective_runs": len(ctx["labels"]), "main_grid_rows_equal_saved": len(saved)}


def analyze() -> dict[str, Any]:
    result: dict[str, Any] = {"label": "post-hoc / exploratory / retrospective re-scoring; not prospective evidence",
                              "model_groups": {}}
    ctxs = {g: gate_and_score(g) for g in GROUPS}
    result["reproduction_gate"] = {g: c["gate"] for g, c in ctxs.items()}
    if not all(c["gate"]["passed"] for c in ctxs.values()):
        result["status"] = "GATE_FAILED"
        return result
    result["status"] = "gate_passed"
    for g, ctx in ctxs.items():
        audit = labels_audit(g, ctx)
        result["model_groups"][g] = {"labels_audit": audit, "validators": score_group(g, ctx)}
    paths = [RULES, Q2_JSON, CONTINUATIONS, _Q1] + [ROUTING[g] / f for g in GROUPS for f in
              ("counterfactual_predictions.jsonl", "counterfactual_validations.jsonl")] + \
            [cfg[k] for cfg in GROUPS.values() for k in ("part_a", "part_b", "v31_a", "v31_b")]
    result["source_hashes"] = {str(p.relative_to(REPO)): hash_file(p) for p in paths}
    return result


# ---------------------------------------------------------------------------------- report
def _cell(a: dict) -> str:
    if not a["n"]:
        return "0/0"
    lo, hi = a["wilson95"]
    return f"{a['k']}/{a['n']} = {a['accuracy']:.3f} [{lo:.3f}, {hi:.3f}] p={a['p_binomial_vs_0.5']:.3f}"


def render(result: dict[str, Any]) -> str:
    L = ["# Router relabel re-scoring", "",
         "**POST-HOC / EXPLORATORY / RETROSPECTIVE.** Frozen predictions are re-scored against corrected executed "
         "outcomes. This is not prospective evidence; no router was retrained. Wilson 95% intervals and exact "
         "binomial p-values (vs 0.5) treat predictions as independent; they are clustered by project and strategy, "
         "so these intervals are optimistic. A 3-class sign match has no natural 0.5 chance level; compare with the "
         "baselines. Source: `results/processed/router_relabel_posthoc.json`.", ""]
    if result["status"] != "gate_passed":
        L += ["## Reproduction gate FAILED", "", "```", json.dumps(result["reproduction_gate"], indent=1), "```"]
        return "\n".join(L) + "\n"
    L += ["## Plain statement of what the baselines show", "",
          "- The trivial **always-tie** baseline (predict no feasibility change) is at least as accurate as the "
          "frozen router in 7 of the 8 group/validator/label cells, and beats it with corrected v3 labels: original 26/50 vs 21/50 and "
          "price-matched 36/64 vs 24/64. The detailed tables below give every baseline for every slice, including "
          "where **always-less** or the training-only **stage-rate** baseline equals or beats the router "
          "(for example price-matched frozen v3: always-less 32/64 and stage-rate 36/64 vs router 31/64).",
          "- The router exceeds **always-more** by a wide margin; its margin over the other baselines is small "
          "or negative in the cells shown.",
          "- Corrected labels depend on the 40 paid continuation calls and on the 11 cleaning recoveries, whose "
          "downstream stages saw a `failed` upstream label; they are a sensitivity, not a reconstruction.",
          "- Nothing here shows the router repaired, validated or deployable. Corrected labels lowered its "
          "accuracy in every group and validator shown; this is a retrospective re-scoring only.", ""]
    L += ["## Reproduction gate", ""]
    for g, gt in result["reproduction_gate"].items():
        L.append(f"- {g}: {gt['records_reproduced_exactly']}/{gt['n_predictions']} validations reproduced exactly; "
                 f"pooled {gt['pooled_k_n'][0]}/{gt['pooled_k_n'][1]} (expected {EXPECTED[g][0]}/{EXPECTED[g][1]}).")
    L.append("")
    for g, body in result["model_groups"].items():
        names = ", ".join(f"`{a}` = {n}" for a, n in NAMES[g].items())
        L += [f"## Group {g} (alias meaning: {names})", ""]
        for vname, vb in body["validators"].items():
            L += [f"### {vname}", "", "| slice | method | frozen | corrected |", "|---|---|---|---|"]
            for sname in vb["frozen"]["slices"]:
                for m in METHODS:
                    L.append(f"| {sname} | {m} | {_cell(vb['frozen']['slices'][sname]['methods'][m])} | "
                             f"{_cell(vb['corrected']['slices'][sname]['methods'][m])} |")
            L += ["", "McNemar exact p, router vs baseline (pooled; discordant router-only/baseline-only), corrected labels:", ""]
            for m, d in vb["corrected"]["slices"]["pooled"]["mcnemar_router_vs"].items():
                L.append(f"- {m}: {d['router_only_correct']}/{d['baseline_only_correct']}, p={d['p_exact']}")
            L += ["", "Predicted sign (rows -1,0,1) by actual sign (cols -1,0,1), frozen / corrected:", ""]
            for kind in ("frozen", "corrected"):
                t = vb[kind]["pred_sign_by_actual_sign"]
                L.append(f"- {kind}: " + "; ".join(f"{k}:{v}" for k, v in t.items()))
            L += ["", f"Predictions whose correctness or actual sign changed: {len(vb['changed_predictions'])} "
                  "(listed in the JSON `changed_predictions`).", ""]
    return "\n".join(L) + "\n"


def write_outputs(res: dict[str, Any], out: Path = OUT, report: Path = REPORT) -> bool:
    """Write processed JSON and report only when the reproduction gate passed."""
    if res.get("status") != "gate_passed":
        return False
    out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    report.write_text(render(res))
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-only", action="store_true")
    args = ap.parse_args()
    res = analyze()
    print(json.dumps(res["reproduction_gate"], indent=1))
    if args.gate_only:
        return 0 if res["status"] == "gate_passed" else 2
    return 0 if write_outputs(res) else 2


if __name__ == "__main__":
    raise SystemExit(main())
