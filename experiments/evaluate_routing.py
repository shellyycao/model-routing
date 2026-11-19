"""Leave-one-project-out routing evaluation (offline; no AWS calls).

Phase 1 (`predict`, default) — prospective, for each held-out project:
  TrainingView (held-out records physically excluded) -> S1/S2/S3 decision traces -> template
  explanations -> COMPUTATIONAL FAITHFULNESS checks -> counterfactual predictions appended to the
  hash-chained prediction log. No outcome of the held-out project is read in this phase.
Phase 2 (`--phase all`, or run experiments/validate_counterfactuals.py later) — retrospective:
  EMPIRICAL VALIDITY of the logged predictions and the S4 oracle comparison.

Outputs (in --out):
  traces.jsonl, explanations.jsonl        decision traces + rendered explanations
  computational_faithfulness.jsonl        FaithfulnessCheck per trace (separate from empirical validity)
  counterfactual_predictions.jsonl(.head) append-only hash-chained CounterfactualPrediction log
  predict_manifest.json

Usage:
  .venv/bin/python -m experiments.evaluate_routing --records <file-or-dir> --out <dir> [--phase all]
SYNTHETIC_FIXTURE inputs are refused if --out is under results/.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from src.contracts import canonical_json
from src.explainability.explanations import render_explanation
from src.explainability.validation import check_faithfulness
from src.routing.config import DEFAULT_CONFIG_PATH, RoutingConfig, load_routing_config
from src.routing.counterfactual import PredictionLog, generate_counterfactuals
from src.routing.data import RecordStore, build_training_view, ensure_output_allowed, load_records
from src.routing.strategies import decide_prospective

PRED_LOG = "counterfactual_predictions.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _append(path: Path, obj) -> None:
    with open(path, "a") as fh:
        fh.write(canonical_json(obj) + "\n")


def run_predict(store: RecordStore, cfg: RoutingConfig, out: Path, created_at: str | None = None) -> dict:
    ensure_output_allowed(out, store)
    out.mkdir(parents=True, exist_ok=True)
    for name in ("traces.jsonl", "explanations.jsonl", "computational_faithfulness.jsonl"):
        if (out / name).exists():
            raise FileExistsError(f"{out / name} exists; use a fresh output directory")
    created_at = created_at or _now()
    log = PredictionLog(out / PRED_LOG)
    manifest = {"synthetic_fixture": store.is_synthetic, "config_hash": cfg.config_hash,
                "router_version": cfg.router_version, "created_at": created_at, "folds": []}
    for project in store.projects():
        view = build_training_view(store, project)
        decisions = decide_prospective(view, cfg, created_at)
        fold = {"held_out_project": project, "training_projects": list(view.training_projects),
                "n_training_stage_records": len(view.stage_records),
                "n_training_workflow_runs": len(view.workflow_runs), "decisions": [], "counterfactual_notes": []}
        for traces in decisions.values():
            for t in traces:
                _append(out / "traces.jsonl", t.model_dump(mode="json"))
                expl = render_explanation(t)
                _append(out / "explanations.jsonl", expl.to_dict())
                fc = check_faithfulness(t, expl, created_at)
                _append(out / "computational_faithfulness.jsonl", fc.model_dump(mode="json"))
                preds, notes = generate_counterfactuals(t, created_at)
                for p in preds:                         # logged BEFORE any validation can run
                    log.append_prediction(p)
                fold["decisions"].append({"trace_id": t.trace_id, "strategy": t.strategy.value,
                                          "selected_path_id": t.selected_path_id,
                                          "no_feasible_path": t.no_feasible_path,
                                          "inactive_criteria": t.inactive_criteria,
                                          "n_counterfactuals_logged": len(preds),
                                          "faithfulness": f"{fc.claims_consistent}/{fc.claims_checked} claims; "
                                                          f"replay_matches_selection={fc.replay_matches_selection}"})
                fold["counterfactual_notes"] += notes
        manifest["folds"].append(fold)
    rep = log.verify()
    manifest["prediction_log"] = {"path": PRED_LOG, "n_lines": rep.n_lines, "head": rep.head, "chain_ok": rep.ok}
    (out / "predict_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--records", required=True, help="JSONL file or directory of JSONL records")
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    ap.add_argument("--phase", choices=["predict", "all"], default="predict")
    args = ap.parse_args(argv)
    store, cfg, out = load_records(args.records), load_routing_config(args.config), Path(args.out)
    m = run_predict(store, cfg, out)
    print(json.dumps({"phase": "predict", "folds": [(f["held_out_project"], [(d["strategy"], d["selected_path_id"])
                                                                            for d in f["decisions"]])
                                                   for f in m["folds"]],
                      "prediction_log": m["prediction_log"]}, indent=1))
    if args.phase == "all":
        from experiments.validate_counterfactuals import run_validate
        r = run_validate(store, cfg, out)
        print(json.dumps({"phase": "validate", "n_validations": r["n_validations"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
