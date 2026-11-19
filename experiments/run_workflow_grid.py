"""Experiment B grid runner: every path (src.contracts.enumerate_paths) x project x repeat.

    # Plan only (DEFAULT; no AWS client is created, no call is made):
    python -m experiments.run_workflow_grid --projects retail_sales --stages 2 --repeats 1
    # Paid execution (lead only, after user approval): explicit flag AND explicit hard limits
    python -m experiments.run_workflow_grid --projects retail_sales --stages 2 --execute \
        --max-calls 30 --max-input-tokens 300000 --max-output-tokens 80000

Resume / checkpoint
- run_id = make_run_id(experiment_id, models, prompt version, dataset hash, settings+project+path+repeat).
- A run with a record in results/raw/workflow_runs/<experiment_id>.jsonl is COMPLETED whatever its
  outcome (feasible / infeasible / void_infra). Completed runs are skipped and listed; they are never
  re-run. Failed runs are kept.
- void_infra runs are re-attempted ONLY with --retry-void-infra: the new attempt gets a NEW run_id
  (settings + "infra_attempt": k); the void record stays in the file.
- An interrupted run (artifact dir without a record) is re-run; its old directory is moved aside.

Limits
- --execute requires --max-calls/--max-input-tokens/--max-output-tokens (UsageLimits). They are
  enforced by the client's ledger (default: a NEW ledger file per execution under
  results/raw/ledgers/). max_calls counts API attempts incl. retries. The run refuses to start if
  the limits are below the plan's worst case unless --allow-limits-below-plan.
- Worst-case input tokens use the client's own reservation estimate (1 token per prompt byte +
  overhead) with every variable prompt part at its byte cap; worst-case output = maxTokens per call.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.bedrock.client import RetryPolicy
from src.bedrock.models import REPO_ROOT, ModelRegistry, load_registry
from src.contracts import STAGES, ProjectSpec, enumerate_paths, parse_path_id
from src.storage import RunStore
from src.storage.run_store import DEFAULT_ROOT
from src.workflow.orchestrator import (
    PRIMARY_EXPERIMENT_ID,
    PROJECTS_DIR,
    SHARED_PREFIX_EXPERIMENT_ID,
    WorkflowOrchestrator,
)
from src.workflow.stages import prompt_input_token_upper_bound


class _RegistryOnly:
    """Stand-in client for planning: exposes .registry, cannot call anything."""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry


def _spec(project_id: str, projects_dir: Path = PROJECTS_DIR) -> ProjectSpec:
    return ProjectSpec.model_validate_json((projects_dir / project_id / "project.json").read_text())


def select_paths(aliases: list[str], n_stages: int, paths: list[str] | None = None) -> list[str]:
    all_paths = enumerate_paths(aliases, n_stages)
    if not paths:
        return all_paths
    bad = [p for p in paths if p not in all_paths]
    if bad:
        raise ValueError(f"paths {bad} are not {n_stages}-stage paths over {aliases}")
    return [p for p in all_paths if p in set(paths)]


@dataclass
class PlannedRun:
    project_id: str
    path_id: str
    repeat_index: int
    run_id: str
    status: str            # "pending" | "completed" | "retry_void_infra"
    infra_attempt: int = 0
    calls: int = 0
    worst_input_tokens: int = 0
    worst_output_tokens: int = 0


@dataclass
class GridPlan:
    experiment_id: str
    mode: str
    projects: list[str]
    n_stages: int
    paths: list[str]
    repeats: list[int]
    runs: list[PlannedRun] = field(default_factory=list)

    def pending(self) -> list[PlannedRun]:
        return [r for r in self.runs if r.status != "completed"]

    def totals(self, retry_attempts: int = RetryPolicy().max_attempts) -> dict:
        pend = self.pending()
        calls = sum(r.calls for r in pend)
        by_stage: dict[str, int] = {}
        for r in pend:
            for i in range(self.n_stages):
                by_stage[STAGES[i].value] = by_stage.get(STAGES[i].value, 0) + (
                    1 if r.calls > i else 0)
        return {
            "experiment_id": self.experiment_id, "mode": self.mode, "projects": self.projects,
            "n_stages": self.n_stages, "n_paths": len(self.paths), "repeats": self.repeats,
            "n_runs_total": len(self.runs),
            "n_runs_completed_skipped": sum(r.status == "completed" for r in self.runs),
            "n_runs_to_execute": len(pend),
            "planned_model_calls": calls,
            "planned_calls_by_stage": by_stage,
            "worst_case_input_tokens": sum(r.worst_input_tokens for r in pend),
            "worst_case_output_tokens": sum(r.worst_output_tokens for r in pend),
            "worst_case_api_attempts_incl_retries": calls * retry_attempts,
            "notes": [
                "Worst case assumes every stage runs (terminate policy can only reduce calls).",
                "Input tokens: client reservation estimate (1 token/byte + overhead) at prompt byte caps.",
                "Output tokens: maxTokens per call (reasoning tokens count toward it).",
                "max_calls in UsageLimits counts API attempts including throttling retries.",
            ],
        }


def plan_grid(projects: list[str], n_stages: int, *, paths: list[str] | None = None, repeats: int = 1,
              repeat_start: int = 0, mode: str = "fresh", experiment_id: str | None = None,
              registry: ModelRegistry | None = None, max_tokens: int | None = None,
              results_root: str | Path = DEFAULT_ROOT, projects_dir: Path = PROJECTS_DIR,
              retry_void_infra: bool = False, protocol: str = "v2") -> GridPlan:
    """Pure planning: reads project files, prompt templates and existing records; no AWS."""
    registry = registry or load_registry()
    experiment_id = experiment_id or (PRIMARY_EXPERIMENT_ID if mode == "fresh" else SHARED_PREFIX_EXPERIMENT_ID)
    if protocol == "v3" and not experiment_id.endswith("_v3"):
        experiment_id += "_v3"
    sel = select_paths(registry.aliases, n_stages, paths)
    store = RunStore(experiment_id, root=results_root)   # read-only use (no mode pin)
    ident = WorkflowOrchestrator(_RegistryOnly(registry), None, store, mode=mode, projects_dir=projects_dir,
                                 max_tokens=max_tokens, protocol=protocol)
    existing = {r.run_id: r for r in store.load_records()}
    plan = GridPlan(experiment_id, mode, list(projects), n_stages, sel, list(range(repeat_start, repeat_start + repeats)))
    for proj in projects:
        spec = _spec(proj, projects_dir)
        in_bound = {s: prompt_input_token_upper_bound(s, spec, projects_dir / proj, ident.prompt_version) for s in STAGES[:n_stages]}
        for rep in plan.repeats:
            seen_prefixes: set[tuple[str, ...]] = set()
            for path in sel:
                models = parse_path_id(path)
                attempt, status = 0, "pending"
                while True:
                    rid = ident.run_id(proj, path, rep, attempt)
                    rec = existing.get(rid)
                    if rec is None:
                        status = "pending" if attempt == 0 else "retry_void_infra"
                        break
                    if rec.feasibility.outcome == "void_infra" and retry_void_infra:
                        attempt += 1
                        continue
                    status = "completed"
                    break
                calls = w_in = w_out = 0
                for i in range(n_stages):
                    prefix = models[: i + 1]
                    if mode == "shared_prefix" and prefix in seen_prefixes:
                        continue          # worst case: identical request served from the cache
                    seen_prefixes.add(prefix)
                    calls += 1
                    w_in += in_bound[STAGES[i]]
                    w_out += max_tokens or registry.get(models[i]).inference.max_tokens
                plan.runs.append(PlannedRun(proj, path, rep, rid, status, attempt, calls, w_in, w_out))
    return plan


def estimate_pilot_usage(projects: list[str] | tuple[str, ...] = ("retail_sales",), n_stages: int = 2, *,
                         paths: list[str] | None = None, repeats: int = 1, mode: str = "fresh",
                         max_tokens: int | None = None, registry: ModelRegistry | None = None,
                         results_root: str | Path | None = None) -> dict:
    """Worst-case calls/tokens of a pilot, ignoring any existing records unless results_root is given.
    No AWS client is created."""
    import tempfile
    if results_root is None:
        with tempfile.TemporaryDirectory() as tmp:
            return plan_grid(list(projects), n_stages, paths=paths, repeats=repeats, mode=mode,
                             registry=registry, max_tokens=max_tokens, results_root=tmp).totals()
    return plan_grid(list(projects), n_stages, paths=paths, repeats=repeats, mode=mode, registry=registry,
                     max_tokens=max_tokens, results_root=results_root).totals()


# ---------------------------------------------------------------------- execution
def execute_plan(plan: GridPlan, orchestrator: WorkflowOrchestrator, *, log=print) -> dict:
    done, skipped = [], []
    for r in plan.runs:
        if r.status == "completed":
            skipped.append(r.run_id)
            log(f"SKIP completed {r.run_id} ({r.project_id} {r.path_id} rep {r.repeat_index})")
            continue
        rec = orchestrator.run_path(r.project_id, r.path_id, plan.experiment_id, r.repeat_index,
                                    infra_attempt=r.infra_attempt)
        done.append(rec.run_id)
        log(f"RUN {rec.run_id} {r.project_id} {r.path_id} rep {r.repeat_index}: {rec.feasibility.outcome}"
            + (f" (first failure: {rec.feasibility.first_failure_stage.value} "
               f"{rec.feasibility.failure_type.value})" if rec.feasibility.first_failure_stage else ""))
    return {"executed": done, "skipped_completed": skipped}


def check_limits(totals: dict, max_calls: int, max_in: int, max_out: int) -> list[str]:
    problems = []
    if max_calls < totals["planned_model_calls"]:
        problems.append(f"--max-calls {max_calls} < planned calls {totals['planned_model_calls']}")
    if max_in < totals["worst_case_input_tokens"]:
        problems.append(f"--max-input-tokens {max_in} < worst case {totals['worst_case_input_tokens']}")
    if max_out < totals["worst_case_output_tokens"]:
        problems.append(f"--max-output-tokens {max_out} < worst case {totals['worst_case_output_tokens']}")
    return problems


def add_common_args(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--projects", nargs="+", default=["retail_sales"])
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--repeat-start", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=None, help="override maxTokens for EVERY model")
    ap.add_argument("--results-root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--plan", action="store_true", help="print the plan (default when --execute is absent)")
    ap.add_argument("--execute", action="store_true", help="make PAID Bedrock calls (requires hard limits)")
    ap.add_argument("--max-calls", type=int)
    ap.add_argument("--max-input-tokens", type=int)
    ap.add_argument("--max-output-tokens", type=int)
    ap.add_argument("--ledger", type=Path, default=None)
    ap.add_argument("--allow-limits-below-plan", action="store_true")


def require_limits(args, totals: dict) -> Any:
    from src.bedrock.usage import UsageLimits
    missing = [n for n in ("max_calls", "max_input_tokens", "max_output_tokens") if getattr(args, n) is None]
    if missing:
        raise SystemExit(f"--execute requires explicit hard limits: missing {', '.join('--' + m.replace('_', '-') for m in missing)}")
    problems = check_limits(totals, args.max_calls, args.max_input_tokens, args.max_output_tokens)
    if problems and not args.allow_limits_below_plan:
        raise SystemExit("limits below the plan's worst case (use --allow-limits-below-plan to accept "
                         "budget-refused void_infra runs):\n  " + "\n  ".join(problems))
    return UsageLimits(max_calls=args.max_calls, max_input_tokens=args.max_input_tokens,
                       max_output_tokens=args.max_output_tokens)


def default_ledger(results_root: Path, experiment_id: str) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return results_root / "ledgers" / f"{experiment_id}_{ts}.json"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(ap)
    ap.add_argument("--stages", type=int, choices=(2, 3), default=2)
    ap.add_argument("--paths", nargs="+", default=None, help="subset of enumerated paths, e.g. A-B B-B")
    ap.add_argument("--mode", choices=("fresh", "shared_prefix"), default="fresh")
    ap.add_argument("--experiment-id", default=None)
    ap.add_argument("--retry-void-infra", action="store_true")
    ap.add_argument("--protocol", choices=("v2", "v3"), default="v2",
                    help="v3 = prospective primary (prompts/v3 + reporting validator v3; experiment id gets _v3)")
    args = ap.parse_args(argv)

    plan = plan_grid(args.projects, args.stages, paths=args.paths, repeats=args.repeats,
                     repeat_start=args.repeat_start, mode=args.mode, experiment_id=args.experiment_id,
                     max_tokens=args.max_tokens, results_root=args.results_root,
                     retry_void_infra=args.retry_void_infra, protocol=args.protocol)
    totals = plan.totals()
    print(json.dumps(totals, indent=2))
    for r in plan.runs:
        if r.status == "completed":
            print(f"completed (will skip): {r.run_id} {r.project_id} {r.path_id} rep {r.repeat_index}")
    if not args.execute:
        print("PLAN ONLY: no AWS client created, no model call made. Add --execute and hard limits to run.")
        return 0

    limits = require_limits(args, totals)
    # Paid path: only reached with --execute.
    from src.bedrock.client import BedrockClient
    from src.workflow.executor import DockerExecutor
    from src.workflow.stages import SandboxGate
    executor = DockerExecutor()
    gate = SandboxGate()
    decision = gate.check(executor)
    if not decision.ok or decision.image_id is None:
        raise SystemExit(f"sandbox preflight failed before any model call: {decision.reason}")
    with executor.image_lease(decision.image_id):
        client = BedrockClient(limits=limits,
                               ledger_path=args.ledger or default_ledger(args.results_root, plan.experiment_id))
        store = RunStore(plan.experiment_id, root=args.results_root)
        orch = WorkflowOrchestrator(client, executor, store, gate=gate, mode=args.mode,
                                    max_tokens=args.max_tokens, protocol=args.protocol)
        summary = execute_plan(plan, orch)
    print(json.dumps({k: len(v) for k, v in summary.items()}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
