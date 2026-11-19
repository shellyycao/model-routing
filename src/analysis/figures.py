"""Deterministic matplotlib figures (PNG) plus the data CSV behind each figure.

Every title carries the data label (PILOT ONLY / SYNTHETIC FIXTURE / PARTIAL / INSUFFICIENT EVIDENCE).
PNG metadata is stripped so identical inputs give byte-identical files.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .io import Table  # noqa: E402
from .tables import METRIC_KEYS, ORACLE_LABEL  # noqa: E402

INK, MUTED, ACCENT = "#1f2328", "#6e7781", "#2f6fb0"
UNIT_METRICS = [(s, m) for s, m in METRIC_KEYS if m != "unsupported_claim_count"]   # [0,1] metrics only


def data_label(status: str, evidence: str, synthetic: bool) -> str:
    parts = []
    if synthetic:
        parts.append("SYNTHETIC FIXTURE - not results")
    if status == "pilot_only":
        parts.append("PILOT ONLY - engineering smoke, not findings")
    if evidence == "partial":
        parts.append("PARTIAL DATA")
    if evidence == "insufficient_evidence":
        parts.append("INSUFFICIENT EVIDENCE")
    return " | ".join(parts) or "complete data (exploratory; no significance claims)"


def _style():
    plt.rcParams.update({"font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                         "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False,
                         "axes.spines.right": False, "svg.hashsalt": "analysis"})


def _save(fig, path: Path):
    fig.savefig(path, dpi=110, metadata={"Software": None}, bbox_inches="tight")
    plt.close(fig)


def _panel_groups(rows, key=("experiment_id", "project_id", "n_stages")):
    g = defaultdict(list)
    for r in rows:
        g[tuple(r.get(k) for k in key)].append(r)
    return dict(sorted(g.items(), key=lambda kv: tuple(str(x) for x in kv[0])))


def _empty(path: Path, title: str, msg: str):
    fig, ax = plt.subplots(figsize=(6, 2), layout="constrained")
    ax.axis("off")
    ax.text(0.5, 0.5, msg, ha="center", va="center", color=INK)
    fig.suptitle(title, color=INK, fontsize=9)
    _save(fig, path)


def fig_feasibility(ps: Table, label: str, out: Path) -> Table:
    rows = [{"experiment_id": r["experiment_id"], "project_id": r["project_id"], "n_stages": r["n_stages"],
             "path_id": r["path_id"], "feasibility_rate": r["feasibility_rate"], "n_valid": r["n_valid"],
             "n_void_infra": r["n_void_infra"]} for r in ps.rows if r.get("path_id")]
    title = f"Strict feasibility rate by path (void_infra excluded)\n{label}"
    groups = _panel_groups(rows)
    if not groups:
        _empty(out, title, "No workflow runs")
    else:
        fig, axes = plt.subplots(1, len(groups), figsize=(4.2 * len(groups), 0.9 + 0.22 * max(
            len(v) for v in groups.values())), squeeze=False, layout="constrained")
        for ax, ((exp, proj, n), rs) in zip(axes[0], groups.items()):
            y = np.arange(len(rs))
            vals = [r["feasibility_rate"] if r["feasibility_rate"] is not None else 0.0 for r in rs]
            ax.barh(y, vals, color=ACCENT, height=0.6)
            for yi, r in zip(y, rs):
                if r["feasibility_rate"] is None:
                    ax.text(0.01, yi, "void_infra only (excluded)", va="center", color=MUTED, fontsize=7)
            ax.set_yticks(y, [r["path_id"] for r in rs])
            ax.invert_yaxis()
            ax.set_xlim(0, 1)
            ax.set_xlabel("feasible / non-void runs")
            ax.set_title(f"{proj} ({n}-stage) [{exp}]", fontsize=8, color=INK)
        fig.suptitle(title, color=INK, fontsize=9)
        _save(fig, out)
    return Table("fig_feasibility_by_path_data", list(rows[0]) if rows else ["experiment_id"], rows,
                 ps.status, ps.evidence_status, notes=["Data behind fig_feasibility_by_path.png"])


def _heatmap(groups, cols, value, title, out, cmap, vmin, vmax, cbar_label):
    fig, axes = plt.subplots(len(groups), 1, figsize=(1.2 + 0.55 * len(cols), sum(
        2.4 + 0.22 * len(paths) for paths, _ in groups.values())), squeeze=False, layout="constrained")
    for ax, ((exp, proj, n), (paths, cells)) in zip(axes[:, 0], groups.items()):
        m = np.full((len(paths), len(cols)), np.nan)
        for i, p in enumerate(paths):
            for j, c in enumerate(cols):
                v = cells.get((p, c))
                if v is not None:
                    m[i, j] = v
        im = ax.imshow(np.ma.masked_invalid(m), cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
        ax.set_facecolor("#e6e6e6")
        ax.set_yticks(range(len(paths)), paths)
        ax.set_xticks(range(len(cols)), [f"{s}.{mm}" for s, mm in cols], rotation=60, ha="right")
        ax.set_title(f"{proj} ({n}-stage) [{exp}]  grey = not measured", fontsize=8, color=INK)
        fig.colorbar(im, ax=ax, label=cbar_label, fraction=0.03)
    fig.suptitle(title, color=INK, fontsize=9)
    _save(fig, out)


def fig_quality(ps: Table, label: str, out: Path) -> Table:
    rows = []
    for r in ps.rows:
        if not r.get("path_id"):
            continue
        for s, m in METRIC_KEYS:
            if r.get(f"gt.{s}.{m}") is not None or r.get(f"cond.{s}.{m}") is not None:
                rows.append({"experiment_id": r["experiment_id"], "project_id": r["project_id"],
                             "n_stages": r["n_stages"], "path_id": r["path_id"], "stage": s, "metric": m,
                             "gt_mean": r.get(f"gt.{s}.{m}"), "cond_mean": r.get(f"cond.{s}.{m}")})
    title = f"Ground-truth stage quality (mean over non-void runs; [0,1] metrics only)\n{label}"
    groups = {}
    for key, rs in _panel_groups([r for r in ps.rows if r.get("path_id")]).items():
        groups[key] = ([r["path_id"] for r in rs],
                       {(r["path_id"], (s, m)): r.get(f"gt.{s}.{m}") for r in rs for s, m in UNIT_METRICS})
    if not groups:
        _empty(out, title, "No workflow runs")
    else:
        _heatmap(groups, UNIT_METRICS, "gt", title, out, "Blues", 0.0, 1.0, "quality (ground truth)")
    cols = ["experiment_id", "project_id", "n_stages", "path_id", "stage", "metric", "gt_mean", "cond_mean"]
    return Table("fig_quality_heatmap_data", cols, rows, ps.status, ps.evidence_status,
                 notes=["Data behind fig_quality_heatmap.png (gt and conditional side by side)."])


def fig_propagation(pt: Table, label: str, out: Path) -> Table:
    rows = [{k: r[k] for k in ("experiment_id", "project_id", "path_id", "stage", "metric", "mean", "n")}
            for r in pt.rows if r.get("quantity") == "propagation_impact"]
    title = ("Propagation impact = conditional - ground-truth quality (descriptive decomposition,\n"
             "NOT a causal switching/handoff cost; colour clipped at +/-1, exact values in data CSV)\n"
             f"{label}")
    for r in rows:
        r["n_stages"] = len(r["path_id"].split("-"))
    cols = sorted({(r["stage"], r["metric"]) for r in rows}, key=lambda sm: [k for k in METRIC_KEYS].index(sm)
                  if sm in METRIC_KEYS else 99)
    groups = {}
    for key, rs in _panel_groups(rows).items():
        groups[key] = (sorted({r["path_id"] for r in rs}),
                       {(r["path_id"], (r["stage"], r["metric"])): r["mean"] for r in rs})
    if not groups:
        _empty(out, title, "No propagation impact recorded")
    else:
        _heatmap(groups, cols, "mean", title, out, "RdBu_r", -1.0, 1.0, "conditional - ground truth")
    c = ["experiment_id", "project_id", "n_stages", "path_id", "stage", "metric", "mean", "n"]
    return Table("fig_propagation_impact_data", c, rows, pt.status, pt.evidence_status,
                 notes=["Data behind fig_propagation_impact.png; descriptive, not causal."])


def fig_pareto(pa: Table, label: str, out: Path) -> Table:
    cands = [r for r in pa.rows if r.get("row_type") == "candidate"]
    rows = []
    for r in cands:
        q = r["quality_feasible_mean"] or {}
        last_stage = METRIC_KEYS[3 * (int(r["n_stages"]) - 1)][0]
        ykey = next((f"{s}.{m}" for s, m in UNIT_METRICS if s == last_stage and f"{s}.{m}" in q), None)
        rows.append({"experiment_id": r["experiment_id"], "project_id": r["project_id"], "n_stages": r["n_stages"],
                     "path_id": r["path_id"], "end_to_end_ms": r["end_to_end_ms"], "quality_key": ykey,
                     "quality_value": q.get(ykey) if ykey else None, "pareto_optimal": r["pareto_optimal"]})
    nofeas = [r for r in pa.rows if r.get("row_type") == "no_feasible_path"]
    title = ("Feasible paths: end-to-end time vs last-stage quality (Pareto set over ALL objectives)\n"
             f"{label}")
    groups = _panel_groups(rows)
    if not groups:
        msg = "No feasible path in any group" if nofeas else "No data"
        _empty(out, title, msg)
    else:
        fig, axes = plt.subplots(1, len(groups), figsize=(4.2 * len(groups), 3.2), squeeze=False, layout="constrained")
        for ax, ((exp, proj, n), rs) in zip(axes[0], groups.items()):
            for opt, mk, lab in ((True, "o", "Pareto-optimal"), (False, "x", "dominated")):
                pts = [r for r in rs if bool(r["pareto_optimal"]) == opt and r["end_to_end_ms"] is not None
                       and r["quality_value"] is not None]
                if pts:
                    ax.scatter([p["end_to_end_ms"] / 1000 for p in pts], [p["quality_value"] for p in pts],
                               marker=mk, s=40, color=ACCENT if opt else MUTED, label=lab)
                    for p in pts:
                        ax.annotate(p["path_id"], (p["end_to_end_ms"] / 1000, p["quality_value"]),
                                    fontsize=6, color=INK, xytext=(3, 3), textcoords="offset points")
            ax.set_xlabel("end-to-end time (s, mean over feasible runs)")
            ax.set_ylabel(rs[0]["quality_key"] or "quality")
            ax.set_title(f"{proj} ({n}-stage) [{exp}]", fontsize=8, color=INK)
            if ax.get_legend_handles_labels()[0]:
                ax.legend(fontsize=7, frameon=False)
        fig.suptitle(title, color=INK, fontsize=9)
        _save(fig, out)
    cols = ["experiment_id", "project_id", "n_stages", "path_id", "end_to_end_ms", "quality_key",
            "quality_value", "pareto_optimal"]
    return Table("fig_pareto_scatter_data", cols, rows, pa.status, pa.evidence_status,
                 notes=["Data behind fig_pareto_scatter.png. Groups with no feasible path are listed in pareto."])


def fig_counterfactual(cf: Table, label: str, out: Path) -> Table | None:
    rows = [{k: r[k] for k in ("project_id", "prediction_id", "strategy", "quantity", "predicted_delta",
                                "actual_delta")}
            for r in cf.rows if r.get("predicted_delta") is not None and r.get("actual_delta") is not None]
    if not rows:
        return None
    quantities = sorted({r["quantity"] for r in rows})
    strategies = sorted({r["strategy"] for r in rows})
    markers = ["o", "s", "^", "D"]
    fig, axes = plt.subplots(1, len(quantities), figsize=(3.4 * len(quantities), 3.4), squeeze=False, layout="constrained")
    for ax, q in zip(axes[0], quantities):            # one panel per quantity: scales never mixed
        qr = [r for r in rows if r["quantity"] == q]
        for i, s in enumerate(strategies):
            pts = [r for r in qr if r["strategy"] == s]
            if pts:
                ax.scatter([p["predicted_delta"] for p in pts], [p["actual_delta"] for p in pts], s=24,
                           marker=markers[i % 4], color=ACCENT if i == 0 else MUTED, label=s)
        lo = min(min(r["predicted_delta"], r["actual_delta"]) for r in qr)
        hi = max(max(r["predicted_delta"], r["actual_delta"]) for r in qr)
        ax.plot([lo, hi], [lo, hi], color=MUTED, linewidth=1, linestyle="--")
        ax.set_title(q, fontsize=8, color=INK)
        ax.set_xlabel("predicted delta (alt - selected)")
        ax.set_ylabel("actual delta (executed)")
        ax.legend(fontsize=6, frameon=False)
    fig.suptitle("Counterfactual deltas: predicted vs executed (empirical validity)\n" + label,
                 color=INK, fontsize=9)
    _save(fig, out)
    cols = ["project_id", "prediction_id", "strategy", "quantity", "predicted_delta", "actual_delta"]
    return Table("fig_counterfactual_deltas_data", cols, rows, cf.status, cf.evidence_status,
                 notes=["Data behind fig_counterfactual_deltas.png; S4 oracle is " + ORACLE_LABEL + "."])
