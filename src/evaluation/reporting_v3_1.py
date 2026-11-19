"""POST-HOC reporting validator v3.1. Secondary analysis only; it never replaces v3 scores.

Motivation (docs/reviews/2026-11-18_reporting_v3_1_posthoc.md): the frozen v2/v3 check
`prose_claims_consistent` ties a number written after "<metric alias> is/was ..." to that alias. In a
COMPARATIVE clause ("Premium LTV is 292.0% higher than Basic") the number is a relative change, not
the alias's value, so a correct sentence was rejected (Phase 1, customer_churn q7, two models).

v3.1 = v3, except that a `prose_claims_consistent` entry is cleared when ALL of these hold:
  1. relation is "after" (number follows "<alias> is/was/=/:"),
  2. the number is immediately followed by a comparative word (higher/lower/more/less/greater/
     larger/smaller/above/below/up/down/than),
  3. the number matches ANOTHER verified metric of the same finding (the frozen check already
     identified it: "matches '<other_key>'"),
  4. the frozen detail list is complete (fewer than 10 entries, i.e. not truncated).
Every other attribution error is kept. All other checks are unchanged. The frozen v3 module is not
modified; v3.1 post-processes the v3 result deterministically.
"""

from __future__ import annotations

import re

from src.contracts import ReportOutput, ValidationResult
from src.contracts.project import ProjectSpec

from .reporting_v3 import validate_reporting_v3

VALIDATOR_VERSION = "3.1-posthoc"
_ENTRY = re.compile(r"^(?P<fid>[^:]+): number '(?P<num>.+?)' (?P<rel>after|before) '(?P<key>[^']+)' "
                    r"matches (?:'(?P<other>[^']+)'|no verified)")
_COMPARATIVE = re.compile(r"\s*(?:percent|percentage points?|pp|%)?\s*(?:higher|lower|more|less|greater|larger|"
                          r"smaller|above|below|up|down|than)\b", re.IGNORECASE)
_MAX_DETAIL_ENTRIES = 10   # reporting.py truncates the detail list at 10 entries


def _report(report) -> ReportOutput:
    if isinstance(report, ReportOutput):
        return report
    if isinstance(report, str):
        return ReportOutput.model_validate_json(report)
    return ReportOutput.model_validate(report)


def _comparative_after(statement: str, number_text: str) -> bool:
    for m in re.finditer(re.escape(number_text), statement):
        if _COMPARATIVE.match(statement[m.end():]):
            return True
    return False


def validate_reporting_v3_1(report, verified_findings: dict[str, float], spec: ProjectSpec, **kw) -> ValidationResult:
    base = validate_reporting_v3(report, verified_findings, spec, **kw)
    rep = _report(report)
    statements = {kf.finding_id: kf.statement for kf in rep.key_findings}
    checks = []
    for c in base.checks:
        if c.name == "prose_claims_consistent" and not c.passed and c.detail:
            entries = [e.strip() for e in c.detail.split("; ") if e.strip()]
            if len(entries) < _MAX_DETAIL_ENTRIES:
                kept, cleared = [], []
                for e in entries:
                    m = _ENTRY.match(e)
                    ok = (m and m["rel"] == "after" and m["other"]
                          and _comparative_after(statements.get(m["fid"], ""), m["num"]))
                    (cleared if ok else kept).append(e)
                if cleared:
                    detail = "; ".join(kept) if kept else "structured claims agree with prose"
                    detail += f" [v3.1 cleared comparative-clause attributions: {'; '.join(cleared)}]"
                    c = c.model_copy(update={"passed": not kept, "detail": detail})
        checks.append(c)
    hard_pass = all(c.passed for c in checks if c.mandatory)
    return base.model_copy(update={"checks": checks, "hard_pass": hard_pass, "validator_version": VALIDATOR_VERSION})
