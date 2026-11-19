"""Analysis of the independent task benchmarks (A1-A3). OFFLINE: reads saved records only.

Writes results/processed/independent/tables.json (schema indep-1.0, with source hashes) and prints markdown
tables used in results/reports/independent_task_benchmark.md. Never reads or writes Part B/C data.
"""

from __future__ import annotations

import collections
import hashlib
import json
import math
import statistics as st
from pathlib import Path

from src.independent import EXPERIMENT_IDS, INDEPENDENT_SCHEMA_VERSION

REPO = Path(__file__).resolve().parents[1]
NAMES = {"A": "Claude Sonnet 4.6", "B": "Amazon Nova Pro", "C": "OpenAI gpt-oss-120b"}
PRIMARY = {"a1": ("functional_correct", "hidden_pass_rate"), "a2": ("all_fields_correct", "f1"),
           "a3": ("ndcg_at_5", "grounding_accuracy")}


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0, c - h), 3), round(min(1, c + h), 3)]


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(st.median(xs), 3) if xs else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(st.mean(xs), 3) if xs else None


def main() -> int:
    out = {"schema_version": INDEPENDENT_SCHEMA_VERSION, "sources": {}, "cells": {}}
    for task, eid in EXPERIMENT_IDS.items():
        p = REPO / "results/raw/independent" / f"{eid}.jsonl"
        if not p.exists():
            continue
        out["sources"][str(p.relative_to(REPO))] = hashlib.sha256(p.read_bytes()).hexdigest()
        recs = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
        by = collections.defaultdict(list)
        for r in recs:
            by[r["model_alias"]].append(r)
        for m, rs in sorted(by.items()):
            valid = [r for r in rs if r["status"] != "void_infra"]
            sc = [r["scores"] for r in valid]
            c = {"task": task, "model": m, "model_name": NAMES[m], "n": len(rs), "n_void": len(rs) - len(valid),
                 "hard_pass": sum(r["status"] == "passed" for r in valid),
                 "parse_ok": sum(bool(r["parse_ok"]) for r in valid), "truncated": sum(bool(r["truncated"]) for r in valid),
                 "failure_types": dict(collections.Counter(r["failure_type"] for r in valid if r["failure_type"])),
                 "gen_s_median": med([(r["generation_ms"] or 0) / 1000 for r in valid]),
                 "in_tok_median": med([r["input_tokens"] for r in valid]),
                 "out_tok_median": med([r["output_tokens"] for r in valid]),
                 "reasoning_chars_median": med([r["reasoning_chars"] for r in valid]),
                 "cost_status": sorted({r["cost_status"] for r in valid})}
            if task == "a1":
                k = sum(bool(s.get("functional_correct")) for s in sc)
                c |= {"functional_correct": k, "functional_correct_wilson95": wilson(k, len(valid)),
                      "hidden_pass_rate_mean": mean([s.get("hidden_pass_rate") for s in sc]),
                      "exec_success": sum((r.get("execution") or {}).get("status") == "success" for r in valid),
                      "names_buggy_function": sum(bool(s.get("names_buggy_function")) for s in sc),
                      "per_case": {r["case_id"]: (r["scores"].get("hidden_passed"), r["scores"].get("hidden_total"),
                                                  r["failure_type"]) for r in valid}}
            elif task == "a2":
                k = sum(bool(s.get("all_fields_correct")) for s in sc)
                c |= {"all_fields_correct": k, "all_fields_correct_wilson95": wilson(k, len(valid)),
                      "precision_mean": mean([s.get("precision") for s in sc]), "recall_mean": mean([s.get("recall") for s in sc]),
                      "f1_mean": mean([s.get("f1") for s in sc]), "f1_min": min([s.get("f1", 0) for s in sc], default=None),
                      "schema_valid": sum(bool(s.get("schema_valid")) for s in sc),
                      "null_accuracy_mean": mean([s.get("null_accuracy") for s in sc]),
                      "hallucinated_fields": sum(s.get("hallucinated_fields", 0) for s in sc),
                      "field_errors": dict(collections.Counter(f"{r['case_id'].split('_', 2)[2]}.{k_}:{v}"
                                                               for r in valid for k_, v in (r["scores"].get("per_field") or {}).items()
                                                               if v not in ("correct", "correct_null")))}
            else:
                c |= {"ndcg_at_5_mean": mean([s.get("ndcg_at_5") for s in sc]), "ndcg_at_5_min": min([s.get("ndcg_at_5", 0) for s in sc], default=None),
                      "precision_at_5_mean": mean([s.get("precision_at_5") for s in sc]),
                      "recall_grade2_mean": mean([s.get("recall_grade2_at_5") for s in sc]),
                      "grounding_accuracy_mean": mean([s.get("grounding_accuracy") for s in sc]),
                      "citation_consistent": sum(bool(s.get("citation_consistent")) for s in sc),
                      "claims_median": med([s.get("n_claims") for s in sc])}
            c["failures"] = [(r["case_id"], r["failure_type"], (r["failure_detail"] or "")[:200]) for r in rs if r["status"] != "passed"]
            out["cells"][f"{task}|{m}"] = c
    dest = REPO / "results/processed/independent/tables.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n")
    for key, c in out["cells"].items():
        print(key, json.dumps({k: v for k, v in c.items() if k not in ("per_case", "field_errors", "failures", "task", "model")}))
        if c.get("field_errors"):
            print("   field errors:", c["field_errors"])
        for f in c["failures"][:6]:
            print("   FAIL", f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
