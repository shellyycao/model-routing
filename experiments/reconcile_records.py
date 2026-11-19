"""Reconcile saved experiment records against invocation logs, ledgers, artifacts and the sandbox
verification (offline; read-only). Exits non-zero if any hard inconsistency is found.

Usage: .venv/bin/python -m experiments.reconcile_records --experiment expB_paths_v3 [--experiment expA_stage_v3]
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
from pathlib import Path

from src.contracts import StageBenchmarkRecord, WorkflowRunRecord

REPO = Path(__file__).resolve().parents[1]


def _stages(d: dict) -> list[dict]:
    return [d["record"]] if "record" in d else d["stages"]


def reconcile(experiment: str) -> dict:
    kind = "stage_benchmark" if experiment.startswith("expA") else "workflow_runs"
    path = REPO / "results/raw" / kind / f"{experiment}.jsonl"
    lines = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    model = StageBenchmarkRecord if kind == "stage_benchmark" else WorkflowRunRecord
    problems: list[str] = []
    for d in lines:
        try:
            model.model_validate(d)
        except Exception as e:  # noqa: BLE001
            problems.append(f"{d.get('run_id')}: contract validation failed: {str(e)[:120]}")
    ids = [d["run_id"] for d in lines]
    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    if dup:
        problems.append(f"duplicate run_ids: {dup[:5]}")

    invs = {}
    for l in (REPO / "results/raw/invocations.jsonl").read_text().splitlines():
        if l.strip():
            i = json.loads(l)
            if i.get("context", {}).get("experiment_id") == experiment:
                invs[i["invocation_id"]] = i
    verified = json.loads((REPO / "results/verification/sandbox_verification.json").read_text())["image_id"]
    hist = {json.loads(Path(p).read_text())["image_id"] for p in glob.glob(str(REPO / "results/verification/history/*.json"))}

    referenced, n_exec, images, cache_hits, zero_cost, missing_dirs = set(), 0, collections.Counter(), 0, 0, 0
    for d in lines:
        for s in _stages(d):
            for iid in s.get("invocation_ids", []):
                referenced.add(iid)
                inv = invs.get(iid)
                if inv is None:
                    problems.append(f"{d['run_id']}/{s['stage']}: invocation {iid} not in invocations.jsonl")
                    continue
                if inv["context"].get("run_id") != d["run_id"] or inv["model_id"] != s["model_id"]:
                    problems.append(f"{d['run_id']}/{s['stage']}: invocation {iid} run/model mismatch")
            ex = s.get("execution")
            if ex:
                n_exec += 1
                images[ex.get("sandbox_image")] += 1
            cache_hits += bool(s.get("cache_hit"))
            if s.get("cost_usd") == 0 and s.get("cost_status") not in ("not_incurred",):
                zero_cost += 1
            for p in s.get("output_artifacts", [])[:1]:
                if not (REPO / p).exists():
                    missing_dirs += 1
    unexpected_images = {k: v for k, v in images.items() if k not in ({verified} | hist)}
    if unexpected_images:
        problems.append(f"executions in unverified images: {unexpected_images}")
    if cache_hits and experiment.startswith("expB_paths") and "shared" not in experiment:
        problems.append(f"{cache_hits} cache hits in a fresh-call experiment")
    if zero_cost:
        problems.append(f"{zero_cost} stages with cost 0 but cost_status != not_incurred")
    if missing_dirs:
        problems.append(f"{missing_dirs} stages whose first output artifact is missing on disk")
    orphan = [i for i, inv in invs.items() if i not in referenced and inv.get("status") not in ("parse_error",)]
    attempts = sum(1 + len(i.get("attempts") or []) for i in invs.values() if i.get("status") != "parse_error"
                   and not i.get("from_cache"))
    ledgers = {}
    for f in sorted(glob.glob(str(REPO / "results/raw/ledgers" / f"{experiment}_*.json"))) + \
            ([str(REPO / f"results/raw/{experiment}_ledger.json")] if False else []):
        try:
            led = json.loads(Path(f).read_text())
            ledgers[Path(f).name] = {k: led.get(k) for k in ("calls", "input_tokens", "output_tokens", "failed_attempts")}
        except Exception:  # noqa: BLE001
            pass
    outcomes = collections.Counter(d["feasibility"]["outcome"] if "feasibility" in d else d["record"]["status"] for d in lines)
    return {"experiment": experiment, "records": len(lines), "outcomes": dict(outcomes),
            "invocations_logged": len(invs), "invocations_referenced": len(referenced),
            "orphan_invocations": len(orphan), "api_attempts_from_log": attempts,
            "ledgers": ledgers, "ledger_calls_total": sum((v.get("calls") or 0) for v in ledgers.values()),
            "sandbox_executions": n_exec, "sandbox_images": dict(images), "verified_image": verified,
            "cache_hits": cache_hits, "problems": problems}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", action="append", required=True)
    ap.add_argument("--out", default="results/processed/reconciliation.json")
    args = ap.parse_args(argv)
    res = [reconcile(e) for e in args.experiment]
    (REPO / args.out).parent.mkdir(parents=True, exist_ok=True)
    (REPO / args.out).write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))
    return 1 if any(r["problems"] for r in res) else 0


if __name__ == "__main__":
    raise SystemExit(main())
