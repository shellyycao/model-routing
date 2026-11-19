"""Input loading, provenance hashing, output guard and deterministic table writing.

Record parsing reuses ``src.routing.data`` (contract-version check, duplicate run_id check,
SYNTHETIC_FIXTURE detection). Nothing here re-implements those rules.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from src.routing.data import SYNTHETIC_MARKER, RecordStore, load_records, read_jsonl
from src.contracts import WorkflowRunRecord

from .reruns import SUCCESSFUL_RERUN_REPLACES_VOID, resolve_workflow_reruns

from . import SCHEMA_VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]
STATUS_VALUES = ("complete", "partial", "insufficient_evidence", "pilot_only")


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path: str | Path) -> str:
    """Repo-relative POSIX path when possible (keeps metadata machine-independent)."""
    p = Path(path).resolve()
    try:
        return p.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return p.name


def code_version() -> str:
    """git HEAD of the repo, with '-dirty' if analysis code/config has uncommitted changes."""
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "experiments", "configs"],
                               cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()
        return head + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


@dataclass
class Inputs:
    store: RecordStore
    sources: dict[str, str] = field(default_factory=dict)   # repo-relative path -> sha256
    routing_dir: Path | None = None
    rescores: list[dict] = field(default_factory=list)       # parsed rescore JSON (+ "_source")
    synthetic: bool = False
    rerun_resolution: dict | None = None


def load_inputs(workflow_records: list[str | Path], stage_benchmark_records: list[str | Path] = (),
                routing_dir: str | Path | None = None, reporting_rescores: list[str | Path] = (),
                rerun_resolution: str | None = None) -> Inputs:
    sources: dict[str, str] = {}
    recs = []
    for f in [*workflow_records, *stage_benchmark_records]:
        p = Path(f)
        if not p.is_file():
            raise FileNotFoundError(f"record file not found: {p}")
        sources[rel(p)] = sha256_file(p)
        recs.extend(read_jsonl(p))
    resolution_audit = None
    if rerun_resolution is not None:
        if rerun_resolution != SUCCESSFUL_RERUN_REPLACES_VOID:
            raise ValueError(f"unknown rerun_resolution {rerun_resolution!r}")
        workflow = [rec for rec in recs if isinstance(rec, WorkflowRunRecord)]
        effective, resolution_audit = resolve_workflow_reruns(workflow)
        recs = [rec for rec in recs if not isinstance(rec, WorkflowRunRecord)] + effective
    store = load_records(recs)
    rdir = None
    if routing_dir is not None and Path(routing_dir).is_dir():
        rdir = Path(routing_dir)
        for name in sorted(p.name for p in rdir.iterdir() if p.is_file()):
            if name.endswith((".jsonl", ".json")):
                sources[rel(rdir / name)] = sha256_file(rdir / name)
    rescores = []
    for f in reporting_rescores:
        p = Path(f)
        if not p.is_file():
            continue
        sources[rel(p)] = sha256_file(p)
        d = json.loads(p.read_text(encoding="utf-8"))
        d["_source"] = rel(p)
        rescores.append(d)
    synthetic = store.is_synthetic or any(SYNTHETIC_MARKER in k for k in sources)
    if rdir is not None:
        man = rdir / "predict_manifest.json"
        if man.exists() and json.loads(man.read_text()).get("synthetic_fixture"):
            synthetic = True
    return Inputs(store=store, sources=dict(sorted(sources.items())), routing_dir=rdir,
                  rescores=rescores, synthetic=synthetic, rerun_resolution=resolution_audit)


def ensure_output_allowed(out_dir: str | Path, synthetic: bool) -> None:
    """Same rule as src.routing.data.ensure_output_allowed, extended to every analysis input:
    output derived from any SYNTHETIC_FIXTURE input must never be written under results/."""
    if not synthetic:
        return
    out = Path(out_dir).resolve()
    results = (REPO_ROOT / "results").resolve()
    if out == results or results in out.parents:
        raise ValueError(f"refusing to write SYNTHETIC_FIXTURE-derived analysis output under {results}")


# --------------------------------------------------------------------------- writing

def _cell(v) -> str:
    if v is None:
        return ""                       # missing (e.g. unpriced cost) is empty, never 0
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            raise ValueError("non-finite value in table")
        return repr(v)
    if isinstance(v, (dict, list, tuple)):
        return json.dumps(v, sort_keys=True, separators=(",", ":"))
    return str(v)


@dataclass
class Table:
    name: str
    columns: list[str]
    rows: list[dict]
    status: str
    evidence_status: str
    notes: list[str] = field(default_factory=list)
    extra_meta: dict = field(default_factory=dict)

    def __post_init__(self):
        for s in (self.status, self.evidence_status):
            if s not in STATUS_VALUES:
                raise ValueError(f"bad status {s!r}")
        for r in self.rows:
            unknown = set(r) - set(self.columns)
            if unknown:
                raise ValueError(f"table {self.name}: unknown columns {sorted(unknown)}")


def write_table(table: Table, out_dir: Path, meta: dict) -> list[Path]:
    """Write <name>.json ({metadata, columns, rows}) and <name>.csv ('# key: value' metadata
    lines, then a normal CSV header + rows). Deterministic: sorted keys, fixed column order."""
    md = dict(meta) | {"table": table.name, "status": table.status,
                       "evidence_status": table.evidence_status, "n_rows": len(table.rows),
                       "notes": table.notes} | table.extra_meta
    rows = [{c: r.get(c) for c in table.columns} for r in table.rows]
    jp = out_dir / f"{table.name}.json"
    jp.write_text(json.dumps({"metadata": md, "columns": table.columns, "rows": rows},
                             indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    buf = io.StringIO()
    for k in sorted(md):
        buf.write(f"# {k}: {_cell(md[k])}\n")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(table.columns)
    for r in rows:
        w.writerow([_cell(r[c]) for c in table.columns])
    cp = out_dir / f"{table.name}.csv"
    cp.write_text(buf.getvalue(), encoding="utf-8")
    return [jp, cp]


def base_meta(inputs: Inputs, generated_at: str, code_ver: str, experiment_ids: list[str]) -> dict:
    meta = {"schema_version": SCHEMA_VERSION, "generated_at": generated_at, "code_version": code_ver,
            "source_files": inputs.sources, "experiment_ids": experiment_ids,
            "synthetic_fixture": inputs.synthetic}
    if inputs.rerun_resolution is not None:
        meta["rerun_resolution"] = inputs.rerun_resolution
    return meta
