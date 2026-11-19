"""Deterministic validator for the CLEANING stage.

Compares a cleaned CSV (produced in the sandbox) to the project's canonical cleaned CSV, which
was produced by trusted reference code (datasets/). Everything is read as text with the stdlib
csv module, so the verdict does not depend on pandas' type inference.

Mandatory checks (gate feasibility):
  output_exists, output_parses, required_columns_present, schema_constraints,
  no_duplicate_keys, row_set_matches_reference, values_match_reference
Quality metrics (src.contracts.QUALITY_METRICS[CLEANING]), all in [0, 1]:
  cleaning_correctness  matched cells / (|union of row keys| x |schema columns|); a missing or extra
                        row counts as all-mismatched cells.
  data_integrity        |K_out & K_ref| / (n_output_rows + |K_ref - K_out|): 1 iff the output has
                        exactly the reference rows with no duplicates.
  schema_compliance     fraction of individual schema constraints satisfied (per column: present,
                        dtype, nullability, allowed values, min, max; plus "no extra columns").
"""

from __future__ import annotations

import csv
import json
import math
import re
from datetime import date
from pathlib import Path

from src.contracts import CheckResult, ColumnSpec, ProjectSpec, StageId, ValidationResult

VALIDATOR_VERSION = "1.0"
_MISSING = {"", "nan", "none", "null", "na", "n/a", "nat"}
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MAX_EXAMPLES = 5


def load_project(project_dir: str | Path) -> tuple[ProjectSpec, dict, Path]:
    """Load (spec, ground_truth, project_dir) for a project directory."""
    pdir = Path(project_dir)
    spec = ProjectSpec.model_validate_json((pdir / "project.json").read_text(encoding="utf-8"))
    gt = json.loads((pdir / spec.ground_truth_file).read_text(encoding="utf-8"))
    return spec, gt, pdir


def _is_missing(v: str | None) -> bool:
    return v is None or v.strip().lower() in _MISSING


def _to_float(v: str) -> float | None:
    try:
        x = float(v.strip().replace(",", ""))
    except (ValueError, AttributeError):
        return None
    return x if math.isfinite(x) else None


def _to_date(v: str) -> date | None:
    s = v.strip()
    if not _ISO_DATE.match(s):
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _parses_as(v: str, dtype: str) -> bool:
    if dtype in ("str", "category"):
        return True
    if dtype == "float":
        return _to_float(v) is not None
    if dtype == "int":
        x = _to_float(v)
        return x is not None and x == math.floor(x)
    if dtype == "date":
        return _to_date(v) is not None
    if dtype == "bool":
        return v.strip().lower() in {"true", "false", "1", "0"}
    return False


def _read(path: Path) -> tuple[list[str], list[list[str]]]:
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        raise ValueError("empty file (no header)")
    # Excel and some CSV writers prefix the first header with a UTF-8 BOM. It is
    # encoding metadata, not part of the column name.
    header = [h.strip().lstrip("\ufeff") for h in rows[0]]
    body = [r for r in rows[1:] if r]   # tolerate blank trailing lines
    bad = [i + 2 for i, r in enumerate(body) if len(r) != len(header)]
    if bad:
        raise ValueError(f"{len(bad)} rows have a different field count than the header (lines {bad[:5]})")
    return header, body


def _schema_units(col: ColumnSpec, values: list[str] | None) -> list[tuple[str, bool, str]]:
    """Individual schema constraints for one column -> [(name, passed, detail)]."""
    n = col.name
    if values is None:
        units = [(f"{n}:present", False, "column missing")]
        units += [(f"{n}:{k}", False, "column missing") for k in ("dtype", "nullable")]
        if col.allowed_values is not None:
            units.append((f"{n}:allowed_values", False, "column missing"))
        if col.min_value is not None:
            units.append((f"{n}:min", False, "column missing"))
        if col.max_value is not None:
            units.append((f"{n}:max", False, "column missing"))
        return units
    present = [v for v in values if not _is_missing(v)]
    bad_type = [v for v in present if not _parses_as(v, col.dtype)]
    units = [(f"{n}:present", True, ""),
             (f"{n}:dtype", not bad_type, f"{len(bad_type)} values not {col.dtype}, e.g. {bad_type[:3]}" if bad_type else ""),
             (f"{n}:nullable", col.nullable or len(present) == len(values),
              "" if col.nullable or len(present) == len(values) else f"{len(values) - len(present)} missing values")]
    if col.allowed_values is not None:
        bad = sorted({v.strip() for v in present} - set(col.allowed_values))
        units.append((f"{n}:allowed_values", not bad, f"unexpected values {bad[:5]}" if bad else ""))
    nums = [x for x in (_to_float(v) for v in present) if x is not None] if col.dtype in ("int", "float") else []
    if col.min_value is not None:
        below = [x for x in nums if x < col.min_value]
        units.append((f"{n}:min", not below, f"{len(below)} values < {col.min_value}" if below else ""))
    if col.max_value is not None:
        above = [x for x in nums if x > col.max_value]
        units.append((f"{n}:max", not above, f"{len(above)} values > {col.max_value}" if above else ""))
    return units


def _cell_equal(a: str, b: str, dtype: str, abs_tol: float, rel_tol: float) -> bool:
    """a = output cell, b = reference cell."""
    if _is_missing(b) or _is_missing(a):
        return _is_missing(a) and _is_missing(b)
    if dtype in ("int", "float"):
        x, y = _to_float(a), _to_float(b)
        return x is not None and y is not None and abs(x - y) <= max(abs_tol, rel_tol * abs(y)) + 1e-12
    if dtype == "date":
        x, y = _to_date(a), _to_date(b)
        return x is not None and x == y
    if dtype == "bool":
        return a.strip().lower() in {"true", "1"} if b.strip().lower() in {"true", "1"} else a.strip().lower() in {"false", "0"}
    return a.strip() == b.strip()


def _fail_all(checks: list[CheckResult], names: list[str], reason: str) -> None:
    done = {c.name for c in checks}
    checks.extend(CheckResult(name=n, passed=False, mandatory=True, detail=reason) for n in names if n not in done)


_MANDATORY = ["output_exists", "output_parses", "required_columns_present", "schema_constraints",
              "no_duplicate_keys", "row_set_matches_reference", "values_match_reference"]


def validate_cleaning(output_csv: str | Path | None, project_dir: str | Path) -> ValidationResult:
    spec, gt, pdir = load_project(project_dir)
    key = gt["cleaning"]["key_column"]
    abs_tol = float(gt["cleaning"]["value_abs_tolerance"])
    rel_tol = float(gt["cleaning"]["value_rel_tolerance"])
    schema = spec.cleaned_schema
    checks: list[CheckResult] = []
    zero = {"cleaning_correctness": 0.0, "data_integrity": 0.0, "schema_compliance": 0.0}

    def result() -> ValidationResult:
        return ValidationResult(stage=StageId.CLEANING, hard_pass=all(c.passed for c in checks if c.mandatory),
                                checks=checks, quality=quality, validator_version=VALIDATOR_VERSION,
                                quality_basis="ground_truth")

    quality = dict(zero)
    path = Path(output_csv) if output_csv else None
    if path is None or not path.is_file():
        checks.append(CheckResult(name="output_exists", passed=False, mandatory=True,
                                  detail=f"cleaned CSV not found: {output_csv}"))
        _fail_all(checks, _MANDATORY, "no output")
        return result()
    checks.append(CheckResult(name="output_exists", passed=True, mandatory=True, detail=str(path)))
    try:
        header, body = _read(path)
    except (ValueError, UnicodeDecodeError, csv.Error) as e:
        checks.append(CheckResult(name="output_parses", passed=False, mandatory=True, detail=str(e)[:500]))
        _fail_all(checks, _MANDATORY, "output does not parse")
        return result()
    checks.append(CheckResult(name="output_parses", passed=True, mandatory=True,
                              detail=f"{len(body)} rows, {len(header)} columns"))

    ref_header, ref_body = _read(pdir / spec.canonical_cleaned_file)
    idx = {h: i for i, h in enumerate(header)}   # first occurrence wins for duplicated headers
    ridx = {h: i for i, h in enumerate(ref_header)}

    # --- schema
    required = [c.name for c in schema]
    missing_cols = [c for c in required if c not in idx]
    extra_cols = [h for h in header if h not in required]
    checks.append(CheckResult(name="required_columns_present", passed=not missing_cols, mandatory=True,
                              detail=f"missing {missing_cols}" if missing_cols else "all present"))
    units: list[tuple[str, bool, str]] = []
    for col in schema:
        values = [r[idx[col.name]] for r in body] if col.name in idx else None
        units.extend(_schema_units(col, values))
    units.append(("no_extra_columns", not extra_cols, f"extra columns {extra_cols}" if extra_cols else ""))
    failed_units = [u for u in units if not u[1] and u[0] != "no_extra_columns"]
    checks.append(CheckResult(
        name="schema_constraints", passed=not failed_units, mandatory=True,
        detail="; ".join(f"{n}: {d}" for n, _, d in failed_units[:_MAX_EXAMPLES]) or "all constraints satisfied",
        value=sum(u[1] for u in units) / len(units)))
    checks.append(CheckResult(name="no_extra_columns", passed=not extra_cols, mandatory=False,
                              detail=f"extra columns {extra_cols}" if extra_cols else ""))
    quality["schema_compliance"] = sum(u[1] for u in units) / len(units)

    # --- rows
    if key not in idx:
        _fail_all(checks, _MANDATORY, f"key column '{key}' missing")
        return result()
    out_keys = [r[idx[key]].strip() for r in body]
    seen: dict[str, list[str]] = {}
    dups = 0
    for k, r in zip(out_keys, body):
        if k in seen:
            dups += 1
        else:
            seen[k] = r
    checks.append(CheckResult(name="no_duplicate_keys", passed=dups == 0, mandatory=True,
                              detail=f"{dups} rows repeat an existing {key}" if dups else "", value=float(dups)))
    ref_rows = {r[ridx[key]].strip(): r for r in ref_body}
    k_out, k_ref = set(seen), set(ref_rows)
    missing_rows, extra_rows = sorted(k_ref - k_out), sorted(k_out - k_ref)
    checks.append(CheckResult(
        name="row_set_matches_reference", passed=not missing_rows and not extra_rows, mandatory=True,
        detail=(f"{len(missing_rows)} reference rows missing (e.g. {missing_rows[:_MAX_EXAMPLES]}); "
                f"{len(extra_rows)} unexpected rows (e.g. {extra_rows[:_MAX_EXAMPLES]}); "
                f"output rows={len(body)}, reference rows={len(ref_rows)}")))
    quality["data_integrity"] = len(k_out & k_ref) / (len(body) + len(k_ref - k_out)) if (body or k_ref) else 1.0

    # --- values (first occurrence of each key)
    mism: dict[str, list[str]] = {}
    matched = 0
    common = k_out & k_ref
    for k in sorted(common):
        out_r, ref_r = seen[k], ref_rows[k]
        for col in schema:
            if col.name in idx and _cell_equal(out_r[idx[col.name]], ref_r[ridx[col.name]], col.dtype, abs_tol, rel_tol):
                matched += 1
            else:
                mism.setdefault(col.name, []).append(k)
    n_cells_common = len(common) * len(schema)
    union = len(k_out | k_ref)
    quality["cleaning_correctness"] = matched / (union * len(schema)) if union else 1.0
    detail = "; ".join(f"{c}: {len(ks)} mismatches (e.g. {ks[:3]})" for c, ks in mism.items())
    checks.append(CheckResult(
        name="values_match_reference", passed=not mism and bool(common or not k_ref), mandatory=True,
        detail=detail or f"{matched}/{n_cells_common} cells match (abs_tol={abs_tol}, rel_tol={rel_tol})",
        value=matched / n_cells_common if n_cells_common else 0.0))
    return result()
