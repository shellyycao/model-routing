"""SYNTHETIC_FIXTURE generator for XAI routing tests. NOT experimental data. NOT results.

Every number here is invented to exercise the routing / explanation / counterfactual code paths.
Nothing generated here may be presented as a result or written to results/.

Three invented projects (synthetic_fixture_p1..p3), models A/B/C, all 27 paths.
Built-in (invented) cross-stage interactions so S2 and S3 can disagree:
  * B at cleaning followed by a different analysis model: analysis pass probability x0.55 and
    analysis.numerical_accuracy -0.15;
  * C at analysis followed by A at reporting: reporting.unsupported_claim_count +1.0;
  * every model switch adds 800 ms orchestration time; every run adds 200 ms overhead.
Includes one INFRA_ERROR stage record, one cache-hit stage record and one void_infra workflow run.

Regenerate the committed JSONL:
  .venv/bin/python -m tests.fixtures.xai.SYNTHETIC_FIXTURE_generator
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from src.contracts import (
    STAGES,
    Feasibility,
    FailureType,
    StageBenchmarkRecord,
    StageId,
    StageRunRecord,
    StageStatus,
    StageTimings,
    ValidationResult,
    WorkflowEfficiency,
    WorkflowRunRecord,
    enumerate_paths,
    n_switches,
)

MARK = "SYNTHETIC_FIXTURE"
PROJECTS = ["synthetic_fixture_p1", "synthetic_fixture_p2", "synthetic_fixture_p3"]
MODELS = ["A", "B", "C"]
EXP_A = f"{MARK}_expA_stage"
EXP_B = f"{MARK}_expB_paths"
TS = "2026-01-01T00:00:00Z"
JSONL_PATH = Path(__file__).with_name(f"{MARK}_records.jsonl")

P_PASS = {"cleaning": {"A": 0.97, "B": 0.95, "C": 0.92},
          "analysis": {"A": 0.97, "B": 0.9, "C": 0.92},
          "reporting": {"A": 0.97, "B": 0.95, "C": 0.92}}
QUALITY = {
    "cleaning": {"A": (0.97, 0.98, 1.0), "B": (0.93, 0.95, 0.98), "C": (0.95, 0.96, 0.99)},
    "analysis": {"A": (0.97, 0.98, 1.0), "B": (0.93, 0.94, 0.97), "C": (0.95, 0.96, 0.98)},
    "reporting": {"A": (0.95, 0.95, 0.2), "B": (0.9, 0.9, 0.7), "C": (0.92, 0.93, 0.4)},
}
METRICS = {"cleaning": ("cleaning_correctness", "data_integrity", "schema_compliance"),
           "analysis": ("numerical_accuracy", "calculation_coverage", "reproducibility"),
           "reporting": ("numerical_consistency", "finding_coverage", "unsupported_claim_count")}
TIME_MS = {"cleaning": {"A": 9000, "B": 4000, "C": 6000},
           "analysis": {"A": 11000, "B": 5000, "C": 3500},
           "reporting": {"A": 8000, "B": 3500, "C": 5000}}
TOKENS = {"A": 3000, "B": 2500, "C": 4000}
PROJECT_OFFSET = {"synthetic_fixture_p1": 0.0, "synthetic_fixture_p2": -0.01, "synthetic_fixture_p3": 0.01}


def _quality(stage: str, model: str, project: str, rng: random.Random, acc_shift=0.0, claim_shift=0.0) -> dict:
    base = QUALITY[stage][model]
    q = {}
    for m, b in zip(METRICS[stage], base):
        if m == "unsupported_claim_count":
            q[m] = float(max(0.0, round(b + claim_shift + rng.uniform(-0.2, 0.2), 3)))
        else:
            shift = acc_shift if m == "numerical_accuracy" else 0.0
            q[m] = round(min(1.0, max(0.0, b + PROJECT_OFFSET[project] + shift + rng.uniform(-0.01, 0.01))), 4)
    return q


def _stage_run(stage: str, model: str, status: StageStatus, quality: dict | None, rng: random.Random,
               run_tag: str, cache_hit: bool = False, failure: FailureType | None = None) -> StageRunRecord:
    executed = status in (StageStatus.PASSED, StageStatus.FAILED)
    gen = TIME_MS[stage][model] * rng.uniform(0.95, 1.05)
    return StageRunRecord(
        stage=StageId(stage), model_alias=model, model_id=f"{MARK}-model-{model}", prompt_version=MARK,
        invocation_ids=[f"{MARK}-inv-{run_tag}-{stage}"] if executed else [], cache_hit=cache_hit, status=status,
        failure_type=failure, parse_ok=True if executed else None,
        validation=ValidationResult(stage=StageId(stage), hard_pass=status == StageStatus.PASSED, checks=[],
                                    quality=quality or {}) if executed else None,
        input_tokens=int(TOKENS[model] * 0.6) if executed else None,
        output_tokens=int(TOKENS[model] * 0.4) if executed else None,
        cost_usd=None, cost_status="unavailable",
        timings=StageTimings(generation_ms=None if (cache_hit or not executed) else round(gen * 0.8, 1),
                             execution_ms=round(gen * 0.15, 1) if executed else None,
                             validation_ms=round(gen * 0.05, 1) if executed else None),
    )


def experiment_a(repeats: int = 4) -> list[StageBenchmarkRecord]:
    out = []
    for proj in PROJECTS:
        for stage in METRICS:
            for model in MODELS:
                for r in range(repeats):
                    rng = random.Random(f"{MARK}|A|{proj}|{stage}|{model}|{r}")
                    passed = rng.random() < P_PASS[stage][model]
                    status = StageStatus.PASSED if passed else StageStatus.FAILED
                    tag = f"{proj}-{stage}-{model}-r{r}"
                    rec = _stage_run(stage, model, status, _quality(stage, model, proj, rng) if passed else {},
                                     rng, tag, failure=None if passed else FailureType.VALIDATION_FAILED,
                                     cache_hit=(proj == "synthetic_fixture_p1" and stage == "reporting"
                                                and model == "B" and r == 3 and passed))
                    out.append(StageBenchmarkRecord(run_id=f"{MARK}-expA-{tag}", experiment_id=EXP_A, project_id=proj,
                                                    stage=StageId(stage), model_alias=model, repeat_index=r,
                                                    canonical_inputs=[f"{MARK}/canonical/{stage}"],
                                                    config_hash=MARK, record=rec))
    # One void infrastructure record (excluded by estimators).
    rng = random.Random(f"{MARK}|A|infra")
    rec = _stage_run("analysis", "C", StageStatus.INFRA_ERROR, None, rng, "infra", failure=FailureType.INFRA)
    out.append(StageBenchmarkRecord(run_id=f"{MARK}-expA-synthetic_fixture_p2-analysis-C-infra",
                                    experiment_id=EXP_A, project_id="synthetic_fixture_p2", stage=StageId.ANALYSIS,
                                    model_alias="C", repeat_index=99, canonical_inputs=[f"{MARK}/canonical/analysis"],
                                    config_hash=MARK, record=rec))
    return out


def _workflow_run(proj: str, path: str, r: int) -> WorkflowRunRecord:
    rng = random.Random(f"{MARK}|B|{proj}|{path}|{r}")
    models = path.split("-")
    stages, quality, failed = [], {}, None
    total_ms, toks = 200.0 + 800.0 * n_switches(path), 0
    tag = f"{proj}-{path}-r{r}"
    for i, st in enumerate(STAGES):
        s, m = st.value, models[i]
        if failed is not None:
            stages.append(_stage_run(s, m, StageStatus.NOT_RUN_UPSTREAM_FAILURE, None, rng, tag))
            continue
        p = P_PASS[s][m]
        acc_shift = claim_shift = 0.0
        if s == "analysis" and models[0] == "B" and m != "B":
            p *= 0.55
            acc_shift = -0.15
        if s == "reporting" and models[1] == "C" and m == "A":
            claim_shift = 1.0
        ok = rng.random() < p
        q = _quality(s, m, proj, rng, acc_shift, claim_shift) if ok else None
        rec = _stage_run(s, m, StageStatus.PASSED if ok else StageStatus.FAILED, q, rng, tag,
                         failure=None if ok else FailureType.VALIDATION_FAILED)
        stages.append(rec)
        total_ms += sum(x for x in (rec.timings.generation_ms, rec.timings.execution_ms, rec.timings.validation_ms)
                        if x is not None)
        toks += (rec.input_tokens or 0) + (rec.output_tokens or 0)
        if ok:
            quality[s] = q
        else:
            failed = st
    status = {x.stage.value: x.status for x in stages}
    feas = Feasibility(outcome="feasible" if failed is None else "infeasible", stage_status=status,
                       first_failure_stage=failed, failure_type=None if failed is None else FailureType.VALIDATION_FAILED)
    return WorkflowRunRecord(
        run_id=f"{MARK}-expB-{tag}", experiment_id=EXP_B, project_id=proj, path_id=path, models=models,
        repeat_index=r, config_hash=MARK, started_at=TS, finished_at=TS, stages=stages, feasibility=feas,
        quality=quality if failed is None else {},
        efficiency=WorkflowEfficiency(end_to_end_ms=round(total_ms, 1), input_tokens=int(toks * 0.6),
                                      output_tokens=toks - int(toks * 0.6), cost_usd=None,
                                      cost_status="unavailable", n_calls=sum(bool(x.invocation_ids) for x in stages),
                                      n_switches=n_switches(path)),
    )


def experiment_b(repeats: int = 2) -> list[WorkflowRunRecord]:
    out = [_workflow_run(p, path, r) for p in PROJECTS for path in enumerate_paths(MODELS) for r in range(repeats)]
    # One void infrastructure run (excluded from outcomes).
    rng = random.Random(f"{MARK}|B|infra")
    tag = "synthetic_fixture_p3-A-A-A-infra"
    stages = [_stage_run("cleaning", "A", StageStatus.INFRA_ERROR, None, rng, tag, failure=FailureType.INFRA),
              _stage_run("analysis", "A", StageStatus.NOT_RUN_UPSTREAM_FAILURE, None, rng, tag),
              _stage_run("reporting", "A", StageStatus.NOT_RUN_UPSTREAM_FAILURE, None, rng, tag)]
    out.append(WorkflowRunRecord(
        run_id=f"{MARK}-expB-{tag}", experiment_id=EXP_B, project_id="synthetic_fixture_p3", path_id="A-A-A",
        models=["A", "A", "A"], repeat_index=99, config_hash=MARK, started_at=TS, stages=stages,
        feasibility=Feasibility(outcome="void_infra", stage_status={x.stage.value: x.status for x in stages},
                                first_failure_stage=StageId.CLEANING, failure_type=FailureType.INFRA),
        efficiency=WorkflowEfficiency(cost_status="unavailable")))
    return out


def build_records() -> list:
    return [*experiment_a(), *experiment_b()]


def write_jsonl(path: Path = JSONL_PATH) -> Path:
    with open(path, "w") as fh:
        for r in build_records():
            fh.write(r.model_dump_json() + "\n")
    return path


if __name__ == "__main__":
    print(write_jsonl())
