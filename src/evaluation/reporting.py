"""Deterministic validator for the REPORTING stage (no LLM judge).

The report (ReportOutput) is checked against VERIFIED findings: the findings.json produced in the
sandbox by the analysis stage (in Experiment A, the canonical findings). quality_basis is
"ground_truth" when those are the canonical findings, else the caller passes
"conditional_reference" (field exists from contracts v1.1; ignored on v1.0).

Mandatory checks include report parsing, one structured finding for every required question, every
required metric key under its own finding, correct values, directions, rankings and declared derived
values, and no numeric value attributed to the wrong finding. Unsupported numeric commentary is a
quality metric with an advisory threshold; it is not a hard failure. Word limit, evidence refs and
the unsupported-claim threshold are non-mandatory checks.

Quality metrics
  numerical_consistency   matched reported_values / all reported_values (omitted if there are none)
  finding_coverage        present required finding_ids / required finding_ids.
  unsupported_claim_count numeric claims matching no verified value, valid declared derivation, or
                          supplied verified cleaning-log count.

NUMBER MATCHING RULE (stated value s vs verified value v)
  s matches v if  |s - v| <= max(abs_tol, rel_tol * |v|)   (the metric's analysis tolerance), or
  if s is consistent with v at the precision s is written in, i.e.
     |s - v| <= 0.5 * unit(s)  AND  |s - v| <= 1% of |v|,
  where unit(s) is the place value of the last written digit times any scale suffix (e.g. "10.08%"
  -> 0.01; "$445K" -> 1,000; "1.23 million" -> 10,000; "520" -> 10 because trailing zeros of an
  integer are treated as rounding). The 1% cap means coarse rounding ("$1M" for 1,234,567) is
  never accepted. For text, matching is sign-insensitive ("fell 5.2%" vs -5.2); reported_values
  are matched with sign. A text number is "supported" if it matches ANY verified value.

WHAT COUNTS AS A NUMERIC CLAIM
  Every number in title, executive_summary, finding statements, limitations and conclusion. Structured
  reported_values and derived_values have their own hard checks. Not counted: digits inside identifiers
  (Q1, revenue_2024_q1, R100001),
  ISO / slash dates, and "context numbers" that appear in the project objective or analysis
  question texts or metric keys (e.g. the years 2023/2024, the 20% discount threshold, quarter numbers).

KNOWN LIMITS (documented, not hidden)
  - Numbers written as words ("twelve") are not detected.
  - Free-text numbers in summaries and limitations are not tied to a particular finding; structured
    `reported_values` remain the authoritative attribution check.
"""

from __future__ import annotations

import math
import re

from pydantic import ValidationError

from src.contracts import CheckResult, ProjectSpec, ReportOutput, StageId, ValidationResult

VALIDATOR_VERSION = "2.0"
ROUNDING_REL_CAP = 0.01
DEFAULT_MAX_UNSUPPORTED_CLAIMS = 2

_SCALE = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6, "b": 1e9, "bn": 1e9, "billion": 1e9}
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{4}/\d{2}/\d{2}\b")
_NUM_RE = re.compile(
    r"(?<![\w.])(?P<sign>[-+−]?)(?:US)?\$?\s?(?P<int>\d{1,3}(?:,\d{3})+|\d+)(?P<frac>\.\d+)?"
    r"(?:\s?(?P<suffix>%|percent\b|[kKmMbB]\b|bn\b|thousand\b|million\b|billion\b))?(?![\w])")


class NumericClaim:
    __slots__ = ("text", "value", "unit")

    def __init__(self, text: str, value: float, unit: float):
        self.text, self.value, self.unit = text, value, unit

    def __repr__(self) -> str:
        return f"NumericClaim({self.text!r}, {self.value}, unit={self.unit})"


def extract_numbers(text: str) -> list[NumericClaim]:
    """Numeric claims in free text (dates and identifier digits are skipped)."""
    text = _DATE_RE.sub(" ", text or "")
    out = []
    for m in _NUM_RE.finditer(text):
        int_part = m["int"].replace(",", "")
        frac = m["frac"] or ""
        suffix = (m["suffix"] or "").lower()
        scale = _SCALE.get(suffix, 1.0)
        value = float(int_part + frac) * scale
        if m["sign"] in ("-", "−"):
            value = -value
        if frac:
            unit = 10.0 ** -(len(frac) - 1)
        else:
            tz = len(int_part) - len(int_part.rstrip("0")) if int_part.strip("0") else 0
            unit = 10.0 ** tz
        out.append(NumericClaim(m.group(0).strip(), value, unit * scale))
    return out


def _float_unit(x: float) -> float:
    """Precision implied by a float's shortest repr (12.3 -> 0.1; 1230000.0 -> 10000)."""
    s = repr(float(x))
    if "e" in s or "E" in s:
        return 0.0
    i, _, f = s.partition(".")
    f = f.rstrip("0")
    if f:
        return 10.0 ** -len(f)
    i = i.lstrip("-")
    tz = len(i) - len(i.rstrip("0")) if i.strip("0") else 0
    return 10.0 ** tz


def number_matches(stated: float, verified: float, unit: float, abs_tol: float, rel_tol: float) -> bool:
    diff = abs(stated - verified)
    if diff <= max(abs_tol, rel_tol * abs(verified)) + 1e-9:
        return True
    return diff <= 0.5 * unit + 1e-9 and diff <= ROUNDING_REL_CAP * abs(verified) + 1e-9


def _context_numbers(spec: ProjectSpec) -> set[float]:
    """Every number written in the objective, question texts and metric keys (including digits
    inside identifiers such as churn_rate_cohort_2021_pct -> 2021)."""
    texts = [spec.objective] + [q.question for q in spec.analysis_questions]
    texts += [k for q in spec.analysis_questions for k in q.metric_keys]
    return {float(m) for t in texts for m in re.findall(r"\d+(?:\.\d+)?", t)}


def _expected_direction(value: float, abs_tol: float, rel_tol: float) -> str:
    zero_tol = max(abs_tol, rel_tol * abs(value))
    if abs(value) <= zero_tol:
        return "no_change"
    return "increase" if value > 0 else "decrease"


def _derived_value(kind: str, a: float, b: float) -> float | None:
    if kind == "difference":
        return a - b
    if b == 0:
        return None
    if kind == "ratio":
        return a / b
    if kind == "pct_change":
        return (a - b) / b * 100
    if kind == "share":
        return a / b * 100
    return None


def validate_reporting(report: ReportOutput | dict | str, verified_findings: dict[str, float],
                       spec: ProjectSpec, *, max_unsupported_claims: int = DEFAULT_MAX_UNSUPPORTED_CLAIMS,
                       quality_basis: str = "ground_truth",
                       cleaning_counts: dict[str, int | float] | None = None) -> ValidationResult:
    checks: list[CheckResult] = []
    quality: dict[str, float] = {}

    def result() -> ValidationResult:
        return ValidationResult(stage=StageId.REPORTING, hard_pass=all(c.passed for c in checks if c.mandatory),
                                checks=checks, quality=quality, validator_version=VALIDATOR_VERSION,
                                quality_basis=quality_basis)

    try:
        rep = report if isinstance(report, ReportOutput) else (
            ReportOutput.model_validate_json(report) if isinstance(report, str) else ReportOutput.model_validate(report))
    except (ValidationError, ValueError) as e:
        checks.append(CheckResult(name="report_valid", passed=False, mandatory=True, detail=str(e)[:500]))
        for n in ("required_findings_covered", "required_metric_keys_present",
                  "reported_values_consistent", "directions_correct", "rankings_correct",
                  "derived_values_correct", "finding_statements_substantive",
                  "prose_claims_consistent", "numeric_attribution_correct"):
            checks.append(CheckResult(name=n, passed=False, mandatory=True, detail="report invalid"))
        quality["finding_coverage"] = 0.0
        return result()
    checks.append(CheckResult(name="report_valid", passed=True, mandatory=True))

    tol: dict[str, tuple[float, float]] = {k: (q.abs_tolerance, q.rel_tolerance)
                                           for q in spec.analysis_questions for k in q.metric_keys}
    q_by_id = {q.question_id: q for q in spec.analysis_questions}
    q_keys = {q.question_id: set(q.metric_keys) for q in spec.analysis_questions}
    verified: dict[str, float] = {k: float(v) for k, v in verified_findings.items()
                                  if not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v)}

    by_finding: dict[str, list] = {}
    for kf in rep.key_findings:
        by_finding.setdefault(kf.finding_id, []).append(kf)

    # --- coverage and required structured values
    required = spec.reporting.required_finding_ids
    covered = [fid for fid in required if by_finding.get(fid)]
    uncovered = [f for f in required if f not in covered]
    quality["finding_coverage"] = len(covered) / len(required) if required else 1.0
    checks.append(CheckResult(name="required_findings_covered", passed=not uncovered, mandatory=True,
                              detail=f"not covered: {uncovered}" if uncovered else f"{len(covered)}/{len(required)}",
                              value=quality["finding_coverage"]))

    missing_metric_keys: list[str] = []
    wrong_group_keys: list[str] = []
    for fid in required:
        expected = q_keys.get(fid, set())
        supplied = {k for kf in by_finding.get(fid, []) for k in kf.reported_values}
        missing_metric_keys += [f"{fid}.{k}" for k in sorted(expected - supplied)]
        wrong_group_keys += [f"{fid}.{k}" for k in sorted(supplied - expected)]
    checks.append(CheckResult(
        name="required_metric_keys_present", passed=not missing_metric_keys and not wrong_group_keys,
        mandatory=True,
        detail=(f"missing {missing_metric_keys[:12]}; wrong finding/group {wrong_group_keys[:12]}"
                if missing_metric_keys or wrong_group_keys else "every required metric key reported in its finding")))

    # --- reported values vs verified findings, per key and finding
    pairs = [(kf.finding_id, k, v) for kf in rep.key_findings for k, v in kf.reported_values.items()]
    bad = []
    for fid, k, v in pairs:
        if k not in q_keys.get(fid, set()):
            bad.append(f"{fid}.{k}={v} (key belongs to another finding or is unknown)")
            continue
        if k not in verified:
            bad.append(f"{fid}.{k}={v} (no verified finding with this key)")
            continue
        a, r = tol.get(k, (1e-6, 1e-4))
        if not (math.isfinite(v) and number_matches(v, verified[k], _float_unit(v), a, r)):
            bad.append(f"{fid}.{k}={v} (verified {verified[k]})")
    if pairs:
        quality["numerical_consistency"] = (len(pairs) - len(bad)) / len(pairs)
    checks.append(CheckResult(name="reported_values_consistent", passed=bool(pairs) and not bad, mandatory=True,
                              detail="; ".join(bad[:8]) or ("no reported values" if not pairs else "all consistent"),
                              value=quality.get("numerical_consistency")))

    # --- structured direction and ranking claims
    bad_directions: list[str] = []
    bad_rankings: list[str] = []
    for fid in required:
        q = q_by_id.get(fid)
        findings = by_finding.get(fid, [])
        if q is None or not findings:
            continue
        if q.direction_key:
            if q.direction_key not in verified:
                bad_directions.append(f"{fid}: direction key {q.direction_key!r} missing")
            else:
                a, r = tol[q.direction_key]
                expected = _expected_direction(verified[q.direction_key], a, r)
                actual = [kf.direction for kf in findings]
                if actual != [expected] * len(findings):
                    bad_directions.append(f"{fid}: stated {actual}, expected {expected}")
        if q.ranking_labels:
            missing = [k for k in q.ranking_labels if k not in verified]
            if missing:
                bad_rankings.append(f"{fid}: ranking keys missing {missing}")
            else:
                expected = [q.ranking_labels[k] for k in sorted(
                    q.ranking_labels, key=lambda k: (-verified[k], q.ranking_labels[k]))]
                label_to_key = {label: key for key, label in q.ranking_labels.items()}
                for kf in findings:
                    actual = kf.ranking
                    valid_set = actual is not None and len(actual) == len(expected) and set(actual) == set(expected)
                    ordered = bool(valid_set)
                    if valid_set:
                        for left, right in zip(actual, actual[1:]):
                            lk, rk = label_to_key[left], label_to_key[right]
                            a, r = tol.get(lk, (1e-6, 1e-4))
                            tie_tol = max(a, r * max(abs(verified[lk]), abs(verified[rk])))
                            if verified[lk] + tie_tol < verified[rk]:
                                ordered = False
                                break
                    if not ordered:
                        bad_rankings.append(f"{fid}: stated {actual}, expected descending values like {expected}")
    checks.append(CheckResult(name="directions_correct", passed=not bad_directions, mandatory=True,
                              detail="; ".join(bad_directions[:8]) or "all required directions correct"))
    checks.append(CheckResult(name="rankings_correct", passed=not bad_rankings, mandatory=True,
                              detail="; ".join(bad_rankings[:8]) or "all required rankings correct"))

    # --- declared derived values
    bad_derived: list[str] = []
    valid_derived: dict[int, list[float]] = {}
    valid_derived_by_key: dict[tuple[int, str], list[float]] = {}
    for i, kf in enumerate(rep.key_findings):
        allowed = q_keys.get(kf.finding_id, set())
        for j, dv in enumerate(kf.derived_values):
            where = f"{kf.finding_id}.derived_values[{j}]"
            if (len(dv.operands) != 2 or any(k not in verified for k in dv.operands)
                    or not any(k in allowed for k in dv.operands)):
                bad_derived.append(f"{where}: operands must be verified and include a key from this finding")
                continue
            expected = _derived_value(dv.kind, verified[dv.operands[0]], verified[dv.operands[1]])
            if expected is None or not math.isfinite(dv.value):
                bad_derived.append(f"{where}: undefined or non-finite")
                continue
            a = max(tol.get(k, (1e-6, 1e-4))[0] for k in dv.operands)
            r = max(tol.get(k, (1e-6, 1e-4))[1] for k in dv.operands)
            if not number_matches(dv.value, expected, _float_unit(dv.value), a, r):
                bad_derived.append(f"{where}={dv.value} (recomputed {expected})")
                continue
            valid_derived.setdefault(i, []).append(float(dv.value))
            for key in dv.operands:
                valid_derived_by_key.setdefault((i, key), []).append(float(dv.value))
    checks.append(CheckResult(name="derived_values_correct", passed=not bad_derived, mandatory=True,
                              detail="; ".join(bad_derived[:8]) or "all declared derived values recompute"))
    all_valid_derived = [v for values in valid_derived.values() for v in values]
    context = _context_numbers(spec)

    # Reject empty "See values" prose while allowing the concise summaries requested by the prompt.
    # The renderer separately exposes every authoritative structured value.
    unsubstantive: list[str] = []
    for i, kf in enumerate(rep.key_findings):
        if kf.finding_id not in required:
            continue
        keys = list(q_keys.get(kf.finding_id, set()))
        claims = extract_numbers(kf.statement)
        supported_claim = any(
            any(key in verified and (
                number_matches(claim.value, verified[key], claim.unit, *tol.get(key, (1e-6, 1e-4)))
                or number_matches(abs(claim.value), abs(verified[key]), claim.unit,
                                  *tol.get(key, (1e-6, 1e-4)))) for key in keys)
            or any(number_matches(abs(claim.value), abs(value), claim.unit, 1e-6, 1e-4)
                   for value in valid_derived.get(i, []))
            for claim in claims)
        if not supported_claim:
            unsubstantive.append(f"{kf.finding_id}: statement contains no supported numeric finding")
    checks.append(CheckResult(name="finding_statements_substantive", passed=not unsubstantive, mandatory=True,
                              detail="; ".join(unsubstantive[:8]) or "every statement has a supported numeric finding"))

    # Tie free-text numbers to nearby metric aliases. This catches self-contradictory reports whose
    # structured reported_values are correct but whose prose swaps values between keys/groups.
    labelled_attribution_errors: list[str] = []
    for i, kf in enumerate(rep.key_findings):
        q = q_by_id.get(kf.finding_id)
        if q is None:
            continue
        raw_occurrences: list[tuple[int, int, str]] = []
        display = q.ranking_labels or {}
        for key in q.metric_keys:
            aliases = {key, key.replace("_", " ")}
            if key in display:
                aliases.add(display[key])
                remainder = [part for part in key.split("_") if part.lower() != display[key].lower()]
                if remainder:
                    aliases.add(f"{display[key]} {' '.join(remainder)}")
                    natural = [part for part in remainder if part.lower() not in {"pct", "count", "cohort"}]
                    if natural:
                        aliases.add(f"{display[key]} {' '.join(natural)}")
            for alias in aliases:
                flexible = re.escape(alias).replace(r"\-", r"[-_\s]+").replace(r"\ ", r"[-_\s]+")
                pattern = re.compile(rf"(?<!\w){flexible}(?!\w)", re.IGNORECASE)
                raw_occurrences.extend((m.start(), m.end(), key) for m in pattern.finditer(kf.statement))
        # Prefer the longest overlapping alias ("off-peak" over its suffix "peak").
        occurrences = [occ for occ in raw_occurrences if not any(
            other[0] <= occ[0] and other[1] >= occ[1] and
            (other[1] - other[0]) > (occ[1] - occ[0])
            for other in raw_occurrences)]
        occurrences.sort()
        def check_claim(key: str, claim: NumericClaim, relation: str) -> None:
            if abs(claim.value) in context:
                return
            a, r = tol.get(key, (1e-6, 1e-4))
            own = (key in verified and
                   (number_matches(claim.value, verified[key], claim.unit, a, r)
                    or number_matches(abs(claim.value), abs(verified[key]), claim.unit, a, r)))
            derived_for_key = any(number_matches(
                abs(claim.value), abs(value), claim.unit, 1e-6, 1e-4)
                for value in valid_derived_by_key.get((i, key), []))
            if own or derived_for_key:
                return
            other_key = next((other for other in q.metric_keys
                              if other != key and other in verified and number_matches(
                                  abs(claim.value), abs(verified[other]), claim.unit,
                                  *tol.get(other, (1e-6, 1e-4)))), None)
            detail = f"matches {other_key!r}" if other_key else "matches no verified/derived value for that key"
            labelled_attribution_errors.append(
                f"{kf.finding_id}: number '{claim.text}' {relation} {key!r} {detail}")

        for start, end, key in occurrences:
            # Hard attribution is deliberately limited to machine-checkable adjacency. Natural
            # prose is authoritative through the validated structured fields rendered alongside it.
            suffix = kf.statement[end:]
            separator = re.match(r"\s*(?::|=|\b(?:was|is|were)\b)\s*", suffix, re.IGNORECASE)
            if separator:
                numeric = _NUM_RE.match(suffix[separator.end():])
                if numeric:
                    check_claim(key, extract_numbers(numeric.group(0))[0], "after")
            prefix = kf.statement[:start]
            numeric_matches = list(_NUM_RE.finditer(prefix))
            if numeric_matches:
                last = numeric_matches[-1]
                if not prefix[last.end():].strip():
                    check_claim(key, extract_numbers(last.group(0))[0], "before")

    checks.append(CheckResult(name="prose_claims_consistent",
                              passed=not labelled_attribution_errors,
                              mandatory=True,
                              detail="; ".join(labelled_attribution_errors[:10])
                              or "structured claims agree with prose"))

    # --- unsupported claims
    count_values = [float(v) for v in (cleaning_counts or {}).values()
                    if not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v)]

    def supported(value: float, unit: float, signed: bool, keys: set[str] | None = None,
                  extras: list[float] | None = None) -> bool:
        selected = verified.items() if keys is None else ((k, verified[k]) for k in keys if k in verified)
        for k, vv in selected:
            a, r = tol.get(k, (1e-6, 1e-4))
            if number_matches(value, vv, unit, a, r) or (not signed and number_matches(abs(value), abs(vv), unit, a, r)):
                return True
        for vv in (extras or []) + count_values:
            if number_matches(value, vv, unit, 1e-6, 1e-4) or (not signed and number_matches(abs(value), abs(vv), unit, 1e-6, 1e-4)):
                return True
        return False

    unsupported: list[str] = []
    fields: list[tuple[str, str, int | None]] = [("title", rep.title, None),
                                                ("executive_summary", rep.executive_summary, None),
                                                ("conclusion", rep.conclusion, None)]
    fields += [(f"key_findings[{i}].statement", kf.statement, i) for i, kf in enumerate(rep.key_findings)]
    fields += [(f"limitations[{i}]", t, None) for i, t in enumerate(rep.limitations)]
    n_claims = 0
    wrong_attribution: list[str] = []
    for where, text, finding_i in fields:
        for c in extract_numbers(text):
            if abs(c.value) in context:
                continue
            n_claims += 1
            keys = None if finding_i is None else q_keys.get(rep.key_findings[finding_i].finding_id, set())
            extras = all_valid_derived if finding_i is None else valid_derived.get(finding_i, [])
            if supported(c.value, c.unit, signed=False, keys=keys, extras=extras):
                continue
            # A real finding value placed under another finding is a factual attribution error.
            if finding_i is not None and supported(c.value, c.unit, signed=False):
                wrong_attribution.append(f"{where}: '{c.text}' matches another finding")
            else:
                unsupported.append(f"{where}: '{c.text}'")
    quality["unsupported_claim_count"] = float(len(unsupported))
    checks.append(CheckResult(
        name="numeric_attribution_correct", passed=not wrong_attribution, mandatory=True,
        detail="; ".join(wrong_attribution[:10]) or "all finding numbers belong to their finding"))
    checks.append(CheckResult(
        name="unsupported_claims_within_threshold", passed=len(unsupported) <= max_unsupported_claims,
        mandatory=False,
        detail=("; ".join(unsupported[:10]) or "none") + f" ({n_claims} numeric claims checked)",
        value=float(len(unsupported))))

    # --- non-mandatory
    bad_refs = sorted({r for kf in rep.key_findings for r in kf.evidence_refs if r not in verified})
    checks.append(CheckResult(name="evidence_refs_valid", passed=not bad_refs, mandatory=False,
                              detail=f"unknown refs {bad_refs}" if bad_refs else ""))
    if spec.reporting.max_words:
        words = len(" ".join(t for _, t, _ in fields).split())
        checks.append(CheckResult(name="within_word_limit", passed=words <= spec.reporting.max_words,
                                  mandatory=False, detail=f"{words} words (limit {spec.reporting.max_words})",
                                  value=float(words)))
    return result()
