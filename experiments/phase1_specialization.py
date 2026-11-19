"""Phase 1 (model specialization) analysis of Experiment A records. OFFLINE: reads saved files only.

Inputs : results/raw/stage_benchmark/<experiment>.jsonl (StageBenchmarkRecord)
         results/raw/invocations.jsonl (InvocationRecord; reasoning chars, truncation, retries)
Outputs: results/reports/phase1_tables.json  (all computed numbers + source hashes)
         stdout: markdown tables used in results/reports/phase1_model_specialization.md

Usage: .venv/bin/python -m experiments.phase1_specialization [--experiment expA_stage_v3]
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODELS = {"A": "Claude Sonnet 4.6", "B": "Amazon Nova Pro", "C": "OpenAI gpt-oss-120b"}
STAGES = ("cleaning", "analysis", "reporting")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0, c - h), 3), round(min(1, c + h), 3))


def summ(xs: list[float]) -> dict | None:
    xs = [x for x in xs if x is not None]
    if not xs:
        return None
    return {"n": len(xs), "median": round(st.median(xs), 3), "mean": round(st.mean(xs), 3),
            "min": round(min(xs), 3), "max": round(max(xs), 3)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", default="expA_stage_v3")
    args = ap.parse_args(argv)
    rec_path = REPO / "results/raw/stage_benchmark" / f"{args.experiment}.jsonl"
    inv_path = REPO / "results/raw/invocations.jsonl"
    recs = [json.loads(l) for l in rec_path.read_text().splitlines() if l.strip()]
    invs = {}
    for l in inv_path.read_text().splitlines():
        if l.strip():
            d = json.loads(l)
            if d.get("context", {}).get("experiment_id") == args.experiment:
                invs[d["invocation_id"]] = d

    cells: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for r in recs:
        cells[(r["stage"], r["model_alias"])].append(r)

    out = {"experiment": args.experiment, "n_records": len(recs),
           "projects": sorted({r["project_id"] for r in recs}),
           "sources": {str(rec_path.relative_to(REPO)): sha(rec_path), str(inv_path.relative_to(REPO)): sha(inv_path)},
           "cells": {}}
    for (stage, m), rs in sorted(cells.items()):
        k = sum(1 for r in rs if r["record"]["status"] == "passed")
        parse_ok = sum(1 for r in rs if r["record"].get("parse_ok"))
        structural = sum(1 for r in rs if r["record"].get("structural_ok"))
        ex = [r["record"].get("execution") for r in rs]
        ex_ok = sum(1 for e in ex if e and e.get("status") == "success")
        ex_n = sum(1 for e in ex if e)
        quality = collections.defaultdict(list)
        failed_checks = collections.Counter()
        for r in rs:
            v = r["record"].get("validation") or {}
            for q, val in (v.get("quality") or {}).items():
                quality[q].append(val)
            for c in v.get("checks", []):
                if c["mandatory"] and not c["passed"]:
                    failed_checks[c["name"]] += 1
        inv = [invs.get(i) for r in rs for i in r["record"]["invocation_ids"]]
        inv = [i for i in inv if i and i.get("status") != "parse_error"]   # parse events duplicate the call
        out["cells"][f"{stage}|{m}"] = {
            "stage": stage, "model": m, "model_name": MODELS[m], "n": len(rs),
            "projects": sorted(r["project_id"] for r in rs),
            "passed": k, "pass_rate": round(k / len(rs), 3), "pass_rate_wilson95": wilson(k, len(rs)),
            "per_project": {r["project_id"]: r["record"]["status"] for r in rs},
            "parse_ok": parse_ok, "structural_ok": structural,
            "execution_success": ex_ok, "execution_attempted": ex_n,
            "execution_statuses": dict(collections.Counter(e["status"] for e in ex if e)),
            "quality": {q: summ(v) for q, v in quality.items()},
            "failure_types": dict(collections.Counter(r["record"]["failure_type"] for r in rs if r["record"]["failure_type"])),
            "failed_mandatory_checks": dict(failed_checks),
            "failure_examples": [{"project": r["project_id"], "type": r["record"]["failure_type"],
                                  "detail": (r["record"].get("failure_detail") or "")[:300],
                                  "run_dir": str(Path(r["record"]["output_artifacts"][0]).parent) if r["record"]["output_artifacts"] else None}
                                 for r in rs if r["record"]["status"] != "passed"],
            "generation_s": summ([(r["record"]["timings"].get("generation_ms") or 0) / 1000 for r in rs]),
            "execution_s": summ([(r["record"]["timings"].get("execution_ms") or 0) / 1000 for r in rs
                                 if r["record"]["timings"].get("execution_ms") is not None]),
            "server_latency_s": summ([(i.get("server_latency_ms") or 0) / 1000 for i in inv]),
            "input_tokens": summ([r["record"]["input_tokens"] for r in rs]),
            "output_tokens": summ([r["record"]["output_tokens"] for r in rs]),
            "reasoning_chars": summ([i.get("reasoning_chars") for i in inv]),
            "truncated_calls": sum(1 for i in inv if i.get("truncated")),
            "near_cap_calls": sum(1 for i in inv if (i.get("output_tokens") or 0) >= 0.95 * 4096),
            "retries": sum(i.get("retry_count") or 0 for i in inv),
            "cost_status": sorted({r["record"]["cost_status"] for r in rs}),
        }
    dest = REPO / "results/reports/phase1_tables.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    # Compact markdown for the report.
    print(f"## n_records={len(recs)} projects={out['projects']}\n")
    print("| Task | Model | Pass (k/n) | Wilson 95% | Parse OK | Exec OK | Key quality (median [min–max]) | Gen s (median) | In tok (median) | Out tok (median) | Reasoning chars (median) | Trunc |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    keyq = {"cleaning": "cleaning_correctness", "analysis": "numerical_accuracy", "reporting": "numerical_consistency"}
    for key, c in out["cells"].items():
        q = c["quality"].get(keyq[c["stage"]])
        qs = f"{q['median']} [{q['min']}–{q['max']}] (n={q['n']})" if q else "n/a"
        ex = f"{c['execution_success']}/{c['execution_attempted']}" if c["execution_attempted"] else "n/a"
        rc = c["reasoning_chars"]["median"] if c["reasoning_chars"] else "—"
        print(f"| {c['stage']} | {c['model_name']} | {c['passed']}/{c['n']} | {c['pass_rate_wilson95']} | {c['parse_ok']}/{c['n']} | {ex} | {qs} | "
              f"{c['generation_s']['median']} | {c['input_tokens']['median']} | {c['output_tokens']['median']} | {rc} | {c['truncated_calls']} |")
    print("\n## failures")
    for key, c in out["cells"].items():
        if c["failure_examples"]:
            print(f"\n### {key}  types={c['failure_types']}  failed_checks={c['failed_mandatory_checks']}  exec={c['execution_statuses']}")
            for e in c["failure_examples"]:
                print(f"- {e['project']}: {e['type']}: {e['detail'][:220]}")
    print("\n## all quality metrics")
    for key, c in out["cells"].items():
        print(key, {q: (v["median"], v["min"], v["max"]) for q, v in c["quality"].items() if v})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
