"""SYNTHETIC_FIXTURE record builder for analysis tests. NOT experimental data. NOT results.

Every number is invented and chosen so the expected table values can be checked by hand
(see tests/test_analysis.py). Nothing built here may be written under results/.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.contracts import (
    STAGES,
    CheckResult,
    Feasibility,
    FailureType,
    PropagationSummary,
    StageBenchmarkRecord,
    StageRunRecord,
    StageStatus,
    ValidationResult,
    WorkflowEfficiency,
    WorkflowRunRecord,
    n_switches,
    parse_path_id,
)

MARK = "SYNTHETIC_FIXTURE"
EXP_B = f"{MARK}_expB"
EXP_A = f"{MARK}_expA"
PROJECT = "synthetic_fixture_p1"
TS = "2026-01-01T00:00:00+00:00"
VALIDATOR = {"cleaning": "1.0", "analysis": "1.0", "reporting": "2.0"}


def _val(stage, passed, quality, basis="ground_truth"):
    return ValidationResult(stage=stage, hard_pass=passed, quality=quality, quality_basis=basis,
                            validator_version=VALIDATOR[stage],
                            checks=[CheckResult(name="mandatory", passed=passed, mandatory=True)])


def run(run_id: str, path: str, statuses: list[str], gt: dict, cond: dict | None = None, *, e2e=1000.0,
        api=600.0, tin=100, tout=50, repeat=0, exp=EXP_B, project=PROJECT) -> WorkflowRunRecord:
    """statuses per stage: passed | failed | blocked | infra | not_run. gt/cond: {stage: {metric: v}}."""
    cond = cond or {}
    models = list(parse_path_id(path))
    smap = {"passed": StageStatus.PASSED, "failed": StageStatus.FAILED, "infra": StageStatus.INFRA_ERROR,
            "blocked": StageStatus.BLOCKED_BY_INVALID_ARTIFACT, "not_run": StageStatus.NOT_RUN_UPSTREAM_FAILURE}
    stages = []
    for i, (m, st) in enumerate(zip(models, statuses)):
        name = STAGES[i].value
        status = smap[st]
        ran = st in ("passed", "failed")
        stages.append(StageRunRecord(
            stage=STAGES[i], model_alias=m, model_id=f"{MARK}-{m}", prompt_version="v2",
            invocation_ids=[f"{run_id}-{name}"] if st in ("passed", "failed", "infra") else [],
            status=status, structural_ok=ran,
            failure_type={"failed": FailureType.VALIDATION_FAILED, "infra": FailureType.INFRA}.get(st),
            failure_detail="upstream artifact unusable" if st == "blocked" else None,
            validation=_val(name, st == "passed", gt[name]) if ran and name in gt else None,
            conditional_validation=_val(name, st == "passed", cond[name], "conditional_reference")
            if ran and name in cond else None))
    first_bad = next((s for s in stages if s.status != StageStatus.PASSED), None)
    outcome = "feasible" if first_bad is None else (
        "void_infra" if any(s.status == StageStatus.INFRA_ERROR for s in stages) else "infeasible")
    names = [s.stage.value for s in stages]
    impact = {s: {m: cond[s][m] - gt[s][m] for m in cond[s]} for s in cond}
    sev = {names[i]: {m: 1 - v for m, v in gt[names[i - 1]].items()}
           for i in range(1, len(names)) if names[i - 1] in gt and stages[i].status in (StageStatus.PASSED,
                                                                                        StageStatus.FAILED)}
    prop = PropagationSummary(
        downstream_executable={s.stage.value: s.status in (StageStatus.PASSED, StageStatus.FAILED) for s in stages},
        upstream_error_severity=sev, end_to_end_accuracy=dict(gt.get(names[-1], {})),
        propagation_impact=impact,
        blocked_stages=[s.stage.value for s in stages if s.status == StageStatus.BLOCKED_BY_INVALID_ARTIFACT])
    return WorkflowRunRecord(
        run_id=f"{MARK}-{run_id}", experiment_id=exp, project_id=project, path_id=path, models=models,
        repeat_index=repeat, config_hash="0" * 64, failure_policy="continue_with_actual_artifact",
        started_at=TS, finished_at=TS, stages=stages,
        feasibility=Feasibility(outcome=outcome, stage_status={s.stage.value: s.status for s in stages},
                                first_failure_stage=first_bad.stage if first_bad else None,
                                failure_type=first_bad.failure_type if first_bad else None),
        quality=gt, conditional_quality=cond,
        efficiency=WorkflowEfficiency(end_to_end_ms=e2e, total_api_latency_ms=api, input_tokens=tin,
                                      output_tokens=tout, n_calls=len(models), n_switches=n_switches(path)),
        propagation=prop)


def base_runs(exp=EXP_B) -> list[WorkflowRunRecord]:
    c = {"cleaning": {"cleaning_correctness": 1.0}}
    def q(na):
        return c | {"analysis": {"numerical_accuracy": na}}
    rep = {"reporting": {"numerical_consistency": 1.0, "finding_coverage": 1.0, "unsupported_claim_count": 0.0}}
    return [
        # 2-stage group
        run("aa0", "A-A", ["passed", "passed"], q(0.9), e2e=1000, api=600, tin=100, tout=50, exp=exp),
        run("aa1", "A-A", ["passed", "passed"], q(0.7), e2e=1400, api=700, tin=120, tout=60, repeat=1, exp=exp),
        run("ab0", "A-B", ["passed", "failed"], q(0.5), {"analysis": {"numerical_accuracy": 0.8}}, e2e=900, exp=exp),
        run("ab1", "A-B", ["infra", "not_run"], {}, e2e=50, api=0, tin=0, tout=0, exp=exp),
        run("ba0", "B-A", ["passed", "passed"], q(0.95), e2e=2000, api=1500, tin=300, tout=100, exp=exp),
        run("bb0", "B-B", ["passed", "passed"], q(0.8), e2e=2500, api=2000, tin=350, tout=150, exp=exp),
        # 3-stage group (reporting validator-version tests)
        run("aaa0", "A-A-A", ["passed", "passed", "passed"], q(1.0) | rep, exp=exp),
        run("aab0", "A-A-B", ["passed", "passed", "failed"], q(1.0) | {"reporting": dict(
            rep["reporting"], numerical_consistency=0.5)}, exp=exp),
        run("bbb0", "B-B-B", ["infra", "not_run", "not_run"], {}, exp=exp),
    ]


def stage_record(run_id: str, model: str, na: float, exp=EXP_A, project=PROJECT) -> StageBenchmarkRecord:
    rec = StageRunRecord(stage=STAGES[1], model_alias=model, model_id=f"{MARK}-{model}", prompt_version="v2",
                         invocation_ids=[run_id], status=StageStatus.PASSED, structural_ok=True,
                         validation=_val("analysis", True, {"numerical_accuracy": na}))
    return StageBenchmarkRecord(run_id=f"{MARK}-{run_id}", experiment_id=exp, project_id=project, stage=STAGES[1],
                                model_alias=model, canonical_inputs=["canonical/cleaned.csv"], config_hash="0" * 64,
                                record=rec)


def write_jsonl(path: Path, records) -> Path:
    path.write_text("".join(json.dumps(r.model_dump(mode="json"), sort_keys=True) + "\n" for r in records))
    return path


def rescore(path: Path, records_sha256: str, aab_v2_pass: bool = False) -> Path:
    """A v3-style rescore file for run aab0 (shape of results/processed/pilot_v3_rescore/*.json)."""
    q = {"numerical_consistency": 1.0, "finding_coverage": 1.0, "unsupported_claim_count": 0.0}
    d = {"mode": "offline_saved_output_rescore", "project_id": PROJECT, "source_records_sha256": records_sha256,
         "records": [{"run_id": f"{MARK}-aab0", "path_id": "A-A-B",
                      "v2_ground_truth": {"stage": "reporting", "hard_pass": aab_v2_pass, "checks": [],
                                          "quality": dict(q, numerical_consistency=0.5),
                                          "quality_basis": "ground_truth", "validator_version": "2.0"},
                      "v3_ground_truth": {"stage": "reporting", "hard_pass": True, "checks": [], "quality": q,
                                          "quality_basis": "ground_truth",
                                          "validator_version": "3.0-post-freeze"}}]}
    path.write_text(json.dumps(d))
    return path
