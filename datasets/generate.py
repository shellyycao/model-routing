"""Build benchmark projects deterministically from their seeds.

    python -m datasets.generate                     # (re)build every project in datasets/projects/
    python -m datasets.generate --project retail_sales --out /tmp/x
    python -m datasets.generate --check             # rebuild in a temp dir and compare bytes

Layout of datasets/projects/<project_id>/:
    project.json              ProjectSpec (src.contracts)
    raw.csv                   synthetic raw data with injected imperfections
    canonical/cleaned.csv     reference cleaning output (trusted Python)
    canonical/findings.json   reference analysis output (flat {metric_key: number})
    ground_truth.json         machine-readable expected outputs + tolerances + provenance
"""

from __future__ import annotations

import argparse
import importlib
import sys
import tempfile
from pathlib import Path
from types import ModuleType

from src.contracts import CONTRACT_VERSION, ProjectSpec

from .common import GENERATOR_VERSION, dump_json, sha256_file

PROJECTS_DIR = Path(__file__).resolve().parent / "projects"

# project_id -> module under datasets/. Order = development sequence.
REGISTRY: dict[str, str] = {
    "retail_sales": "datasets.retail_sales",
    "customer_churn": "datasets.customer_churn",
    "energy_consumption": "datasets.energy_consumption",
    "support_operations": "datasets.support_operations",
}

FILES = ("project.json", "raw.csv", "canonical/cleaned.csv", "canonical/findings.json", "ground_truth.json")


def project_files(project_id: str) -> tuple[str, ...]:
    """All generated files, including extra model inputs for multi-file projects."""
    spec = project_module(project_id).project_spec()
    extras = [f.path for f in spec.model_input_files() if f.path not in FILES]
    return FILES + tuple(extras)


def project_module(project_id: str) -> ModuleType:
    return importlib.import_module(REGISTRY[project_id])


def build_project(project_id: str, out_dir: Path) -> Path:
    mod = project_module(project_id)
    spec: ProjectSpec = mod.project_spec()
    assert spec.project_id == project_id and spec.seed == mod.SEED
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "canonical").mkdir(exist_ok=True)

    raw = out_dir / spec.raw_data_file
    gen_log = mod.generate_raw(raw)
    cleaned = out_dir / spec.canonical_cleaned_file
    clean_log = mod.reference_clean(raw, cleaned)
    metrics = mod.reference_analysis(cleaned)
    findings = out_dir / spec.canonical_findings_file
    dump_json(metrics, findings)

    expected_keys = [k for q in spec.analysis_questions for k in q.metric_keys]
    if sorted(expected_keys) != sorted(metrics) or len(set(expected_keys)) != len(expected_keys):
        raise RuntimeError(f"{project_id}: metric keys do not match the analysis questions")

    dump_json(spec.model_dump(mode="json"), out_dir / "project.json")
    ground_truth = {
        "label": "SYNTHETIC",
        "project_id": project_id,
        "seed": mod.SEED,
        "generator_version": GENERATOR_VERSION,
        "contract_version": CONTRACT_VERSION,
        "provenance": "Computed by deterministic reference code in datasets/ (no LLM).",
        "cleaning": {
            "key_column": mod.KEY_COLUMN,
            "columns": [c.name for c in spec.cleaned_schema],
            "value_abs_tolerance": mod.CLEAN_VALUE_ABS_TOL,
            "value_rel_tolerance": mod.CLEAN_VALUE_REL_TOL,
            "expected_row_count": clean_log["cleaned_rows"],
            "rule_log": clean_log,
        },
        "analysis": {
            "metrics": metrics,
            "tolerances": {k: {"question_id": q.question_id, "abs": q.abs_tolerance, "rel": q.rel_tolerance}
                           for q in spec.analysis_questions for k in q.metric_keys},
        },
        "generation": gen_log,
        "sha256": {
            "raw": sha256_file(raw),
            "canonical_cleaned": sha256_file(cleaned),
            "canonical_findings": sha256_file(findings),
            "model_inputs": {f.name: sha256_file(out_dir / f.path) for f in spec.model_input_files()},
        },
    }
    dump_json(ground_truth, out_dir / spec.ground_truth_file)
    return out_dir


def check_reproducible(project_id: str, committed_dir: Path | None = None) -> list[str]:
    """Rebuild into a temp dir; return the files whose bytes differ from the committed copy."""
    committed_dir = committed_dir or PROJECTS_DIR / project_id
    with tempfile.TemporaryDirectory() as tmp:
        fresh = build_project(project_id, Path(tmp) / project_id)
        return [f for f in project_files(project_id)
                if not (committed_dir / f).exists() or (committed_dir / f).read_bytes() != (fresh / f).read_bytes()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", action="append", choices=sorted(REGISTRY))
    ap.add_argument("--out", type=Path, default=PROJECTS_DIR, help="parent directory for project folders")
    ap.add_argument("--check", action="store_true", help="verify committed files are byte-reproducible")
    args = ap.parse_args(argv)
    ids = args.project or list(REGISTRY)
    if args.check:
        bad = {p: d for p in ids if (d := check_reproducible(p, args.out / p))}
        for p, files in bad.items():
            print(f"NOT REPRODUCIBLE {p}: {files}")
        if not bad:
            print(f"OK: {', '.join(ids)} byte-reproducible")
        return 1 if bad else 0
    for p in ids:
        print(f"built {build_project(p, args.out / p)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
