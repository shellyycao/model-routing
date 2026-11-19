"""Deterministic validator for the ANALYSIS stage.

Input: the findings.json produced by executing the model's analysis code in the sandbox. It must
be a flat JSON object mapping every required metric_key (ProjectSpec.analysis_questions) to a
finite number. Extra keys are allowed and ignored.

Reference values
- Default: the project's ground truth (canonical cleaned data -> trusted reference analysis);
  quality_basis = "ground_truth".
- Optional `reference_metrics`: an alternative reference, typically the trusted reference
  analysis recomputed on the ACTUAL upstream cleaned file (see `conditional_reference_metrics`).
  This separates the analysis stage's own errors from upstream error propagation;
  quality_basis = "conditional_reference". (The field exists from contracts v1.1; on v1.0 the
  kwarg is ignored by pydantic.)

Mandatory checks: findings_exists, findings_parses, required_keys_present, values_numeric,
values_within_tolerance.
Quality metrics:
  numerical_accuracy    fraction of required keys whose value is within tolerance of the reference
  calculation_coverage  fraction of required keys present with a finite numeric value
  reproducibility       ONLY when a second execution's findings are supplied: fraction of required
                        keys on which the two executions agree within the key's tolerance (both must
                        be numeric). Omitted otherwise - never estimated.
Tolerance for a key: |actual - expected| <= max(abs_tolerance, rel_tolerance * |expected|), using the
key's AnalysisQuestion tolerances.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from src.contracts import CheckResult, StageId, ValidationResult

from .cleaning import load_project

VALIDATOR_VERSION = "1.0"
_MANDATORY = ["findings_exists", "findings_parses", "required_keys_present", "values_numeric",
              "values_within_tolerance"]


def within_tolerance(actual: float, expected: float, abs_tol: float, rel_tol: float) -> bool:
    return abs(actual - expected) <= max(abs_tol, rel_tol * abs(expected)) + 1e-12


def _num(v: Any) -> float | None:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v) if math.isfinite(v) else None


def _load(findings: dict | str | Path | None) -> tuple[dict | None, str]:
    """-> (dict or None, error). A str/Path is a file path."""
    if findings is None:
        return None, "missing"
    if isinstance(findings, dict):
        return findings, ""
    p = Path(findings)
    if not p.is_file():
        return None, "missing"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return None, f"invalid JSON: {e}"
    if not isinstance(obj, dict):
        return None, f"top level is {type(obj).__name__}, expected a JSON object"
    return obj, ""


def conditional_reference_metrics(project_dir: str | Path, cleaned_csv: str | Path) -> dict[str, float] | None:
    """Run the project's TRUSTED reference analysis on an actual upstream cleaned file.

    Returns None when the trusted analysis cannot run on that file (e.g. missing columns or
    unparseable values) - in that case no conditional reference exists.
    """
    from datasets.generate import project_module  # local import: datasets is a sibling package

    spec, _, _ = load_project(project_dir)
    try:
        return project_module(spec.project_id).reference_analysis(Path(cleaned_csv))
    except Exception:  # noqa: BLE001 - any failure means "no conditional reference available"
        return None


def validate_analysis(findings: dict | str | Path | None, project_dir: str | Path,
                      second_findings: dict | str | Path | None = None,
                      reference_metrics: dict[str, float] | None = None) -> ValidationResult:
    spec, gt, _ = load_project(project_dir)
    tol = gt["analysis"]["tolerances"]
    required = [k for q in spec.analysis_questions for k in q.metric_keys]
    basis = "ground_truth" if reference_metrics is None else "conditional_reference"
    expected = gt["analysis"]["metrics"] if reference_metrics is None else reference_metrics
    checks: list[CheckResult] = []
    quality: dict[str, float] = {"numerical_accuracy": 0.0, "calculation_coverage": 0.0}

    def result() -> ValidationResult:
        return ValidationResult(stage=StageId.ANALYSIS, hard_pass=all(c.passed for c in checks if c.mandatory),
                                checks=checks, quality=quality, validator_version=VALIDATOR_VERSION,
                                quality_basis=basis)

    obj, err = _load(findings)
    checks.append(CheckResult(name="findings_exists", passed=err != "missing", mandatory=True,
                              detail="findings.json not found" if err == "missing" else ""))
    if obj is None:
        if err != "missing":
            checks.append(CheckResult(name="findings_parses", passed=False, mandatory=True, detail=err[:500]))
        for n in _MANDATORY:
            if n not in {c.name for c in checks}:
                checks.append(CheckResult(name=n, passed=False, mandatory=True, detail="no parseable findings"))
        return result()
    checks.append(CheckResult(name="findings_parses", passed=True, mandatory=True))

    missing = [k for k in required if k not in obj]
    non_numeric = [k for k in required if k in obj and _num(obj[k]) is None]
    wrong = []
    correct = 0
    for k in required:
        v = _num(obj.get(k))
        e = expected.get(k)
        if v is not None and e is not None and within_tolerance(v, float(e), tol[k]["abs"], tol[k]["rel"]):
            correct += 1
        elif v is not None:
            wrong.append(f"{k}={v!r} (expected {e!r})")
    checks.append(CheckResult(name="required_keys_present", passed=not missing, mandatory=True,
                              detail=f"missing {missing}" if missing else f"all {len(required)} present"))
    checks.append(CheckResult(name="values_numeric", passed=not non_numeric and not missing, mandatory=True,
                              detail=f"non-numeric {non_numeric}" if non_numeric else ""))
    checks.append(CheckResult(name="values_within_tolerance", passed=correct == len(required), mandatory=True,
                              detail="; ".join(wrong[:8]) or (f"{correct}/{len(required)} correct"),
                              value=correct / len(required)))
    quality["numerical_accuracy"] = correct / len(required)
    quality["calculation_coverage"] = sum(_num(obj.get(k)) is not None for k in required) / len(required)

    if second_findings is not None:
        obj2, err2 = _load(second_findings)
        agree = 0
        if obj2 is not None:
            for k in required:
                a, b = _num(obj.get(k)), _num(obj2.get(k))
                if a is not None and b is not None and within_tolerance(b, a, tol[k]["abs"], tol[k]["rel"]):
                    agree += 1
        quality["reproducibility"] = agree / len(required)
        checks.append(CheckResult(name="reproducible_across_executions", passed=agree == len(required),
                                  mandatory=False, detail=err2 or f"{agree}/{len(required)} keys agree",
                                  value=agree / len(required)))
    return result()
