"""Part A extension runner: independent tasks A1/A2/A3 x models (plan by default; --execute is PAID).

  .venv/bin/python -m experiments.run_independent_benchmark --task all --plan
  .venv/bin/python -m experiments.run_independent_benchmark --task all --execute --max-calls N --max-input-tokens N --max-output-tokens N

Reuses BedrockClient (fresh calls, limits, ledger, invocation log), provenance run ids (completed runs are
skipped, never silently repeated) and, for A1, the verified Docker sandbox (SandboxGate + image lease).
Records: results/raw/independent/<experiment_id>.jsonl (IndependentTaskRecord; append-only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.bedrock.models import load_registry
from src.bedrock.provenance import config_hash, hash_file, hash_tree, make_run_id
from src.independent import EXPERIMENT_IDS, PROMPT_VERSION
from src.independent.records import IndependentTaskRecord
from src.independent.tasks import (A1_HARNESS, A1Response, A2Response, A3Response, a1_vars, a3_candidates_text,
                                   score_a1, score_a2, score_a3)

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "datasets/independent"
PROMPTS = REPO / "prompts" / PROMPT_VERSION
RAW = REPO / "results/raw/independent"
SCHEMAS = {"a1": A1Response, "a2": A2Response, "a3": A3Response}
TEMPLATES = {"a1": "a1_debugging.txt", "a2": "a2_extraction.txt", "a3": "a3_literature.txt"}
MAX_TOKENS = 4096   # identical for every model (same as Parts A/B)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_cases(task: str) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((DATA / task / "cases").glob("*.json"))]


def render(task: str, case: dict) -> str:
    t = (PROMPTS / TEMPLATES[task]).read_text()
    if task == "a1":
        v = a1_vars(case)
    elif task == "a2":
        v = {"schema": "\n".join(f"- {k}: {d}" for k, d in case["schema"].items()), "document": case["document"]}
    else:
        v = {"query": case["query"]["text"], "candidates": a3_candidates_text(case)}
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    assert "{{" not in t, f"unrendered placeholder in {task}"
    return t


def run_id(registry, task: str, case: dict, alias: str, repeat: int) -> str:
    return make_run_id(EXPERIMENT_IDS[task], registry, PROMPT_VERSION, hash_tree(DATA / task),
                       extra={"case": case["case_id"], "model": alias, "repeat": repeat, "max_tokens": MAX_TOKENS,
                              "templates": hash_tree(PROMPTS)})


def completed(task: str) -> set[str]:
    p = RAW / f"{EXPERIMENT_IDS[task]}.jsonl"
    return {json.loads(l)["run_id"] for l in p.read_text().splitlines() if l.strip()} if p.exists() else set()


def plan(tasks: list[str], models: list[str], repeat: int) -> dict:
    registry = load_registry()
    rows, w_in = [], 0
    for task in tasks:
        done = completed(task)
        for case in load_cases(task):
            prompt_bytes = len(render(task, case).encode()) + 2000   # + structured-output schema instruction
            for a in models:
                rid = run_id(registry, task, case, a, repeat)
                if rid in done:
                    continue
                rows.append((task, case["case_id"], a, rid))
                w_in += prompt_bytes + 256
    return {"planned_calls": len(rows), "by_task": {t: sum(r[0] == t for r in rows) for t in tasks},
            "worst_case_input_tokens": w_in, "worst_case_output_tokens": len(rows) * MAX_TOKENS,
            "worst_case_api_attempts_incl_retries": len(rows) * 5, "runs": rows}


def execute(tasks, models, repeat, limits, ledger) -> dict:
    from src.bedrock.client import BedrockClient
    from src.bedrock.usage import InvocationContext
    from src.workflow.executor import DockerExecutor
    from src.workflow.stages import SandboxGate

    client = BedrockClient(limits=limits, ledger_path=ledger)
    registry = client.registry
    executor = gate_decision = None
    if "a1" in tasks:
        executor = DockerExecutor()
        gate_decision = SandboxGate().check(executor)
        if not gate_decision.ok:
            raise SystemExit(f"sandbox gate refused before any model call: {gate_decision.reason}")
    RAW.mkdir(parents=True, exist_ok=True)
    summary = {"executed": 0, "skipped_completed": 0, "void_infra": 0}
    ds_version = (DATA / "a1" / "VERSION").read_text().strip()

    def one(task, case, alias):
        rid = run_id(registry, task, case, alias, repeat)
        if rid in completed(task):
            summary["skipped_completed"] += 1
            return
        rdir = REPO / "results/raw/runs" / rid
        rdir.mkdir(parents=True, exist_ok=True)
        prompt = render(task, case)
        (rdir / "prompt.txt").write_text(prompt)
        spec = registry.get(alias)
        rec = dict(run_id=rid, experiment_id=EXPERIMENT_IDS[task], task=task, case_id=case["case_id"],
                   model_alias=alias, model_id=spec.model_id, repeat_index=repeat, prompt_version=PROMPT_VERSION,
                   prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(), dataset_version=ds_version,
                   case_hash=hash_file(DATA / task / "cases" / f"{case['case_id']}.json"),
                   config_hash=config_hash(registry, PROMPT_VERSION, hash_tree(DATA / task), extra={"max_tokens": MAX_TOKENS}),
                   started_at=now())
        ctx = InvocationContext(experiment_id=EXPERIMENT_IDS[task], run_id=rid, stage_id=task,
                                prompt_version=PROMPT_VERSION, repeat_index=repeat)
        try:
            sr = client.converse_structured(alias, prompt, SCHEMAS[task], context=ctx, use_cache=False,
                                            max_tokens=MAX_TOKENS)
        except Exception as e:  # noqa: BLE001  (API/budget/infra) -> void, never a model failure
            rec.update(status="void_infra", failure_type="infra", failure_detail=str(e)[:500], finished_at=now())
            _append(task, rec); summary["void_infra"] += 1
            return
        r = sr.result.record
        (rdir / "response.txt").write_text(sr.result.text or "")
        rec.update(invocation_ids=[r.invocation_id], parse_ok=sr.parsed is not None, truncated=bool(r.truncated),
                   generation_ms=r.latency_ms, input_tokens=r.input_tokens, output_tokens=r.output_tokens,
                   reasoning_chars=r.reasoning_chars, cost_usd=r.cost_usd, cost_status=r.cost_status,
                   artifacts=[str((rdir / n).relative_to(REPO)) for n in ("prompt.txt", "response.txt")])
        if sr.parsed is None:
            rec.update(status="failed", failure_type="truncated" if r.truncated else "parse_error",
                       failure_detail=str(sr.parse_error)[:500], finished_at=now())
            _append(task, rec); summary["executed"] += 1
            return
        (rdir / "parsed.json").write_text(sr.parsed.model_dump_json(indent=2))
        if task == "a1":
            sol, tests = rdir / "solution.py", rdir / "tests.json"
            sol.write_text(sr.parsed.fixed_code); tests.write_text(json.dumps(case["hidden"]))
            res = executor.execute(A1_HARNESS, {"solution.py": str(sol), "tests.json": str(tests)}, str(rdir / "output"))
            rec["execution"] = {"status": res.status.value, "runtime_ms": res.runtime_ms, "sandbox_image": res.sandbox_image,
                                "stderr_tail": (res.stderr or "")[-400:]}
            if res.status.value == "sandbox_unavailable":
                rec.update(status="void_infra", failure_type="infra", failure_detail=res.stderr[:300], finished_at=now())
                _append(task, rec); summary["void_infra"] += 1
                return
            out = rdir / "output" / "results.json"
            harness = json.loads(out.read_text()) if out.exists() else None
            ok, scores, detail = score_a1(case, sr.parsed, harness)
            if harness is None:
                rec["failure_type"] = "timeout" if res.status.value == "timeout" else "execution_error"
        elif task == "a2":
            ok, scores, detail = score_a2(case, sr.parsed)
        else:
            ok, scores, detail = score_a3(case, sr.parsed)
        rec.update(scores=scores, status="passed" if ok else "failed",
                   failure_type=None if ok else (rec.get("failure_type") or "validation_failed"),
                   failure_detail=detail, finished_at=now())
        _append(task, rec); summary["executed"] += 1

    def _run_all():
        for task in tasks:
            for case in load_cases(task):
                for a in models:
                    one(task, case, a)

    if executor is not None:
        with executor.image_lease(gate_decision.image_id):
            _run_all()
    else:
        _run_all()
    return summary


def _append(task: str, rec: dict) -> None:
    line = IndependentTaskRecord(**rec).model_dump_json()
    with (RAW / f"{EXPERIMENT_IDS[task]}.jsonl").open("a") as f:
        f.write(line + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", choices=("a1", "a2", "a3", "all"), default="all")
    ap.add_argument("--models", nargs="+", default=None)
    ap.add_argument("--repeat", type=int, default=0)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--max-calls", type=int)
    ap.add_argument("--max-input-tokens", type=int)
    ap.add_argument("--max-output-tokens", type=int)
    args = ap.parse_args(argv)
    tasks = ["a1", "a2", "a3"] if args.task == "all" else [args.task]
    models = args.models or load_registry().aliases
    p = plan(tasks, models, args.repeat)
    print(json.dumps({k: v for k, v in p.items() if k != "runs"}, indent=2))
    if not args.execute:
        print("PLAN ONLY: no AWS client created, no model call made.")
        return 0
    if None in (args.max_calls, args.max_input_tokens, args.max_output_tokens):
        raise SystemExit("--execute requires --max-calls, --max-input-tokens and --max-output-tokens")
    from src.bedrock.usage import UsageLimits
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ledger = REPO / "results/raw/ledgers" / f"independent_{args.task}_{ts}.json"
    summary = execute(tasks, models, args.repeat, UsageLimits(max_calls=args.max_calls, max_input_tokens=args.max_input_tokens,
                                                              max_output_tokens=args.max_output_tokens), ledger)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
