"""raw records -> processed tables (JSON + CSV) + figures (PNG + data CSV) + manifest.json.

Deterministic: same input files + same code version + same generated_at -> byte-identical outputs.
generated_at defaults to the latest timestamp found in the source records (not the wall clock), so a
rerun on unchanged inputs reproduces the same bytes; pass an explicit value to override.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import SCHEMA_VERSION
from . import figures as F
from . import tables as T
from .io import REPO_ROOT, base_meta, code_version, ensure_output_allowed, load_inputs, sha256_file, write_table

DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "analysis.yaml"


@dataclass
class AnalysisConfig:
    workflow_records: list[str]
    out_dir: str
    stage_benchmark_records: list[str] = field(default_factory=list)
    routing_dir: str | None = None
    reporting_rescores: list[str] = field(default_factory=list)
    experiment_group: list[str] = field(default_factory=list)      # explicit opt-in for several experiment_ids
    matched_pairs: dict[str, str] = field(default_factory=dict)    # expB id -> expA id
    benchmark_versions: dict[str, str] = field(default_factory=dict)
    status_override: str | None = None                             # e.g. pilot_only
    generated_at: str | None = None
    code_version: str | None = None
    rerun_resolution: str | None = None


def _abs(p: str | None) -> Path | None:
    if p is None:
        return None
    q = Path(p)
    return q if q.is_absolute() else REPO_ROOT / q


def load_config(path: str | Path = DEFAULT_CONFIG_PATH, **overrides) -> AnalysisConfig:
    raw = yaml.safe_load(Path(path).read_text()) or {}
    raw.pop("schema_version", None)
    raw.update({k: v for k, v in overrides.items() if v is not None})
    return AnalysisConfig(**raw)


def _check_experiments(kind: str, ids: set[str], group: list[str]) -> None:
    if len(ids) > 1 and not ids <= set(group):
        raise ValueError(f"{kind} records come from several experiment_ids {sorted(ids)}; refusing to mix them. "
                         "List them explicitly in experiment_group to analyse them side by side (never pooled).")


def run_analysis(cfg: AnalysisConfig) -> dict:
    out = _abs(cfg.out_dir)
    inputs = load_inputs([_abs(p) for p in cfg.workflow_records],
                         [_abs(p) for p in cfg.stage_benchmark_records],
                         _abs(cfg.routing_dir), [_abs(p) for p in cfg.reporting_rescores],
                         cfg.rerun_resolution)
    ensure_output_allowed(out, inputs.synthetic)
    store = inputs.store
    runs_by_exp, stage_by_exp = defaultdict(list), defaultdict(list)
    for r in store.workflow_runs:
        runs_by_exp[r.experiment_id].append(r)
    for s in store.stage_records:
        stage_by_exp[s.experiment_id].append(s)
    _check_experiments("Experiment B (workflow)", set(runs_by_exp), cfg.experiment_group)
    _check_experiments("Experiment A (stage benchmark)", set(stage_by_exp), cfg.experiment_group)
    for b, a in cfg.matched_pairs.items():
        if b not in runs_by_exp or a not in stage_by_exp:
            raise ValueError(f"matched_pairs {b}->{a} names an experiment with no loaded records")

    ctx = T.Context(runs_by_exp=dict(runs_by_exp), stage_by_exp=dict(stage_by_exp),
                    benchmark_versions=cfg.benchmark_versions, matched_pairs=cfg.matched_pairs,
                    status_override=cfg.status_override, routing_dir=inputs.routing_dir,
                    rescores=inputs.rescores, source_hashes=inputs.sources)
    stamps = [t for r in store.workflow_runs for t in (r.started_at, r.finished_at) if t]
    generated_at = cfg.generated_at or (max(stamps) if stamps else "unknown")
    meta = base_meta(inputs, generated_at, cfg.code_version or code_version(),
                     sorted({*runs_by_exp, *stage_by_exp}))
    meta["generated_at_basis"] = "explicit" if cfg.generated_at else "latest_source_record_timestamp"

    tables = [T.path_summary(ctx), T.propagation(ctx), T.matched_baseline(ctx), T.pareto(ctx),
              T.strategies(ctx), T.counterfactual_validity(ctx), T.faithfulness(ctx),
              T.reporting_scores(ctx), T.variability(ctx)]
    by_name = {t.name: t for t in tables}

    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for t in tables:
        written += write_table(t, out, meta)

    F._style()
    def label(t):
        return F.data_label(t.status, t.evidence_status, inputs.synthetic)
    fig_tables = [
        F.fig_feasibility(by_name["path_summary"], label(by_name["path_summary"]), out / "fig_feasibility_by_path.png"),
        F.fig_quality(by_name["path_summary"], label(by_name["path_summary"]), out / "fig_quality_heatmap.png"),
        F.fig_propagation(by_name["propagation"], label(by_name["propagation"]), out / "fig_propagation_impact.png"),
        F.fig_pareto(by_name["pareto"], label(by_name["pareto"]), out / "fig_pareto_scatter.png"),
    ]
    cf_fig = F.fig_counterfactual(by_name["counterfactual_validity"], label(by_name["counterfactual_validity"]),
                                  out / "fig_counterfactual_deltas.png")
    if cf_fig is not None:
        fig_tables.append(cf_fig)
    for ft in fig_tables:
        written += write_table(ft, out, meta)
        written.append(out / (ft.name.removesuffix("_data") + ".png"))

    manifest = {
        "schema_version": SCHEMA_VERSION, "generated_at": generated_at, "code_version": meta["code_version"],
        "synthetic_fixture": inputs.synthetic, "source_files": inputs.sources,
        "experiment_ids": meta["experiment_ids"],
        "tables": {t.name: {"status": t.status, "evidence_status": t.evidence_status, "n_rows": len(t.rows)}
                   for t in [*tables, *fig_tables]},
        "files": {p.name: sha256_file(p) for p in sorted(written)},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
