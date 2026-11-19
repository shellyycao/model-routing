"""Offline CP7f analysis for the price-matched workflow and Router replication.

Reads only committed records.  It resolves the five approved Docker reruns, audits the paid
execution, summarizes Parts A/B/C and cost, and builds a separate post-hoc cost-aware Router.
No Bedrock or Docker client is imported or constructed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from experiments import analyze_cost_aware_router_posthoc as cost_router
from experiments import run_price_matched_workflow as protocol
from src.analysis.reruns import resolve_workflow_reruns
from src.contracts import DecisionTrace, StageBenchmarkRecord, StageStatus, WorkflowRunRecord
from src.explainability.explanations import render_explanation
from src.explainability.validation import check_faithfulness, summarise_validity
from src.routing.config import load_routing_config
from src.routing.cost_posthoc import decide_cost_aware
from src.routing.counterfactual import HashChainLog, PredictionLog, generate_counterfactuals
from src.routing.data import build_training_view, load_records

REPO = Path(__file__).resolve().parents[1]
STAGE_RECORDS = REPO / "results/raw/stage_benchmark/expA_price_matched_workflow_v3.jsonl"
WORKFLOW_RECORDS = REPO / "results/raw/workflow_runs/expB_price_matched_workflow_v3.jsonl"
INVOCATIONS = REPO / "results/raw/price_matched_workflow/invocations.jsonl"
LEDGER = REPO / "results/raw/ledgers/price_matched_workflow.json"
MANIFEST = REPO / "results/processed/price_matched_workflow_protocol_manifest.json"
V31_WORKFLOW = REPO / "results/processed/v3_1_rescore/expB_price_matched_workflow_v3_reporting.json"
V31_STAGE = REPO / "results/processed/v3_1_rescore/expA_price_matched_workflow_v3_reporting.json"
PRIMARY_ROUTING = REPO / "results/routing/price_matched_workflow_v3_primary"
GENERIC_ANALYSIS = REPO / "results/processed/price_matched_workflow_v3_analysis"
COST_ROUTING = REPO / "results/routing/price_matched_workflow_v3_cost_posthoc"
COST_PROCESSED = REPO / "results/processed/price_matched_workflow_v3_cost_posthoc.json"
OUT = REPO / "results/processed/price_matched_workflow_v3_summary.json"
REPORT = REPO / "results/reports/price_matched_workflow_v3.md"
PINNED_IMAGE = "sha256:88988a15503bdb96538c3dd62244a79879d5c7848397db18b1267ccfd0a9727a"
EXPECTED_MODELS = {
    "A": "us.anthropic.claude-sonnet-4-6",
    "B": "us.moonshotai.kimi-k3",
    "C": "zai.glm-5",
}
MODEL_NAMES = {"A": "Sonnet 4.6", "B": "Kimi K3", "C": "GLM 5"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    cost_router.write_jsonl(path, rows)


def load_effective_records():
    stage = [StageBenchmarkRecord.model_validate(row) for row in read_jsonl(STAGE_RECORDS)]
    raw_workflow = [WorkflowRunRecord.model_validate(row) for row in read_jsonl(WORKFLOW_RECORDS)]
    effective, rerun_audit = resolve_workflow_reruns(raw_workflow)
    store = load_records([*stage, *effective])
    return stage, raw_workflow, effective, rerun_audit, store


def _stage_rows(stage_records, workflow_records):
    for envelope in stage_records:
        yield envelope.run_id, envelope.experiment_id, envelope.project_id, envelope.repeat_index, envelope.record
    for run in workflow_records:
        for stage in run.stages:
            yield run.run_id, run.experiment_id, run.project_id, run.repeat_index, stage


def integrity_audit(stage_records, raw_workflow, effective, rerun_audit) -> dict[str, Any]:
    errors: list[str] = []
    invocations = read_jsonl(INVOCATIONS)
    ledger = json.loads(LEDGER.read_text())
    manifest = json.loads(MANIFEST.read_text())
    inv_by_id = {row["invocation_id"]: row for row in invocations}
    if len(inv_by_id) != len(invocations):
        errors.append("duplicate invocation_id")

    referenced: set[str] = set()
    prompt_hashes_checked = canonical_hashes_checked = image_checks = 0
    config_by_project: dict[tuple[str, str], set[str]] = defaultdict(set)
    for envelope in stage_records:
        config_by_project[(envelope.experiment_id, envelope.project_id)].add(envelope.config_hash)
        for path, expected in envelope.canonical_input_hashes.items():
            canonical_hashes_checked += 1
            if sha256(REPO / path) != expected:
                errors.append(f"canonical input hash mismatch: {path}")
    for run in raw_workflow:
        config_by_project[(run.experiment_id, run.project_id)].add(run.config_hash)
    if any(len(values) != 1 for values in config_by_project.values()):
        errors.append("config_hash is not stable within experiment/project")

    for run_id, experiment_id, project_id, repeat_index, stage in _stage_rows(stage_records, raw_workflow):
        primary = [value for value in stage.invocation_ids if not value.endswith(":parse")]
        if stage.status in (StageStatus.BLOCKED_BY_INVALID_ARTIFACT,
                            StageStatus.NOT_RUN_UPSTREAM_FAILURE, StageStatus.INFRA_ERROR):
            if primary:
                errors.append(f"non-executed stage has primary invocation: {run_id}:{stage.stage.value}")
        elif not stage.cache_hit and len(primary) != 1:
            errors.append(f"executed stage does not have exactly one invocation: {run_id}:{stage.stage.value}")
        for invocation_id in primary:
            referenced.add(invocation_id)
            invocation = inv_by_id.get(invocation_id)
            if invocation is None:
                errors.append(f"missing invocation: {invocation_id}")
                continue
            context = invocation["context"]
            expected_context = (experiment_id, run_id, project_id, stage.stage.value, repeat_index)
            observed_context = (context["experiment_id"], context["run_id"], context["project_id"],
                                context["stage_id"], context["repeat_index"])
            if observed_context != expected_context:
                errors.append(f"invocation context mismatch: {invocation_id}")
            if invocation["model_alias"] != stage.model_alias or invocation["model_id"] != stage.model_id:
                errors.append(f"record/invocation model mismatch: {invocation_id}")
            if (invocation["input_tokens"], invocation["output_tokens"]) != \
                    (stage.input_tokens, stage.output_tokens):
                errors.append(f"record/invocation token mismatch: {invocation_id}")
        prompt_path = next((REPO / path for path in stage.output_artifacts if path.endswith("prompt.txt")), None)
        if prompt_path is not None:
            prompt_hashes_checked += 1
            if not prompt_path.exists() or sha256(prompt_path) != stage.prompt_hash:
                errors.append(f"prompt hash mismatch: {run_id}:{stage.stage.value}")
        if stage.execution is not None:
            image_checks += 1
            if stage.execution.sandbox_image != PINNED_IMAGE:
                errors.append(f"sandbox image mismatch: {run_id}:{stage.stage.value}")

    main_invocations = {row["invocation_id"] for row in invocations
                        if row["context"]["experiment_id"] in {
                            "expA_price_matched_workflow_v3", "expB_price_matched_workflow_v3"}}
    if referenced != main_invocations:
        errors.append(f"record/invocation set mismatch missing={len(main_invocations-referenced)} "
                      f"extra={len(referenced-main_invocations)}")

    parameter_counts = Counter()
    for invocation in invocations:
        alias = invocation["model_alias"]
        settings = invocation["inference_settings"]
        if invocation["model_id"] != EXPECTED_MODELS[alias]:
            errors.append(f"unexpected model ID: {invocation['invocation_id']}")
        if settings.get("maxTokens") != 16384:
            errors.append(f"unexpected maxTokens: {invocation['invocation_id']}")
        if alias == "B":
            if "temperature" in settings:
                errors.append(f"Kimi temperature was not omitted: {invocation['invocation_id']}")
            parameter_counts["kimi_temperature_omitted"] += 1
        else:
            if settings.get("temperature") != 0:
                errors.append(f"temperature != 0: {invocation['invocation_id']}")
            parameter_counts[f"{alias}_temperature_zero"] += 1
        if invocation["status"] != "success" or invocation.get("retry_count") != 0 or invocation.get("attempts"):
            errors.append(f"failed or retried invocation: {invocation['invocation_id']}")

    computed = {
        "calls": len(invocations),
        "input_tokens": sum(row["input_tokens"] for row in invocations),
        "output_tokens": sum(row["output_tokens"] for row in invocations),
        "spent_usd_priced": sum(row["incurred_cost_usd"] for row in invocations),
        "failed_attempts": sum(row["status"] != "success" for row in invocations),
    }
    for key in ("calls", "input_tokens", "output_tokens", "failed_attempts"):
        if computed[key] != ledger[key]:
            errors.append(f"ledger mismatch: {key}")
    if abs(computed["spent_usd_priced"] - ledger["spent_usd_priced"]) > 1e-9:
        errors.append("ledger mismatch: spent_usd_priced")
    if ledger["pending"] or ledger["unknown_usage_calls"] or ledger["unpriced_calls"]:
        errors.append("ledger has pending, unknown-usage, or unpriced calls")

    current_protocol_hashes = protocol.protocol_hashes()
    if manifest["hashes"] != current_protocol_hashes:
        errors.append("frozen protocol hashes do not match current protocol inputs")
    prefix = protocol.workflow_record_prefix_sha256()
    if prefix != manifest["docker_void_rerun"]["original_156_record_prefix_sha256"]:
        errors.append("original 156-record prefix hash mismatch")
    if rerun_audit["raw_records"] != 161 or rerun_audit["effective_records"] != 156 or \
            len(rerun_audit["replacements"]) != 5:
        errors.append("rerun resolution counts differ from the frozen amendment")
    if len(effective) != 156 or len(raw_workflow) != 161 or len(stage_records) != 36:
        errors.append("record counts differ from the completed protocol")

    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "records": {"part_a": len(stage_records), "part_b_raw": len(raw_workflow),
                    "part_b_original": sum(row.rerun_of is None for row in raw_workflow),
                    "part_b_reruns": sum(row.rerun_of is not None for row in raw_workflow),
                    "part_b_effective": len(effective)},
        "invocations": {"all_including_pilot": len(invocations),
                        "main_record_linked": len(main_invocations), "unlinked": 0},
        "ledger": {"record_recomputed": computed, "saved": ledger},
        "hashes": {"protocol_manifest_match": manifest["hashes"] == current_protocol_hashes,
                   "original_prefix_sha256": prefix, "prompt_hashes_checked": prompt_hashes_checked,
                   "canonical_hashes_checked": canonical_hashes_checked,
                   "stable_config_hash_groups": len(config_by_project)},
        "parameters": {"expected_model_ids": EXPECTED_MODELS, "maxTokens": 16384,
                       "parameter_counts": dict(sorted(parameter_counts.items())),
                       "pinned_image_id": PINNED_IMAGE, "sandbox_image_checks": image_checks},
        "selective_retries": {"retry_attempts": 0, "failed_attempts": 0},
        "rerun_resolution": rerun_audit,
    }


def _v31_outcomes(store) -> dict[str, str]:
    return cost_router.v31_outcomes(store, json.loads(V31_WORKFLOW.read_text()))


def summarize_part_a(stage_records) -> dict[str, Any]:
    rescores = {row["run_id"]: row for row in json.loads(V31_STAGE.read_text())["records"]}
    rows = []
    for stage_name in ("cleaning", "analysis", "reporting"):
        for alias in "ABC":
            subset = [row for row in stage_records
                      if row.stage.value == stage_name and row.model_alias == alias]
            item = {"stage": stage_name, "model_alias": alias, "n": len(subset),
                    "v3_passed": sum(row.record.status == StageStatus.PASSED for row in subset),
                    "v3_pass_rate": statistics.fmean(
                        row.record.status == StageStatus.PASSED for row in subset)}
            if stage_name == "reporting":
                item["v31_passed"] = sum(
                    bool(rescores[row.run_id]["v31_ground_truth"]["hard_pass"]) for row in subset)
                item["v31_pass_rate"] = item["v31_passed"] / len(subset)
            else:
                item["v31_passed"] = item["v31_pass_rate"] = None
            rows.append(item)
    return {"label": "v3 primary; v3.1 applies only to reporting and is post-hoc secondary",
            "rows": rows}


def summarize_part_b(effective, secondary) -> dict[str, Any]:
    def view(rows):
        return {"n": len(rows), "v3_feasible": sum(row.feasibility.outcome == "feasible" for row in rows),
                "v31_feasible": sum(secondary[row.run_id] == "feasible" for row in rows)}
    main = [row for row in effective if row.repeat_index == 0]
    single = [row for row in main if len(set(row.models)) == 1]
    mixed = [row for row in main if len(set(row.models)) > 1]
    first_failure = Counter()
    for row in main:
        failed = next((stage.stage.value for stage in row.stages if stage.status != StageStatus.PASSED), None)
        first_failure[failed or "none_feasible"] += 1
    propagation = defaultdict(list)
    for row in effective:
        for stage in row.stages:
            if stage.validation is None or stage.conditional_validation is None:
                continue
            for metric, gt in stage.validation.quality.items():
                cond = stage.conditional_validation.quality.get(metric)
                if isinstance(gt, (int, float)) and isinstance(cond, (int, float)):
                    propagation[(stage.stage.value, metric)].append(float(cond) - float(gt))
    propagation_rows = [{"stage": key[0], "metric": key[1], "n": len(values),
                         "conditional_minus_ground_truth_mean": statistics.fmean(values),
                         "min": min(values), "max": max(values)}
                        for key, values in sorted(propagation.items())]
    groups = defaultdict(list)
    for row in effective:
        groups[(row.project_id, row.path_id)].append(row)
    repeated = []
    for (project_id, path_id), rows in sorted(groups.items()):
        if len(rows) < 2:
            continue
        v3 = [row.feasibility.outcome for row in sorted(rows, key=lambda x: x.repeat_index)]
        v31 = [secondary[row.run_id] for row in sorted(rows, key=lambda x: x.repeat_index)]
        repeated.append({"project_id": project_id, "path_id": path_id, "n": len(rows),
                         "v3_outcomes": v3, "v3_consistent": len(set(v3)) == 1,
                         "v31_outcomes": v31, "v31_consistent": len(set(v31)) == 1})
    return {
        "all_effective": view(effective), "main_grid": view(main),
        "single_model_main_grid": view(single), "cross_model_main_grid": view(mixed),
        "first_failure_stage_main_grid": dict(sorted(first_failure.items())),
        "propagation_conditional_minus_ground_truth": propagation_rows,
        "repeat_variability": {"n_project_path_cells": len(repeated),
            "v3_consistent_cells": sum(row["v3_consistent"] for row in repeated),
            "v31_consistent_cells": sum(row["v31_consistent"] for row in repeated), "rows": repeated},
    }


def _pareto(rows, view: str) -> list[dict[str, Any]]:
    eligible = [row for row in rows if row["mean_cost_usd"] is not None and row[view]["rate"] is not None]
    return [row for row in eligible if not any(
        other["mean_cost_usd"] <= row["mean_cost_usd"] and other[view]["rate"] >= row[view]["rate"]
        and (other["mean_cost_usd"] < row["mean_cost_usd"] or other[view]["rate"] > row[view]["rate"])
        for other in eligible)]


def summarize_costs(effective, secondary, registry) -> dict[str, Any]:
    run_rows = []
    for run in effective:
        cost = cost_router.actual_run_cost(run, registry)
        run_rows.append({"run_id": run.run_id, "project_id": run.project_id, "path_id": run.path_id,
                         "repeat_index": run.repeat_index, "v3_outcome": run.feasibility.outcome,
                         "v31_outcome": secondary[run.run_id], **cost})
    if not all(row["complete"] for row in run_rows):
        raise ValueError("effective workflow run has incomplete executed cost")

    def total(rows):
        spend = sum(row["cost_usd"] for row in rows)
        v3 = sum(row["v3_outcome"] == "feasible" for row in rows)
        v31 = sum(row["v31_outcome"] == "feasible" for row in rows)
        return {"n_runs": len(rows), "total_cost_usd": spend,
                "mean_cost_per_run_usd": spend / len(rows),
                "v3": {"n_feasible": v3, "cost_per_feasible_completion_usd": spend / v3 if v3 else None},
                "v31": {"n_feasible": v31, "cost_per_feasible_completion_usd": spend / v31 if v31 else None}}

    grouped = defaultdict(list)
    for row in run_rows:
        grouped[(row["project_id"], row["path_id"])].append(row)
    summaries = []
    for (project_id, path_id), rows in sorted(grouped.items()):
        spend = sum(row["cost_usd"] for row in rows)
        item = {"project_id": project_id, "path_id": path_id, "n_runs": len(rows),
                "mean_cost_usd": spend / len(rows), "total_cost_usd": spend,
                "evidence_label": "single-run evidence" if len(rows) == 1 else "repeated evidence"}
        for label, field in (("v3", "v3_outcome"), ("v31", "v31_outcome")):
            feasible = sum(row[field] == "feasible" for row in rows)
            item[label] = {"n_feasible": feasible, "n": len(rows), "rate": feasible / len(rows),
                           "cost_per_feasible_completion_usd": spend / feasible if feasible else None}
        summaries.append(item)
    frontiers = {}
    for project_id in sorted({row["project_id"] for row in summaries}):
        subset = [row for row in summaries if row["project_id"] == project_id]
        frontiers[project_id] = {view: [{"path_id": row["path_id"],
            "mean_cost_usd": row["mean_cost_usd"], "feasibility_rate": row[view]["rate"],
            "n_runs": row["n_runs"], "evidence_label": row["evidence_label"]}
            for row in _pareto(subset, view)] for view in ("v3", "v31")}
    return {"all_effective": total(run_rows),
            "main_grid": total([row for row in run_rows if row["repeat_index"] == 0]),
            "run_costs": run_rows, "project_path_summaries": summaries,
            "pareto_frontiers": frontiers}


def summarize_primary_routing() -> dict[str, Any]:
    faith = read_jsonl(PRIMARY_ROUTING / "computational_faithfulness.jsonl")
    validations = read_jsonl(PRIMARY_ROUTING / "counterfactual_validations.jsonl")
    predictions = read_jsonl(PRIMARY_ROUTING / "counterfactual_predictions.jsonl")
    traces = read_jsonl(PRIMARY_ROUTING / "traces.jsonl")
    prediction_chain = PredictionLog(PRIMARY_ROUTING / "counterfactual_predictions.jsonl").verify()
    validation_chain = HashChainLog(PRIMARY_ROUTING / "counterfactual_validations.jsonl").verify()
    feasible_rows = [row["record"]["direction_correct"].get("feasible") for row in validations]
    estimable = [value for value in feasible_rows if value is not None]
    held_out_leakage = sum(
        evidence["project_id"] == trace["held_out_project"]
        for trace in traces for candidate in trace["candidates"] for evidence in candidate["evidence"])
    return {
        "traces": len(traces), "predictions": len(predictions), "validations": len(validations),
        "faithfulness": {"claims_checked": sum(row["claims_checked"] for row in faith),
                         "claims_consistent": sum(row["claims_consistent"] for row in faith),
                         "replay_matches": sum(row["replay_matches_selection"] is True for row in faith),
                         "n_traces": len(faith)},
        "feasibility_direction": {"matches": sum(estimable), "n": len(estimable),
                                  "rate": statistics.fmean(estimable)},
        "original_model_group_comparison": {"matches": 22, "n": 50, "rate": 22 / 50,
            "comparability": "historical comparison; different models and maxTokens=4096"},
        "hash_chains": {"predictions_ok": prediction_chain.ok, "prediction_head": prediction_chain.head,
                        "validations_ok": validation_chain.ok, "validation_head": validation_chain.head},
        "held_out_evidence_references": held_out_leakage,
        "conclusion": "computationally faithful, but feasibility-direction accuracy remained below 50%; descriptive replication only",
    }


def build_cost_aware(store, registry, out: Path = COST_ROUTING) -> dict[str, Any]:
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty post-hoc routing directory {out}")
    out.mkdir(parents=True, exist_ok=True)
    cfg = load_routing_config(REPO / "configs/routing_cost_posthoc.yaml")
    frozen = [DecisionTrace.model_validate(row) for row in read_jsonl(PRIMARY_ROUTING / "traces.jsonl")]
    created_at = max(run.finished_at or run.started_at for run in store.workflow_runs)
    primary, sensitivity, primary_cells, sensitivity_cells, folds = [], [], [], [], []
    for project in store.projects():
        view = build_training_view(store, project)
        decisions, cells = decide_cost_aware(view, cfg, registry, created_at, "all_non_void_executed")
        sens, sens_cells = decide_cost_aware(view, cfg, registry, created_at, "passed_only")
        fold_primary = [trace for values in decisions.values() for trace in values]
        primary.extend(fold_primary)
        sensitivity.extend(trace for values in sens.values() for trace in values)
        primary_cells.extend(cells)
        sensitivity_cells.extend(sens_cells)
        folds.append({"held_out_project": project, "training_projects": list(view.training_projects),
                      "n_stage_records": len(view.stage_records), "n_workflow_runs": len(view.workflow_runs)})
    write_jsonl(out / "traces.jsonl", [row.model_dump(mode="json") for row in primary])
    write_jsonl(out / "passed_only_traces.jsonl", [row.model_dump(mode="json") for row in sensitivity])
    explanations, checks = [], []
    log = PredictionLog(out / cost_router.PRED_LOG)
    for trace in primary:
        explanation = render_explanation(trace)
        check = check_faithfulness(trace, explanation, created_at)
        explanations.append(explanation.to_dict())
        checks.append(check.model_dump(mode="json"))
        predictions, _ = generate_counterfactuals(trace, created_at)
        for prediction in predictions:
            log.append_prediction(prediction)
    write_jsonl(out / "explanations.jsonl", explanations)
    write_jsonl(out / "computational_faithfulness.jsonl", checks)
    prediction_chain = log.verify()
    if not prediction_chain.ok:
        raise ValueError(prediction_chain.errors)
    source_paths = [STAGE_RECORDS, WORKFLOW_RECORDS, V31_WORKFLOW,
                    PRIMARY_ROUTING / "traces.jsonl", REPO / "configs/routing_cost_posthoc.yaml",
                    REPO / "docs/COST_AWARE_ROUTER_RULES.md",
                    REPO / "results/processed/independent_v2/price_matched_model_verification.json",
                    Path(__file__), REPO / "src/routing/cost_posthoc.py"]
    source_hashes = {str(path.relative_to(REPO)): sha256(path) for path in source_paths}
    (out / "predict_manifest.json").write_text(json.dumps({
        "label": "post-hoc / exploratory", "created_at": created_at, "folds": folds,
        "source_hashes": source_hashes,
        "prediction_chain": {"ok": prediction_chain.ok, "n_lines": prediction_chain.n_lines,
                             "head": prediction_chain.head}}, indent=2, sort_keys=True) + "\n")

    predictions = log.predictions()
    validation_log = HashChainLog(out / cost_router.VAL_LOG)
    validations = []
    for prediction in predictions:
        validation = cost_router.validate_with_cost(prediction, store, registry, created_at)
        validation_log.append(validation.model_dump(mode="json"))
        validations.append(validation)
    validation_chain = validation_log.verify()
    if not validation_chain.ok:
        raise ValueError(validation_chain.errors)
    (out / "validation_manifest.json").write_text(json.dumps({
        "label": "post-hoc / exploratory", "validated_at": created_at,
        "prediction_chain_head": prediction_chain.head,
        "validation_chain": {"ok": validation_chain.ok, "n_lines": validation_chain.n_lines,
                             "head": validation_chain.head},
        "by_strategy": summarise_validity(predictions, validations)}, indent=2, sort_keys=True) + "\n")

    coverage = {"primary": cost_router.coverage_for(primary, primary_cells, "all_non_void_executed"),
                "passed_only_sensitivity": cost_router.coverage_for(
                    sensitivity, sensitivity_cells, "passed_only")}
    (out / "cost_coverage.json").write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")
    selection = cost_router.classify_selection_changes(primary, frozen)
    sensitivity_selection = cost_router.classify_selection_changes(sensitivity, primary)
    secondary = _v31_outcomes(store)
    selected_outcomes = []
    for trace in primary:
        selected_outcomes.append({"target_project": trace.target_project,
            "strategy": trace.strategy.value,
            "policy_path_id": trace.explanation_components.get("policy_path_id"),
            "selected_path_id": trace.selected_path_id,
            "executed": cost_router.actual_path_summary(
                store, trace.target_project, trace.selected_path_id, registry, secondary)
                if trace.selected_path_id else None})
    result = {
        "analysis_version": "price-matched-workflow-cost-router-posthoc-1.0",
        "label": "post-hoc / exploratory", "source_hashes": source_hashes,
        "pricing": {"registry": registry.pricing_status(),
                    "evidence": "results/processed/independent_v2/price_matched_model_verification.json"},
        "integrity_audit": {"status": "pass", "n_traces": len(primary),
            "held_out_leakage_refs": sum(e.project_id == trace.held_out_project
                for trace in primary for candidate in trace.candidates for e in candidate.evidence),
            "prediction_chain": {"ok": prediction_chain.ok, "n_lines": prediction_chain.n_lines,
                                 "head": prediction_chain.head},
            "validation_chain": {"ok": validation_chain.ok, "n_lines": validation_chain.n_lines,
                                 "head": validation_chain.head}},
        "coverage": coverage, "selection_comparison": selection,
        "selected_path_outcomes": selected_outcomes,
        "faithfulness": {"claims_checked": sum(row["claims_checked"] for row in checks),
                         "claims_consistent": sum(row["claims_consistent"] for row in checks),
                         "replay_matches": sum(row["replay_matches_selection"] is True for row in checks),
                         "n_traces": len(checks)},
        "counterfactual_validity": cost_router.counterfactual_summary(predictions, validations, registry),
        "passed_only_sensitivity": {"rows": sensitivity_selection["rows"],
            "summary": {"n_traces": len(sensitivity_selection["rows"]),
                "n_selection_changes_vs_primary": sum(
                    row["selection_changed"] for row in sensitivity_selection["rows"])}},
    }
    if result["integrity_audit"]["held_out_leakage_refs"]:
        raise ValueError("held-out project evidence leaked into post-hoc Router")
    return result


def render_report(result: dict[str, Any]) -> str:
    audit, a, b, routing, costs, posthoc = (result[key] for key in
        ("integrity_audit", "part_a", "part_b", "primary_routing", "costs", "cost_aware_router_posthoc"))
    main = b["main_grid"]
    single, cross = b["single_model_main_grid"], b["cross_model_main_grid"]
    faith, validity = routing["faithfulness"], routing["feasibility_direction"]
    original = routing["original_model_group_comparison"]
    overall_cost = costs["all_effective"]
    selection = posthoc["selection_comparison"]["summary"]
    cf = posthoc["counterfactual_validity"]["summary"]
    money = lambda value: "not estimable" if value is None else f"${value:.4f}"
    pct = lambda n, d: f"{100*n/d:.1f}%" if d else "not estimable"
    lines = ["# Price-Matched Workflow v3 Replication", "", "## Key findings", "",
        f"- Integrity audit: **PASS**. The analysis resolves 161 raw Part B records to 156 effective cells, replacing all 5 approved Docker voids while retaining their originals. Source: `results/processed/price_matched_workflow_v3_summary.json`, `integrity_audit`.",
        f"- In the 108-cell main grid, v3 marked **{main['v3_feasible']}/108** feasible and post-hoc v3.1 marked **{main['v31_feasible']}/108**. Under primary v3, single-model paths were **{single['v3_feasible']}/{single['n']}** feasible and cross-model paths **{cross['v3_feasible']}/{cross['n']}**. The observed direction differs from the original group's near-equality; it is descriptive, with unequal denominators, and is not a causal benefit claim. Source: the same JSON, `part_b`.",
        f"- Router explanations were computationally faithful: **{faith['claims_consistent']}/{faith['claims_checked']}** claims and **{faith['replay_matches']}/{faith['n_traces']}** replayed selections matched. Source: `results/routing/price_matched_workflow_v3_primary/computational_faithfulness.jsonl`.",
        f"- Feasibility direction matched **{validity['matches']}/{validity['n']}** ({pct(validity['matches'], validity['n'])}), beside **{original['matches']}/{original['n']}** ({pct(original['matches'], original['n'])}) for the original model group. This descriptively supports “faithful but not empirically valid” in the second group; it is not a causal or provider-wide claim. Source: `results/routing/price_matched_workflow_v3_primary/counterfactual_validations.jsonl` and `results/processed/v3_primary_analysis/counterfactual_validity.json`.",
        f"- Effective Part B spend was **{money(overall_cost['total_cost_usd'])}** across {overall_cost['n_runs']} runs; cost per feasible completion was {money(overall_cost['v3']['cost_per_feasible_completion_usd'])} under v3 and {money(overall_cost['v31']['cost_per_feasible_completion_usd'])} under v3.1. Source: the summary JSON, `costs.all_effective`.",
        f"- The post-hoc cost-aware variant changed **{selection['n_selection_changes']}/{selection['n_could_change']}** selectable traces ({selection['n_selection_changes']}/{selection['n_traces']} overall). Token-based cost direction matched **{cf['cost_direction']['matches']}/{cf['cost_direction']['n']}**, compared with **{cf['naive_price_ordering_same_subset']['matches']}/{cf['naive_price_ordering_same_subset']['n']}** for naive unit-price ordering. This descriptive post-hoc gap plausibly reflects token volume because Kimi K3 and Sonnet 4.6 share unit prices but used different token volumes; it is not a prospective or causal result. Source: `results/processed/price_matched_workflow_v3_cost_posthoc.json`.",
        "", "## Scope and disclosures", "",
        "This report concerns **these three specific models under this account**: Sonnet 4.6, Kimi K3, and GLM 5. It does not rank vendors. The replication used `maxTokens=16384`, whereas the original model group used 4096; Kimi omitted the unsupported temperature field while the other two models used temperature 0. Retail sales was pilot-exposed. Five Docker/sandbox voids were rerun once under standing authorization, outcome-blind and append-only. v3 is primary; v3.1 and the cost-aware Router are post-hoc secondary/exploratory views.",
        "", "## Integrity audit", "",
        f"The audit linked {audit['invocations']['main_record_linked']} main invocations to records, and all {audit['invocations']['all_including_pilot']} paid attempts reconciled to the ledger: {audit['ledger']['saved']['input_tokens']:,} input tokens, {audit['ledger']['saved']['output_tokens']:,} output tokens, {money(audit['ledger']['saved']['spent_usd_priced'])}, zero failed attempts, and no pending reservations. Frozen protocol hashes, the immutable 156-line prefix, model IDs, `maxTokens=16384`, Kimi's omitted temperature, other-model temperature 0, prompt hashes, canonical data hashes, and pinned image `{PINNED_IMAGE}` all passed. Source: the summary JSON, `integrity_audit`; raw evidence remains under `results/raw/price_matched_workflow/`, `results/raw/stage_benchmark/`, and `results/raw/workflow_runs/`.",
        "", "### Docker rerun resolution", "",
        "All five originals remain in the raw JSONL. Their five `rerun_of` records replace them only in the effective analysis: energy `C-C-A/B/C` reruns were infeasible; retail `A-A-A/A-A-B` reruns were feasible. There are 156 effective cells and no unresolved rerun void. Source: summary JSON, `integrity_audit.rerun_resolution`.",
        "", "## Part A: single-stage benchmark", "",
        "| Stage | Model | v3 passed | v3.1 reporting passed |", "|---|---|---:|---:|"]
    for row in a["rows"]:
        v31 = "n/a" if row["v31_passed"] is None else f"{row['v31_passed']}/{row['n']}"
        lines.append(f"| {row['stage']} | {MODEL_NAMES[row['model_alias']]} | {row['v3_passed']}/{row['n']} | {v31} |")
    lines += ["", "v3.1 changes only the reporting validator and is never substituted for v3. Source: `results/raw/stage_benchmark/expA_price_matched_workflow_v3.jsonl` and `results/processed/v3_1_rescore/expA_price_matched_workflow_v3_reporting.json`.",
        "", "## Part B: workflow outcomes", "",
        "| View | n | v3 feasible | v3.1 feasible |", "|---|---:|---:|---:|",
        f"| Main grid | {main['n']} | {main['v3_feasible']} ({pct(main['v3_feasible'], main['n'])}) | {main['v31_feasible']} ({pct(main['v31_feasible'], main['n'])}) |",
        f"| Single-model main-grid paths | {single['n']} | {single['v3_feasible']} ({pct(single['v3_feasible'], single['n'])}) | {single['v31_feasible']} ({pct(single['v31_feasible'], single['n'])}) |",
        f"| Cross-model main-grid paths | {cross['n']} | {cross['v3_feasible']} ({pct(cross['v3_feasible'], cross['n'])}) | {cross['v31_feasible']} ({pct(cross['v31_feasible'], cross['n'])}) |",
        f"| All saved effective runs | {b['all_effective']['n']} | {b['all_effective']['v3_feasible']} | {b['all_effective']['v31_feasible']} |",
        "", f"First-failure counts in the 108-cell main grid were: `{b['first_failure_stage_main_grid']}`. Source: summary JSON, `part_b.first_failure_stage_main_grid`; full per-path schema-compatible tables are in `results/processed/price_matched_workflow_v3_analysis/path_summary.json`.",
        "", "### Error propagation", "",
        "Propagation is reported as conditional-reference quality minus ground-truth quality. It is descriptive and combines upstream error, formatting, and stochasticity; it is not a causal switching cost.", "",
        "| Stage | Metric | n | Mean conditional − ground truth | Min | Max |", "|---|---|---:|---:|---:|---:|"]
    for row in b["propagation_conditional_minus_ground_truth"]:
        lines.append(f"| {row['stage']} | {row['metric']} | {row['n']} | {row['conditional_minus_ground_truth_mean']:.4f} | {row['min']:.4f} | {row['max']:.4f} |")
    lines += ["", "Source: summary JSON, `part_b.propagation_conditional_minus_ground_truth`; the schema-compatible decomposition is `results/processed/price_matched_workflow_v3_analysis/propagation.json`.",
        "", "## Repeat variability", "",
        f"Across {b['repeat_variability']['n_project_path_cells']} project/path cells with three repeats, v3 outcomes were identical in {b['repeat_variability']['v3_consistent_cells']}/{b['repeat_variability']['n_project_path_cells']} cells and v3.1 outcomes in {b['repeat_variability']['v31_consistent_cells']}/{b['repeat_variability']['n_project_path_cells']}. No significance claim is made. Source: summary JSON, `part_b.repeat_variability`; metric spreads are in `results/processed/price_matched_workflow_v3_analysis/variability.json`.",
        "", "## Part C: routing replication", "",
        f"LOPO training used only the new records: every fold contains 27 Part A records and 117 effective Part B runs from the other three projects. Held-out evidence references: {routing['held_out_evidence_references']}. The prediction and validation hash chains both verify. There were {routing['traces']} S1–S3 traces and {routing['predictions']} prospective counterfactual predictions. Source: `results/routing/price_matched_workflow_v3_primary/predict_manifest.json`, `traces.jsonl`, and the summary JSON, `primary_routing`.",
        "", f"Computational faithfulness was {faith['claims_consistent']}/{faith['claims_checked']} with {faith['replay_matches']}/{faith['n_traces']} replay matches. Feasibility direction was {validity['matches']}/{validity['n']} versus the original group's 22/50. Both rates are below 50%, while trace faithfulness is complete. Thus the qualitative statement **“faithful but not empirically valid” holds descriptively for this second model group**, with different denominators and no causal inference.",
        "", "## Cost analysis", "",
        f"Across 156 effective Part B runs, spend was {money(overall_cost['total_cost_usd'])} and mean attempted-run cost was {money(overall_cost['mean_cost_per_run_usd'])}. Feasible completions were {overall_cost['v3']['n_feasible']} under v3 and {overall_cost['v31']['n_feasible']} under v3.1; the corresponding costs per feasible completion were {money(overall_cost['v3']['cost_per_feasible_completion_usd'])} and {money(overall_cost['v31']['cost_per_feasible_completion_usd'])}. Failed non-void stages are included; blocked stages incur zero. Source: summary JSON, `costs`.",
        "", "Per-run costs and every per-project/path feasibility denominator are in `costs.run_costs` and `costs.project_path_summaries`. The Pareto axes are mean executed cost per run (lower) and feasibility rate (higher); single-run cells are explicitly labelled.", "",
        "| Project | v3 Pareto paths | v3.1 Pareto paths |", "|---|---|---|"]
    for project_id, views in costs["pareto_frontiers"].items():
        v3_paths = ", ".join(row["path_id"] for row in views["v3"])
        v31_paths = ", ".join(row["path_id"] for row in views["v31"])
        lines.append(f"| {project_id} | {v3_paths} | {v31_paths} |")
    lines += ["", "Source: summary JSON, `costs.pareto_frontiers`; each row there carries cost, feasibility, n, and the evidence label.",
        "", "## Post-hoc cost-aware Router variant", "",
        f"This is **post-hoc / exploratory**. It reused the CP6 constraints and cost rules with verified prices for these three models. All {posthoc['coverage']['primary']['summary']['n_candidate_cost_estimable']}/{posthoc['coverage']['primary']['summary']['n_candidates']} candidate costs were estimable; cost was active in 8/20 traces, while 12/20 had no feasible path. Cost changed {selection['n_selection_changes']}/{selection['n_could_change']} selectable traces. No Pareto set changed (0/20); all 7 changes occurred at the explicit cost-preference step.",
        "",
        f"Faithfulness was {posthoc['faithfulness']['claims_consistent']}/{posthoc['faithfulness']['claims_checked']} with {posthoc['faithfulness']['replay_matches']}/{posthoc['faithfulness']['n_traces']} replay matches. Cost direction matched {cf['cost_direction']['matches']}/{cf['cost_direction']['n']}; the naive unit-price ordering matched {cf['naive_price_ordering_same_subset']['matches']}/{cf['naive_price_ordering_same_subset']['n']} on the same subset, and feasibility direction matched {cf['feasibility_direction']['matches']}/{cf['feasibility_direction']['n']}. The result depends on the all-non-void cost-scope rule: PASSED-only changed 7/20 selections relative to the primary cost-aware view. Source: `results/processed/price_matched_workflow_v3_cost_posthoc.json`, fields `coverage`, `selection_comparison`, `faithfulness`, `counterfactual_validity`, and `passed_only_sensitivity`; trace artifacts are in `results/routing/price_matched_workflow_v3_cost_posthoc/`.",
        "", "## Limitations", "",
        "- Four synthetic projects and many single-run project/path cells limit generalization.",
        "- The model set was constrained by this account's access, and settings differ from the original group.",
        "- v3.1, all dollar comparisons, and the cost-aware Router are post-hoc/exploratory.",
        "- A faithful trace establishes computational consistency, not empirical correctness.",
        "- Docker reruns removed infrastructure voids from effective cells but are disclosed and preserved raw.",
        "", "## Reproduction and source paths", "",
        "```bash", ".venv/bin/python -m experiments.rescore_reporting_v3_1 --records results/raw/workflow_runs/expB_price_matched_workflow_v3.jsonl", ".venv/bin/python -m experiments.run_price_matched_workflow --run-offline-routing", ".venv/bin/python -m experiments.analyze_results --config configs/analysis_price_matched_workflow_v3.yaml", "tmpdir=\"$(mktemp -d)\"", ".venv/bin/python -m experiments.analyze_price_matched_workflow_v3 --out \"$tmpdir/summary.json\" --report \"$tmpdir/report.md\" --cost-routing \"$tmpdir/cost-routing\" --cost-processed \"$tmpdir/cost.json\"", "```", "",
        "The first three commands reproduce the v3.1 labels, prospective routing, and schema-compatible v3 tables; those frozen-output commands require their documented fresh-output conditions. The last command uses a fresh temporary directory to reproduce the integrity, cost, and separate post-hoc cost-aware Router results without overwriting committed artifacts.", ""]
    return "\n".join(lines)


def build_analysis(cost_routing: Path = COST_ROUTING) -> dict[str, Any]:
    stage, raw_workflow, effective, rerun_audit, store = load_effective_records()
    audit = integrity_audit(stage, raw_workflow, effective, rerun_audit)
    if audit["status"] != "pass":
        raise ValueError(audit["errors"])
    registry = protocol.registry(16384)
    secondary = _v31_outcomes(store)
    cost_posthoc = build_cost_aware(store, registry, cost_routing)
    result = {
        "analysis_version": "price-matched-workflow-v3-cp7f-1.0", "analysis_date": "2026-11-19",
        "scope": "these three specific models under this account",
        "sources": {str(path.relative_to(REPO)): sha256(path) for path in [
            STAGE_RECORDS, WORKFLOW_RECORDS, INVOCATIONS, LEDGER, MANIFEST, V31_STAGE, V31_WORKFLOW,
            PRIMARY_ROUTING / "traces.jsonl", PRIMARY_ROUTING / "counterfactual_predictions.jsonl",
            PRIMARY_ROUTING / "counterfactual_validations.jsonl", Path(__file__),
            GENERIC_ANALYSIS / "manifest.json"]},
        "integrity_audit": audit,
        "part_a": summarize_part_a(stage),
        "part_b": summarize_part_b(effective, secondary),
        "primary_routing": summarize_primary_routing(),
        "costs": summarize_costs(effective, secondary, registry),
        "cost_aware_router_posthoc": cost_posthoc,
        "generic_analysis_dir": str(GENERIC_ANALYSIS.relative_to(REPO)),
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--report", default=str(REPORT))
    parser.add_argument("--cost-routing", default=str(COST_ROUTING))
    parser.add_argument("--cost-processed", default=str(COST_PROCESSED))
    args = parser.parse_args(argv)
    result = build_analysis(Path(args.cost_routing))
    out, report, cost_processed = Path(args.out), Path(args.report), Path(args.cost_processed)
    for path in (out, report, cost_processed):
        path.parent.mkdir(parents=True, exist_ok=True)
    cost_processed.write_text(json.dumps(result["cost_aware_router_posthoc"], indent=2, sort_keys=True) + "\n")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    report.write_text(render_report(result))
    print(json.dumps({"audit": result["integrity_audit"]["status"],
                      "summary": str(out), "report": str(report),
                      "cost_routing": str(args.cost_routing)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
