"""Experiment A: each model x stage x project on CANONICAL inputs -> StageBenchmarkRecord.

    python -m experiments.run_stage_benchmark --projects retail_sales            # plan only (default)
    python -m experiments.run_stage_benchmark --projects retail_sales --execute \
        --max-calls 20 --max-input-tokens 200000 --max-output-tokens 40000

Inputs per stage (the only files mounted / rendered):
  cleaning   ProjectSpec.model_input_files() (raw data)
  analysis   the project's canonical cleaned CSV (mounted as cleaned_data_filename)
  reporting  the project's canonical findings.json
The same prompt templates, stage functions, inference settings and validators as Experiment B are
used; the handoff package is built by src.workflow.handoff.canonical_upstream. Every call is fresh
(use_cache=False). Records: results/raw/stage_benchmark/<experiment_id>.jsonl, artifacts under
results/raw/runs/<run_id>/. Completed run_ids are skipped, never re-run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.bedrock.models import ModelRegistry, load_registry
from src.bedrock.provenance import config_hash, hash_file, hash_tree, make_run_id
from src.contracts import STAGES, ResourceLimits, StageBenchmarkRecord, StageId
from src.evaluation.cleaning import load_project
from src.storage import STAGE_BENCHMARK, RunStore
from src.storage.run_store import DEFAULT_ROOT
from src.workflow.handoff import HANDOFF_POLICY_VERSION, build_and_save, canonical_upstream
from src.workflow.orchestrator import PROJECTS_DIR, WORKFLOW_VERSION
from src.workflow.stages import (
    PROMPT_VERSION,
    PROTOCOLS,
    SandboxGate,
    StageContext,
    display_path,
    model_input_files,
    prompt_input_token_upper_bound,
    run_analysis,
    run_cleaning,
    run_reporting,
    template_hashes,
)

from .run_workflow_grid import add_common_args, default_ledger, require_limits

EXPERIMENT_ID = "expA_stage"


def _settings(max_tokens: int | None, limits: ResourceLimits) -> dict:
    return {"workflow_version": WORKFLOW_VERSION, "prompt_templates": template_hashes(),
            "handoff_policy": HANDOFF_POLICY_VERSION, "max_tokens": max_tokens,
            "resource_limits": limits.model_dump(mode="json"), "inputs": "canonical"}


def protocol_for(experiment_id: str) -> str:
    """v3 (prospective primary) experiments are named *_v3; everything else is frozen v2."""
    return "v3" if experiment_id.endswith("_v3") else "v2"


def _pv(experiment_id: str) -> str:
    return PROTOCOLS[protocol_for(experiment_id)]["prompt_version"]


def stage_run_id(registry: ModelRegistry, project_id: str, stage: StageId, alias: str, repeat_index: int,
                 *, experiment_id: str = EXPERIMENT_ID, max_tokens: int | None = None,
                 limits: ResourceLimits | None = None, projects_dir: Path = PROJECTS_DIR) -> str:
    limits = limits or ResourceLimits()
    return make_run_id(experiment_id, registry, _pv(experiment_id), hash_tree(projects_dir / project_id),
                       extra={"settings": _settings(max_tokens, limits), "project_id": project_id,
                              "stage": stage.value, "model": alias, "repeat_index": repeat_index})


def run_stage_benchmark(client: Any, executor: Any, store: RunStore, project_id: str, stage: StageId, alias: str,
                        repeat_index: int = 0, *, gate: SandboxGate | None = None, max_tokens: int | None = None,
                        resource_limits: ResourceLimits | None = None,
                        projects_dir: Path = PROJECTS_DIR) -> StageBenchmarkRecord:
    if store.kind != STAGE_BENCHMARK:
        raise ValueError("needs a stage_benchmark store")
    store._pin_mode("fresh")
    limits = resource_limits or ResourceLimits()
    registry = client.registry
    run_id = stage_run_id(registry, project_id, stage, alias, repeat_index, experiment_id=store.experiment_id,
                          max_tokens=max_tokens, limits=limits, projects_dir=projects_dir)
    run_dir = store.prepare_run_dir(run_id)
    spec, gt, pdir = load_project(projects_dir / project_id)
    ctx = StageContext(client=client, executor=executor, gate=gate or SandboxGate(), spec=spec, project_dir=pdir,
                       ground_truth=gt, experiment_id=store.experiment_id, run_id=run_id, path_id=alias,
                       repeat_index=repeat_index, use_cache=False, max_tokens=max_tokens, resource_limits=limits,
                       protocol=protocol_for(store.experiment_id))
    upstream = canonical_upstream(spec, pdir, stage)
    sdir = run_dir / stage.value
    pkg, size, hms = build_and_save(spec, alias, stage, upstream, sdir / "handoff_in.json")
    info = (str(sdir / "handoff_in.json"), size, hms)
    if stage == StageId.CLEANING:
        inputs = list(model_input_files(spec, pdir).values())
        res = run_cleaning(ctx, alias, pkg, info, sdir)
    elif stage == StageId.ANALYSIS:
        inputs = [str(pdir / spec.canonical_cleaned_file)]
        res = run_analysis(ctx, alias, pkg, info, sdir, inputs[0])
    else:
        inputs = [str(pdir / spec.canonical_findings_file)]
        # canonical findings == ground truth, so a separate conditional basis would duplicate `validation`
        res = run_reporting(ctx, alias, pkg, info, sdir, inputs[0], conditional_basis=False)
    rec = StageBenchmarkRecord(
        run_id=run_id, experiment_id=store.experiment_id, project_id=project_id, stage=stage, model_alias=alias,
        repeat_index=repeat_index, canonical_inputs=[display_path(p) for p in inputs],
        canonical_input_hashes={display_path(p): hash_file(p) for p in inputs},
        config_hash=config_hash(registry, _pv(store.experiment_id), hash_tree(pdir), extra=_settings(max_tokens, limits)),
        record=res.record)
    store.append(rec)
    return rec


def plan_stage_benchmark(projects: list[str], *, stages: list[StageId] | None = None, models: list[str] | None = None,
                         repeats: int = 1, repeat_start: int = 0, max_tokens: int | None = None,
                         registry: ModelRegistry | None = None, results_root: Path = DEFAULT_ROOT,
                         experiment_id: str = EXPERIMENT_ID, projects_dir: Path = PROJECTS_DIR) -> dict:
    registry = registry or load_registry()
    stages = stages or list(STAGES)
    models = models or registry.aliases
    done = RunStore(experiment_id, root=results_root, kind=STAGE_BENCHMARK).completed_run_ids()
    planned, skipped, w_in, w_out = [], [], 0, 0
    for proj in projects:
        spec, _, pdir = load_project(projects_dir / proj)
        for st in stages:
            bound = prompt_input_token_upper_bound(st, spec, pdir, _pv(experiment_id))
            for a in models:
                for rep in range(repeat_start, repeat_start + repeats):
                    rid = stage_run_id(registry, proj, st, a, rep, experiment_id=experiment_id, max_tokens=max_tokens,
                                       projects_dir=projects_dir)
                    item = {"project_id": proj, "stage": st.value, "model": a, "repeat_index": rep, "run_id": rid}
                    if rid in done:
                        skipped.append(item)
                        continue
                    planned.append(item)
                    w_in += bound
                    w_out += max_tokens or registry.get(a).inference.max_tokens
    return {"experiment_id": experiment_id, "planned_model_calls": len(planned), "skipped_completed": skipped,
            "worst_case_input_tokens": w_in, "worst_case_output_tokens": w_out, "planned": planned}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(ap)
    ap.add_argument("--stages", nargs="+", choices=[s.value for s in STAGES], default=None)
    ap.add_argument("--models", nargs="+", default=None)
    ap.add_argument("--experiment-id", default=None)
    ap.add_argument("--protocol", choices=("v2", "v3"), default="v2",
                    help="v3 = prospective primary; default experiment id becomes expA_stage_v3")
    args = ap.parse_args(argv)
    if args.experiment_id is None:
        args.experiment_id = EXPERIMENT_ID + ("_v3" if args.protocol == "v3" else "")
    if protocol_for(args.experiment_id) != args.protocol:
        raise SystemExit(f"--protocol {args.protocol} does not match experiment id {args.experiment_id!r}")
    stages = [StageId(s) for s in args.stages] if args.stages else None
    plan = plan_stage_benchmark(args.projects, stages=stages, models=args.models, repeats=args.repeats,
                                repeat_start=args.repeat_start, max_tokens=args.max_tokens,
                                results_root=args.results_root, experiment_id=args.experiment_id)
    print(json.dumps({k: v for k, v in plan.items() if k != "planned"}, indent=2))
    if not args.execute:
        print("PLAN ONLY: no AWS client created, no model call made.")
        return 0
    limits = require_limits(args, plan)
    from src.bedrock.client import BedrockClient
    from src.workflow.executor import DockerExecutor
    ex = DockerExecutor()
    gate = SandboxGate()
    decision = gate.check(ex)
    if not decision.ok or decision.image_id is None:
        raise SystemExit(f"sandbox preflight failed before any model call: {decision.reason}")
    with ex.image_lease(decision.image_id):
        client = BedrockClient(limits=limits,
                               ledger_path=args.ledger or default_ledger(args.results_root, args.experiment_id))
        store = RunStore(args.experiment_id, root=args.results_root, kind=STAGE_BENCHMARK)
        for it in plan["planned"]:
            rec = run_stage_benchmark(client, ex, store, it["project_id"], StageId(it["stage"]), it["model"],
                                      it["repeat_index"], gate=gate, max_tokens=args.max_tokens)
            print(f"{rec.run_id} {it}: {rec.record.status.value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
