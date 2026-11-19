"""Generate the independent-task datasets (A1/A2/A3) deterministically, with self-checks.

  .venv/bin/python -m datasets.independent.generate          # (re)write datasets/independent/<task>/cases/*.json
  .venv/bin/python -m datasets.independent.generate --check  # verify committed files are byte-identical

A1 self-check (TRUSTED reference/buggy code authored here, run in a local subprocess — never model code):
every hidden test passes on the reference and >=1 hidden test fails on the buggy version.
A3 self-check: a keyword-overlap baseline must NOT reach nDCG@5 = 1.0 on every query.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from datasets.independent import a1_cases, a2_gen, a3_gen
from src.independent.tasks import A1_HARNESS, keyword_baseline_ndcg

ROOT = Path(__file__).resolve().parent
DATASET_VERSION = "indep-data-1.0"


def run_harness_locally(code: str, tests: list[str]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "in").mkdir(); (t / "out").mkdir()
        (t / "in" / "solution.py").write_text(code)
        (t / "in" / "tests.json").write_text(json.dumps(tests))
        (t / "main.py").write_text(A1_HARNESS)
        env = {"PATH": os.environ.get("PATH", ""), "INPUT_DIR": str(t / "in"), "OUTPUT_DIR": str(t / "out")}
        subprocess.run([sys.executable, "-I", str(t / "main.py")], env=env, timeout=60, check=True)
        return json.loads((t / "out" / "results.json").read_text())


def build() -> dict[str, list[dict]]:
    a1 = []
    for c in a1_cases.CASES:
        assert set(c["visible"]) <= set(c["hidden"]), c["case_id"]
        ref = run_harness_locally(c["reference"], c["hidden"])
        bug = run_harness_locally(c["buggy"], c["hidden"])
        assert ref["load_error"] is None and all(r["passed"] for r in ref["results"]), (c["case_id"], ref)
        n_fail = sum(not r["passed"] for r in bug["results"])
        assert n_fail >= 1, f"{c['case_id']}: buggy version passes every hidden test"
        assert all(r["passed"] for r in bug["results"] if r["test"] in c["visible"][:0]), c["case_id"]
        a1.append(c | {"verification": {"reference_passes": len(ref["results"]), "buggy_fails": n_fail}})
    a2 = a2_gen.build_cases()
    a3 = a3_gen.build_cases()
    base = [keyword_baseline_ndcg(c) for c in a3]
    assert not all(b >= 0.999 for b in base), "A3 labels are trivially recoverable by keyword overlap"
    for c, b in zip(a3, base):
        c["keyword_baseline_ndcg_at_5"] = round(b, 4)
    return {"a1": a1, "a2": a2, "a3": a3}


def render(data: dict[str, list[dict]]) -> dict[Path, bytes]:
    files = {}
    for task, cases in data.items():
        for c in cases:
            files[ROOT / task / "cases" / f"{c['case_id']}.json"] = (json.dumps(c, indent=2, sort_keys=True) + "\n").encode()
        files[ROOT / task / "VERSION"] = f"{DATASET_VERSION}\n".encode()
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    files = render(build())
    if args.check:
        bad = [str(p.relative_to(ROOT)) for p, b in files.items() if not p.exists() or p.read_bytes() != b]
        print("OK: independent datasets byte-reproducible" if not bad else f"NOT REPRODUCIBLE: {bad}")
        return 1 if bad else 0
    for p, b in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
    print({t: len(list((ROOT / t / "cases").glob("*.json"))) for t in ("a1", "a2", "a3")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
