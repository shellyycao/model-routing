"""Phase 2 (retrospective): EMPIRICAL VALIDITY of logged counterfactuals + S4 oracle comparison.

Runs only on the output directory of experiments/evaluate_routing.py (phase 1). Refuses to run if the
prediction log's hash chain is broken; every prediction is re-validated (content hash) and
CounterfactualValidation.check_against() is called on the stored prediction. Failed predictions are
kept and listed. Computational faithfulness is NOT recomputed or merged here.

Outputs (in --out):
  counterfactual_validations.jsonl(.head)  hash-chained CounterfactualValidation records
  empirical_validity.json                  descriptive summary per strategy (no significance claims)
  oracle_traces.jsonl                      S4 RETROSPECTIVE oracle traces (not deployable, not predictions)
  oracle_comparison.json                   each prospective decision vs. the held-out project's outcomes

Usage: .venv/bin/python -m experiments.validate_counterfactuals --records <file-or-dir> --out <dir>
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from src.contracts import DecisionTrace, canonical_json
from src.explainability.validation import validate_log
from src.routing.config import DEFAULT_CONFIG_PATH, RoutingConfig, load_routing_config
from src.routing.data import RecordStore, ensure_output_allowed, load_records
from src.routing.outcomes import aggregate_runs
from src.routing.strategies import oracle_s4

PRED_LOG = "counterfactual_predictions.jsonl"
VAL_LOG = "counterfactual_validations.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_validate(store: RecordStore, cfg: RoutingConfig, out: Path, validated_at: str | None = None) -> dict:
    ensure_output_allowed(out, store)
    validated_at = validated_at or _now()
    if (out / VAL_LOG).exists():
        raise FileExistsError(f"{out / VAL_LOG} exists; validation already ran for this prediction log")
    vr = validate_log(out / PRED_LOG, store, validated_at, out / VAL_LOG)
    (out / "empirical_validity.json").write_text(json.dumps(
        {"section": "EMPIRICAL VALIDITY (prediction vs executed outcome; descriptive only)",
         "synthetic_fixture": store.is_synthetic, "validated_at": validated_at,
         "n_predictions": len(vr.predictions), "by_strategy": vr.summary}, indent=2) + "\n")

    traces = [DecisionTrace.model_validate_json(ln) for ln in (out / "traces.jsonl").read_text().splitlines() if ln]
    comparison = []
    with open(out / "oracle_traces.jsonl", "w") as fh:
        for project in sorted({t.target_project for t in traces}):
            oracle = oracle_s4(store, project, cfg, validated_at)
            fh.write(canonical_json(oracle.model_dump(mode="json")) + "\n")
            runs = store.retrospective_outcomes(project)
            for t in (t for t in traces if t.target_project == project):
                executed = t.selected_path_id or (t.explanation_components.get("policy_path_id"))
                po = aggregate_runs(executed, runs) if executed else None
                comparison.append({
                    "held_out_project": project, "strategy": t.strategy.value, "trace_id": t.trace_id,
                    "selected_path_id": t.selected_path_id, "no_feasible_path": t.no_feasible_path,
                    "policy_path_id": t.explanation_components.get("policy_path_id"),
                    "executed_outcome": None if po is None else {"label": po.outcome_label, "values": po.values,
                                                                 "n_runs": po.n_runs, "n_void": po.n_void},
                    "oracle_selected_path_id": oracle.selected_path_id,
                    "matches_oracle_selection": t.selected_path_id == oracle.selected_path_id,
                    "in_oracle_feasible_set": executed in oracle.feasible_path_ids if executed else None,
                    "in_oracle_pareto_set": executed in oracle.pareto_path_ids if executed else None,
                })
    (out / "oracle_comparison.json").write_text(json.dumps(
        {"section": "S4 ORACLE COMPARISON (retrospective reference; the oracle is NOT a deployable router)",
         "synthetic_fixture": store.is_synthetic, "rows": comparison}, indent=2) + "\n")
    return {"n_validations": len(vr.validations), "summary": vr.summary, "oracle_rows": len(comparison)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--records", required=True)
    ap.add_argument("--out", required=True, help="output directory of evaluate_routing (phase 1)")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    args = ap.parse_args(argv)
    r = run_validate(load_records(args.records), load_routing_config(args.config), Path(args.out))
    print(json.dumps({"n_validations": r["n_validations"], "oracle_rows": r["oracle_rows"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
