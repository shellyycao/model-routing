"""Shared, deterministic helpers for project generators and reference solutions.

Design notes
- Randomness comes only from `random.Random(seed)` (stdlib; stable across Python versions for
  `random()`, `randint`, `choice`, `shuffle`, `sample`).
- Reference cleaning/analysis use only the stdlib (csv, math.fsum, statistics), so the ground
  truth does not depend on the pandas/numpy version installed on the host or in the sandbox.
- All files are written with explicit encodings, "\n" line endings and sorted JSON keys so the
  output is byte-reproducible.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from datetime import date
from pathlib import Path
from typing import Iterable

GENERATOR_VERSION = "2.0"

# Tokens treated as missing in raw files (compared case-insensitively after stripping).
MISSING_TOKENS: tuple[str, ...] = ("", "na", "n/a", "null", "none", "-")

MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December")
MONTH_ABBR = tuple(m[:3] for m in MONTHS)

# Date formats that may appear in raw files. Rendering is done here (not with strftime) so it
# is locale-independent. Keys are the format names used in project cleaning requirements.
DATE_FORMATS: dict[str, str] = {
    "iso": "YYYY-MM-DD (e.g. 2024-03-05)",
    "us_slash": "MM/DD/YYYY (e.g. 03/05/2024; month first)",
    "dmy_abbr": "DD-Mon-YYYY (e.g. 05-Mar-2024; English month abbreviation)",
    "ymd_slash": "YYYY/MM/DD (e.g. 2024/03/05)",
    "long": "Month D, YYYY (e.g. March 5, 2024; full English month name)",
}


def render_date(d: date, fmt: str) -> str:
    if fmt == "iso":
        return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
    if fmt == "us_slash":
        return f"{d.month:02d}/{d.day:02d}/{d.year:04d}"
    if fmt == "dmy_abbr":
        return f"{d.day:02d}-{MONTH_ABBR[d.month - 1]}-{d.year:04d}"
    if fmt == "ymd_slash":
        return f"{d.year:04d}/{d.month:02d}/{d.day:02d}"
    if fmt == "long":
        return f"{MONTHS[d.month - 1]} {d.day}, {d.year:04d}"
    raise ValueError(fmt)


_RE_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_RE_US = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
_RE_DMY = re.compile(r"^(\d{2})-([A-Za-z]{3})-(\d{4})$")
_RE_YMD = re.compile(r"^(\d{4})/(\d{2})/(\d{2})$")
_RE_LONG = re.compile(r"^([A-Za-z]+) (\d{1,2}), (\d{4})$")


def parse_date(text: str | None) -> date | None:
    """Parse one of the DATE_FORMATS. Returns None for missing/unparseable/impossible dates."""
    if text is None:
        return None
    s = text.strip()
    try:
        if m := _RE_ISO.match(s):
            return date(int(m[1]), int(m[2]), int(m[3]))
        if m := _RE_US.match(s):
            return date(int(m[3]), int(m[1]), int(m[2]))
        if m := _RE_DMY.match(s):
            abbr = [a.lower() for a in MONTH_ABBR]
            if m[2].lower() not in abbr:
                return None
            return date(int(m[3]), abbr.index(m[2].lower()) + 1, int(m[1]))
        if m := _RE_YMD.match(s):
            return date(int(m[1]), int(m[2]), int(m[3]))
        if m := _RE_LONG.match(s):
            names = [n.lower() for n in MONTHS]
            if m[1].lower() not in names:
                return None
            return date(int(m[3]), names.index(m[1].lower()) + 1, int(m[2]))
    except ValueError:
        return None
    return None


def is_missing(value: str | None) -> bool:
    return value is None or value.strip().lower() in MISSING_TOKENS


def parse_number(text: str | None, strip: Iterable[str] = ()) -> float | None:
    """Parse a number after removing the given substrings and whitespace; None if invalid."""
    if is_missing(text):
        return None
    s = text.strip()
    for token in strip:
        s = s.replace(token, "")
    s = s.strip()
    if not re.fullmatch(r"[-+]?(\d+(\.\d*)?|\.\d+)", s):
        return None
    v = float(s)
    return v if math.isfinite(v) else None


def fmt_num(x: float, decimals: int = 2) -> str:
    """Deterministic fixed-point formatting used in canonical CSVs."""
    out = f"{x:.{decimals}f}"
    return "0." + "0" * decimals if out.startswith("-") and float(out) == 0 else out


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    w.writerow(header)
    w.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8", newline="")


def read_csv_text(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a CSV as text only (no type inference)."""
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = [dict(r) for r in reader]
        return list(reader.fieldnames or []), rows


def dump_json(obj, path: Path) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def r6(x: float) -> float:
    """Round metric values for stable serialisation (well inside every tolerance)."""
    v = round(float(x), 6)
    return 0.0 if v == 0 else v


MISSING_RENDERINGS = ("", "NA", "N/A", "null", "None", "-")


def missing_token(rng) -> str:
    """A random textual rendering of a missing value (all are listed in MISSING_TOKENS)."""
    return rng.choice(MISSING_RENDERINGS)


def whole_number(x: float | None, lo: float, hi: float) -> int | None:
    """int(x) if x is a whole number within [lo, hi], else None."""
    if x is None or x != math.floor(x) or not (lo <= x <= hi):
        return None
    return int(x)
