"""Compute the additive post-hoc corrected Part B (Q2) view, entirely offline.

Frozen workflow records, continuation records, validators, costs, and router artifacts are read-only.
The output keeps frozen and corrected outcomes side by side and never retrains or revalidates a router.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from experiments.analyze_corrected_view import GROUPS, load_records
from src.bedrock.provenance import hash_file, hash_tree
from src.contracts import ProjectSpec, StageStatus
from src.evaluation.reporting_v3 import validate_reporting_v3
from src.evaluation.reporting_v3_1 import validate_reporting_v3_1


REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "docs/CORRECTED_VIEW_RULES.md"
PROTOCOL = REPO / "docs/CONTINUATION_PROTOCOL.md"
DIAGNOSTICS = REPO / "results/processed/diagnostics_posthoc.json"
Q1 = REPO / "results/processed/corrected_view.json"
CONTINUATIONS = REPO / "results/raw/workflow_continuations/continuation_v1.jsonl"
CONTINUATION_INVOCATIONS = REPO / "results/raw/continuations/invocations.jsonl"
CONTINUATION_LEDGER = REPO / "results/raw/ledgers/continuations.json"
ORIGINAL_COSTS = REPO / "results/processed/workflow_cost_posthoc.json"
PRICE_COSTS = REPO / "results/processed/price_matched_workflow_v3_summary.json"
OUT = REPO / "results/processed/corrected_q2.json"
REPORT = REPO / "results/reports/corrected_q2.md"

REPORT_NAMES = {
    "original_4096": {"A": "Sonnet 4.6", "B": "Nova Pro", "C": "gpt-oss-120b"},
    "price_matched_16384": {"A": "Sonnet 4.6", "B": "Kimi K3", "C": "GLM 5"},
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _status_outcome(statuses: list[str]) -> tuple[str, str]:
    first = next((value for value in statuses if value != "passed"), None)
    if first is None:
        return "feasible", "none_feasible"
    first_index = statuses.index(first)
    stage = ("cleaning", "analysis", "reporting")[first_index]
    return ("void_infra" if "infra_error" in statuses else "infeasible"), stage


def _v31_records(group: str) -> dict[str, dict[str, Any]]:
    path = GROUPS[group]["v31_b"]
    return {row["run_id"]: row for row in json.loads(path.read_text())["records"]}


def _rescore_continuation_reporting(row: dict[str, Any]) -> dict[str, Any] | None:
    stage = row["remaining_stages"][0]
    report_path = next((REPO / path for path in stage.get("output_artifacts", [])
                        if path.endswith("/report.json")), None)
    if report_path is None or not report_path.exists():
        return None
    project_dir = REPO / "datasets/projects" / row["project_id"]
    spec = ProjectSpec.model_validate_json((project_dir / "project.json").read_text())
    ground_truth = json.loads((project_dir / "ground_truth.json").read_text())
    report = json.loads(report_path.read_text())
    kwargs = {"cleaning_counts": ground_truth["cleaning"]["rule_log"], "quality_basis": "ground_truth"}
    v3 = validate_reporting_v3(report, ground_truth["analysis"]["metrics"], spec, **kwargs)
    stored = (stage.get("validation") or {}).get("hard_pass")
    if stored is not None and bool(stored) != bool(v3.hard_pass):
        raise ValueError(f"continuation v3 rescore disagrees with stored result: {row['run_id']}")
    v31 = validate_reporting_v3_1(report, ground_truth["analysis"]["metrics"], spec, **kwargs)
    return {"report_sha256": hash_file(report_path), "v3_pass": bool(v3.hard_pass),
            "v31_pass": bool(v31.hard_pass)}


def _cleaning_recoveries() -> set[tuple[str, str]]:
    diagnostics = json.loads(DIAGNOSTICS.read_text())
    rows = diagnostics["serialization_replay"]["records"]
    recovered = {(row["group"], row["run_id"]) for row in rows
                 if row["part"] == "B" and row["stage"] == "cleaning"
                 and row["would_pass_without_serialization_bug"]}
    if len(recovered) != 11:
        raise ValueError(f"expected 11 recovered Part B cleaning cells, got {len(recovered)}")
    return recovered


def _base_costs() -> dict[str, dict[str, float]]:
    original = json.loads(ORIGINAL_COSTS.read_text())["run_costs"]
    price = json.loads(PRICE_COSTS.read_text())["costs"]["run_costs"]
    rows = original + price
    if not all((row.get("cost_complete", row.get("complete"))) and row.get("cost_usd") is not None
               for row in rows):
        raise ValueError("base workflow costs are incomplete")
    result = {row["run_id"]: {"base_cost_usd": float(row["cost_usd"])} for row in rows}
    if len(result) != len(rows):
        raise ValueError("duplicate base run cost")
    return result


def _view(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    counts = Counter(row[field] for row in rows)
    nonvoid = len(rows) - counts["void_infra"]
    return {"n": len(rows), "n_nonvoid": nonvoid, "n_void": counts["void_infra"],
            "n_feasible": counts["feasible"],
            "feasibility_rate": counts["feasible"] / nonvoid if nonvoid else None}


def _outcome_views(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {field: _view(rows, field) for field in
            ("frozen_v3", "corrected_v3", "frozen_v31", "corrected_v31")}


def _cost_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    base = sum(row["base_cost_usd"] for row in rows)
    extra = sum(row["continuation_cost_usd"] for row in rows)
    augmented = base + extra
    result = {"n_runs": len(rows), "base_spend_usd": base,
              "continuation_spend_usd": extra, "corrected_total_spend_usd": augmented}
    for label, outcome, spend in (
        ("frozen_v3", "frozen_v3", base), ("corrected_v3", "corrected_v3", augmented),
        ("frozen_v31", "frozen_v31", base), ("corrected_v31", "corrected_v31", augmented),
    ):
        feasible = sum(row[outcome] == "feasible" for row in rows)
        result[label] = {"n_feasible": feasible,
                         "cost_per_feasible_completion_usd": spend / feasible if feasible else None}
    return result


def _project_paths(main: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: row[key] for key in (
        "project_id", "path_id", "repeat_index", "correction_kind", "frozen_v3",
        "corrected_v3", "frozen_v31", "corrected_v31", "base_cost_usd",
        "continuation_cost_usd", "corrected_cost_usd")}
            | {"changed_v3": row["frozen_v3"] != row["corrected_v3"],
               "changed_v31": row["frozen_v31"] != row["corrected_v31"]}
            for row in sorted(main, key=lambda item: (item["project_id"], item["path_id"]))]


def analyze() -> dict[str, Any]:
    continuation_rows = read_jsonl(CONTINUATIONS)
    continuation_invocations = read_jsonl(CONTINUATION_INVOCATIONS)
    ledger = json.loads(CONTINUATION_LEDGER.read_text())
    continuation_by_original = {row["continued_from"]: row for row in continuation_rows}
    if len(continuation_rows) != 40 or len(continuation_by_original) != 40:
        raise ValueError("continuation store is not complete at 40 distinct cells")
    if any(row["frozen_original_modified"] or not row["corrected_view_only"] for row in continuation_rows):
        raise ValueError("continuation record violates append-only corrected-view flags")
    if len(continuation_invocations) != 40 or len({row["invocation_id"] for row in continuation_invocations}) != 40:
        raise ValueError("continuation invocation correspondence is not 40/40")
    if ledger["calls"] != 40 or ledger["failed_attempts"] != 0 or ledger["pending"] != {}:
        raise ValueError("continuation ledger is not in the completed state")
    invocation_ids = {row["invocation_id"] for row in continuation_invocations}
    record_invocations = {inv for row in continuation_rows for stage in row["remaining_stages"]
                          for inv in stage["invocation_ids"]}
    if invocation_ids != record_invocations:
        raise ValueError("continuation records and invocations differ")
    invocation_spend = sum(float(row["incurred_cost_usd"]) for row in continuation_invocations)
    if abs(invocation_spend - float(ledger["spent_usd_priced"])) > 1e-9:
        raise ValueError("continuation invocation spend does not reconcile to ledger")

    continuation_v31: dict[str, dict[str, Any] | None] = {}
    continuation_voids = []
    for row in continuation_rows:
        stage = row["remaining_stages"][0]
        if stage["stage"] != "reporting" or not row["recovered_stage_validation"]["hard_pass"]:
            raise ValueError(f"invalid continuation shape: {row['run_id']}")
        if row["outcome"] != "complete_for_corrected_view" or stage["status"] == "infra_error":
            continuation_voids.append({"continued_from": row["continued_from"],
                                       "continuation_run_id": row["run_id"],
                                       "stage_status": stage["status"]})
            continuation_v31[row["continued_from"]] = None
        else:
            continuation_v31[row["continued_from"]] = _rescore_continuation_reporting(row)

    cleaning_recoveries = _cleaning_recoveries()
    correction_overlap = cleaning_recoveries & {
        (row["group"], row["continued_from"]) for row in continuation_rows
    }
    if len(correction_overlap) != 1:
        raise ValueError(f"expected one cleaning/analysis correction overlap, got {len(correction_overlap)}")
    base_costs = _base_costs()
    group_outputs: dict[str, Any] = {}
    all_run_rows: list[dict[str, Any]] = []

    for group in GROUPS:
        _, raw, effective, rerun_audit = load_records(group)
        v31_existing = _v31_records(group)
        rows = []
        for run in effective:
            original_statuses = [stage.status.value for stage in run.stages]
            frozen_v3, frozen_v3_first = _status_outcome(original_statuses)
            if frozen_v3 != run.feasibility.outcome:
                raise ValueError(f"stored frozen feasibility mismatch: {run.run_id}")
            existing_report = v31_existing.get(run.run_id)
            frozen_v31_statuses = list(original_statuses)
            if all(value == "passed" for value in original_statuses[:2]) and existing_report \
                    and existing_report["v31_ground_truth"]["hard_pass"]:
                frozen_v31_statuses[2] = "passed"
            frozen_v31, frozen_v31_first = _status_outcome(frozen_v31_statuses)

            corrected_statuses = list(original_statuses)
            corrected_v31_statuses = list(frozen_v31_statuses)
            cleaning_recovered = (group, run.run_id) in cleaning_recoveries
            correction_kind = "none"
            cont = continuation_by_original.get(run.run_id)
            continuation_cost = 0.0
            continuation_run_id = None
            if cont is not None:
                if cont["group"] != group or cont["project_id"] != run.project_id \
                        or cont["path_id"] != run.path_id or cont["repeat_index"] != run.repeat_index:
                    raise ValueError(f"continuation coordinates differ: {run.run_id}")
                if original_statuses[0] != "passed" and not cleaning_recovered:
                    raise ValueError(f"analysis continuation lacks passed/recovered cleaning: {run.run_id}")
                if original_statuses[1] != "failed":
                    raise ValueError(f"analysis continuation lacks failed analysis: {run.run_id}")
                correction_kind = ("cleaning_and_analysis_continuation" if cleaning_recovered
                                   else "analysis_continuation")
                continuation_run_id = cont["run_id"]
                report_stage = cont["remaining_stages"][0]
                continuation_cost = float(report_stage.get("cost_usd") or 0.0)
                if run.run_id in {row["continued_from"] for row in continuation_voids}:
                    corrected_statuses = ["passed", "passed", "infra_error"]
                    corrected_v31_statuses = list(corrected_statuses)
                else:
                    corrected_statuses = ["passed", "passed", report_stage["status"]]
                    rescore = continuation_v31[run.run_id]
                    corrected_v31_statuses = ["passed", "passed",
                                               "passed" if rescore and rescore["v31_pass"]
                                               else report_stage["status"]]
            elif cleaning_recovered:
                if original_statuses[0] != "failed":
                    raise ValueError(f"cleaning recovery does not begin with failed cleaning: {run.run_id}")
                correction_kind = "cleaning_observed_downstream"
                corrected_statuses[0] = "passed"

            if cont is None:
                corrected_v31_statuses = list(corrected_statuses)
                if all(value == "passed" for value in corrected_statuses[:2]) and existing_report \
                        and existing_report["v31_ground_truth"]["hard_pass"]:
                    corrected_v31_statuses[2] = "passed"

            corrected_v3, corrected_v3_first = _status_outcome(corrected_statuses)
            corrected_v31, corrected_v31_first = _status_outcome(corrected_v31_statuses)
            base = base_costs[run.run_id]["base_cost_usd"]
            row = {
                "group": group, "run_id": run.run_id, "project_id": run.project_id,
                "path_id": run.path_id, "repeat_index": run.repeat_index,
                "correction_kind": correction_kind, "continuation_run_id": continuation_run_id,
                "downstream_saw_upstream_failed_label": cleaning_recovered,
                "frozen_v3": frozen_v3, "corrected_v3": corrected_v3,
                "frozen_v31": frozen_v31, "corrected_v31": corrected_v31,
                "first_failure": {"frozen_v3": frozen_v3_first,
                                  "corrected_v3": corrected_v3_first,
                                  "frozen_v31": frozen_v31_first,
                                  "corrected_v31": corrected_v31_first},
                "base_cost_usd": base, "continuation_cost_usd": continuation_cost,
                "corrected_cost_usd": base + continuation_cost,
            }
            rows.append(row)
            all_run_rows.append(row)

        main = [row for row in rows if row["repeat_index"] == 0]
        single = [row for row in main if len(set(row["path_id"].split("-"))) == 1]
        cross = [row for row in main if len(set(row["path_id"].split("-"))) > 1]
        if len(main) != 108 or len(single) != 12 or len(cross) != 96:
            raise ValueError(f"unexpected main-grid denominators for {group}")
        failures = {view: dict(sorted(Counter(row["first_failure"][view] for row in main).items()))
                    for view in ("frozen_v3", "corrected_v3", "frozen_v31", "corrected_v31")}
        path_rows = _project_paths(main)
        group_outputs[group] = {
            "effective_cell_audit": {"raw_records": len(raw), "effective_records": len(effective),
                                     "rerun_replacements": len(rerun_audit.get("replacements", []))},
            "correction_counts": dict(sorted(Counter(row["correction_kind"] for row in rows).items())),
            "main_grid": _outcome_views(main),
            "single_model_main_grid": _outcome_views(single),
            "cross_model_main_grid": _outcome_views(cross),
            "first_failure_stage_main_grid": failures,
            "project_path_outcomes_main_grid": path_rows,
            "changed_paths_main_grid": [row for row in path_rows if row["changed_v3"] or row["changed_v31"]],
            "costs": {"main_grid": _cost_summary(main), "all_effective": _cost_summary(rows)},
        }

    if len(all_run_rows) != 312:
        raise ValueError("expected 156 effective cells per group")
    continuation_stage_spend = sum(row["continuation_cost_usd"] for row in all_run_rows)
    if abs(continuation_stage_spend - invocation_spend) > 1e-9:
        raise ValueError("continuation costs assigned to corrected cells do not reconcile")
    if sum(row["continuation_run_id"] is not None for row in all_run_rows) != 40:
        raise ValueError("not all continuation cells were used")
    if sum(row["downstream_saw_upstream_failed_label"] for row in all_run_rows) != 11:
        raise ValueError("not all cleaning recovery cells were used")

    source_paths = [RULES, PROTOCOL, DIAGNOSTICS, Q1, CONTINUATIONS, CONTINUATION_INVOCATIONS,
                    CONTINUATION_LEDGER, ORIGINAL_COSTS, PRICE_COSTS,
                    REPO / "src/evaluation/reporting_v3.py",
                    REPO / "src/evaluation/reporting_v3_1.py",
                    *[cfg[key] for cfg in GROUPS.values() for key in ("part_b", "v31_b")]]
    return {
        "label": "post-hoc / corrected sensitivity; frozen outcomes remain side by side",
        "scope": "Part B effective cells only; no router retraining or router-validity recomputation",
        "rules": {
            "analysis_continuation": "passed original cleaning + replay-recovered analysis + new reporting",
            "cleaning_recovery": "replay-recovered cleaning + observed downstream stages; downstream handoff saw failed upstream label",
            "correction_overlap": "one cell has both cleaning and analysis recovery; it is counted once as a cell and in both evidence inventories",
            "rounding_recovery_applied_to_q2": False,
            "v3_primary_v31_secondary": True,
        },
        "integrity_audit": {
            "status": "pass", "continuation_records": len(continuation_rows),
            "distinct_continued_from": len(continuation_by_original),
            "continuation_invocations": len(continuation_invocations),
            "continuation_void_infra": len(continuation_voids),
            "continuation_void_records": continuation_voids,
            "cleaning_recoveries_with_observed_downstream": len(cleaning_recoveries),
            "cleaning_and_analysis_recovery_overlap": len(correction_overlap),
            "cleaning_recovery_downstream_saw_failed_label": True,
            "ledger": {key: ledger[key] for key in ("calls", "input_tokens", "output_tokens",
                                                     "spent_usd_priced", "failed_attempts", "pending")},
            "record_invocation_cost_reconciled": True,
            "raw_or_frozen_inputs_modified": False,
        },
        "source_hashes": ({str(path.relative_to(REPO)): hash_file(path) for path in source_paths}
                          | {"datasets/projects": hash_tree(REPO / "datasets/projects")}),
        "model_groups": group_outputs,
        "router_validity_open_item": (
            "Corrected labels may change the frozen 22/50 and 31/64 feasibility-direction counts; "
            "this analysis does not recompute router validity or modify prior router conclusions."
        ),
    }


def pct(view: dict[str, Any]) -> str:
    rate = view["feasibility_rate"]
    return f"{view['n_feasible']}/{view['n_nonvoid']} ({100 * rate:.1f}%)" if rate is not None else "not estimable"


def money(value: float | None) -> str:
    return "not estimable" if value is None else f"${value:.4f}"


def _summary_table(result: dict[str, Any]) -> list[str]:
    lines = ["| Group | View | All paths | Single-model | Cross-model |",
             "|---|---|---:|---:|---:|"]
    for group in ("original_4096", "price_matched_16384"):
        data = result["model_groups"][group]
        label = "Original group (4096)" if group == "original_4096" else "Price-matched group (16384)"
        for view in ("frozen_v3", "corrected_v3", "frozen_v31", "corrected_v31"):
            lines.append(f"| {label} | {view} | {pct(data['main_grid'][view])} | "
                         f"{pct(data['single_model_main_grid'][view])} | "
                         f"{pct(data['cross_model_main_grid'][view])} |")
    return lines


def _failure_table(result: dict[str, Any]) -> list[str]:
    lines = ["| Group | View | Cleaning | Analysis | Reporting | None (feasible) |",
             "|---|---|---:|---:|---:|---:|"]
    for group in ("original_4096", "price_matched_16384"):
        label = "Original group" if group == "original_4096" else "Price-matched group"
        for view, counts in result["model_groups"][group]["first_failure_stage_main_grid"].items():
            lines.append(f"| {label} | {view} | {counts.get('cleaning', 0)} | "
                         f"{counts.get('analysis', 0)} | {counts.get('reporting', 0)} | "
                         f"{counts.get('none_feasible', 0)} |")
    return lines


def _changes_table(result: dict[str, Any]) -> list[str]:
    lines = ["| Group | Project | Path | Correction | v3 frozen → corrected | v3.1 frozen → corrected |",
             "|---|---|---|---|---|---|"]
    for group in ("original_4096", "price_matched_16384"):
        label = "Original" if group == "original_4096" else "Price-matched"
        for row in result["model_groups"][group]["changed_paths_main_grid"]:
            lines.append(f"| {label} | {row['project_id']} | `{row['path_id']}` | "
                         f"{row['correction_kind']} | {row['frozen_v3']} → {row['corrected_v3']} | "
                         f"{row['frozen_v31']} → {row['corrected_v31']} |")
    return lines


def render_report(result: dict[str, Any]) -> str:
    original = result["model_groups"]["original_4096"]
    price = result["model_groups"]["price_matched_16384"]
    audit = result["integrity_audit"]
    return "\n".join([
        "# Corrected Q2 View (Post-hoc)", "",
        "**POST-HOC / CORRECTED SENSITIVITY. Frozen workflow outcomes remain authoritative and are shown beside every corrected view.**", "",
        "## Key Findings", "",
        f"- Original-group main-grid feasibility changes from **{pct(original['main_grid']['frozen_v3'])}** frozen to **{pct(original['main_grid']['corrected_v3'])}** corrected under v3; the v3.1 comparison is **{pct(original['main_grid']['frozen_v31'])}** to **{pct(original['main_grid']['corrected_v31'])}**. Denominator: 108 cells.",
        f"- Price-matched-group main-grid feasibility changes from **{pct(price['main_grid']['frozen_v3'])}** to **{pct(price['main_grid']['corrected_v3'])}** under v3, and from **{pct(price['main_grid']['frozen_v31'])}** to **{pct(price['main_grid']['corrected_v31'])}** under v3.1. Denominator: 108 cells.",
        f"- The view uses all **{audit['continuation_records']}/40** analysis continuations and all **{audit['cleaning_recoveries_with_observed_downstream']}/11** cleaning recoveries; one cell belongs to both evidence sets, and continuation infrastructure voids were **{audit['continuation_void_infra']}**.",
        f"- Continuation spend was **{money(audit['ledger']['spent_usd_priced'])}**, reconciled across 40 records, 40 invocations, and the separate ledger; failed paid attempts were {audit['ledger']['failed_attempts']}.",
        "- These corrections may change the labels used to assess the frozen Router's 22/50 and 31/64 feasibility-direction results. That is an open item only: no Router validity number was recomputed here.",
        "", "## Scope and Rules", "",
        "A corrected analysis-continuation cell combines the original passed or replay-recovered cleaning stage, replay-recovered analysis artifact, and newly executed reporting result under frozen v3. A corrected cleaning-only cell substitutes the replay-passed cleaning status and keeps the already observed analysis/reporting outcomes. One cell needs both cleaning and analysis recovery and therefore uses its continuation reporting result, but it is still counted only once as a workflow cell. All 11 downstream handoffs saw cleaning status `failed`; they are therefore labelled sensitivity evidence, not a reconstruction of how downstream models would respond to a different label. V3.1 is a separate offline rescore of reporting. Q1 stated-precision rounding recoveries are not applied to Q2.",
        "", "Source: `results/processed/corrected_q2.json`, fields `rules` and `integrity_audit`; inputs and hashes are in `source_hashes`.",
        "", "## Feasibility", "", *_summary_table(result), "",
        "All numerators and denominators above come from `model_groups.<group>.{main_grid,single_model_main_grid,cross_model_main_grid}` in `results/processed/corrected_q2.json`.",
        "", "## Single-model and Cross-model Paths", "",
        "Single-model denominators are 12 per group (three alias-constant paths × four projects); cross-model denominators are 96. The unequal denominators make the rates descriptive, not a causal claim about mixing models. Model mappings for this rendered report are: original A/B/C = Sonnet 4.6 / Nova Pro / gpt-oss-120b; price-matched A/B/C = Sonnet 4.6 / Kimi K3 / GLM 5. The processed JSON contains aliases only.",
        "", "## Project and Path Changes", "",
        "Every one of the 108 per-group project/path outcomes is stored in `model_groups.<group>.project_path_outcomes_main_grid`. The table below lists only paths whose v3 or v3.1 outcome changed.",
        "", *_changes_table(result), "",
        "## First-failure Stage", "", *_failure_table(result), "",
        "Source: `results/processed/corrected_q2.json`, `model_groups.<group>.first_failure_stage_main_grid`. Counts include all 108 main-grid cells and sum to 108 in every row.",
        "", "## Cost per Feasible Completion", "",
        "Frozen cost-per-feasible values use the original executed spend. Corrected values add each continuation call to its original run, so failed original stages and all extra continuation calls remain charged.",
        "", "| Group | Scope | Base spend | Added continuation spend | Corrected spend | Frozen v3 cost/success | Corrected v3 cost/success | Frozen v3.1 cost/success | Corrected v3.1 cost/success |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        *[f"| {'Original' if group == 'original_4096' else 'Price-matched'} | {scope} | "
          f"{money(cost['base_spend_usd'])} | {money(cost['continuation_spend_usd'])} | "
          f"{money(cost['corrected_total_spend_usd'])} | "
          f"{money(cost['frozen_v3']['cost_per_feasible_completion_usd'])} | "
          f"{money(cost['corrected_v3']['cost_per_feasible_completion_usd'])} | "
          f"{money(cost['frozen_v31']['cost_per_feasible_completion_usd'])} | "
          f"{money(cost['corrected_v31']['cost_per_feasible_completion_usd'])} |"
          for group in ("original_4096", "price_matched_16384")
          for scope, cost in result["model_groups"][group]["costs"].items()],
        "", "Source: `results/processed/corrected_q2.json`, `model_groups.<group>.costs`. Base costs come from the previously reconciled workflow cost outputs; added spend reconciles to `results/raw/ledgers/continuations.json`.",
        "", "## Limitations and Open Items", "",
        "This is an additive post-hoc view of known serialization artifacts. It does not modify frozen records, apply rounding sensitivity to end-to-end feasibility, retrain the Router, or recompute counterfactual validity. The 11 cleaning recoveries retain observed downstream outcomes even though those downstream prompts saw an upstream `failed` status. No continuation was void-infrastructure; if one had been, it would have remained separately reported with no substantive replacement.",
        "", "## Sources and Reproduction", "", "```bash",
        ".venv/bin/python -m experiments.analyze_corrected_q2", "```", "",
        "The JSON artifact is the authoritative numerical layer. This renderer is deterministic over the source hashes recorded there.", "",
    ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args(argv)
    result = analyze()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.report.write_text(render_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
