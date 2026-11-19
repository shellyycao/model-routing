"""Post-freeze reporting validator v3.

This module is additive. ``src.evaluation.reporting.validate_reporting`` remains the frozen v2
validator used by all recorded pilot runs. V3 separates semantic ranking correctness from explicit
structured-field compliance:

* an explicit ranking may use the declared display labels or their stable metric keys;
* an omitted ranking is semantically recoverable only when the finding contains every required
  reported value (the order is then deterministic);
* a wrong explicit order remains a mandatory failure;
* explicit ranking presence is reported separately as a non-mandatory contract-compliance check.

The distinction is needed because v2 hid the metric-key -> display-label map from models and called
q3 a trend while requiring a ranking in the validator. Existing raw outputs are never modified.
"""

from __future__ import annotations

import math

from pydantic import ValidationError

from src.contracts import CheckResult, ProjectSpec, ReportOutput, ValidationResult

from .reporting import (
    DEFAULT_MAX_UNSUPPORTED_CLAIMS,
    _float_unit,
    number_matches,
    validate_reporting,
)

VALIDATOR_VERSION = "3.0-post-freeze"


def _canonical_tokens(actual: list[str], labels: dict[str, str]) -> list[str] | None:
    token_map = {key: label for key, label in labels.items()}
    token_map.update({label: label for label in labels.values()})
    if any(token not in token_map for token in actual):
        return None
    return [token_map[token] for token in actual]


def _ordered(actual: list[str], labels: dict[str, str], verified: dict[str, float],
             tolerances: dict[str, tuple[float, float]]) -> bool:
    expected_labels = set(labels.values())
    if len(actual) != len(expected_labels) or set(actual) != expected_labels:
        return False
    label_to_key = {label: key for key, label in labels.items()}
    for left, right in zip(actual, actual[1:]):
        lk, rk = label_to_key[left], label_to_key[right]
        abs_tol, rel_tol = tolerances.get(lk, (1e-6, 1e-4))
        tie_tol = max(abs_tol, rel_tol * max(abs(verified[lk]), abs(verified[rk])))
        if verified[lk] + tie_tol < verified[rk]:
            return False
    return True


def validate_reporting_v3(report: ReportOutput | dict | str, verified_findings: dict[str, float],
                          spec: ProjectSpec, *,
                          max_unsupported_claims: int = DEFAULT_MAX_UNSUPPORTED_CLAIMS,
                          quality_basis: str = "ground_truth",
                          cleaning_counts: dict[str, int | float] | None = None) -> ValidationResult:
    """Re-evaluate a report under the documented post-freeze v3 ranking policy."""
    base = validate_reporting(
        report, verified_findings, spec, max_unsupported_claims=max_unsupported_claims,
        quality_basis=quality_basis, cleaning_counts=cleaning_counts)
    try:
        rep = report if isinstance(report, ReportOutput) else (
            ReportOutput.model_validate_json(report) if isinstance(report, str)
            else ReportOutput.model_validate(report))
    except (ValidationError, ValueError):
        payload = base.model_dump(mode="python")
        payload["validator_version"] = VALIDATOR_VERSION
        return ValidationResult.model_validate(payload)

    verified = {k: float(v) for k, v in verified_findings.items()
                if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)}
    tolerances = {k: (q.abs_tolerance, q.rel_tolerance)
                  for q in spec.analysis_questions for k in q.metric_keys}
    q_by_id = {q.question_id: q for q in spec.analysis_questions}
    by_finding: dict[str, list] = {}
    for finding in rep.key_findings:
        by_finding.setdefault(finding.finding_id, []).append(finding)

    semantic_failures: list[str] = []
    explicit_failures: list[str] = []
    required_claims = 0
    explicit_claims = 0
    for finding_id in spec.reporting.required_finding_ids:
        question = q_by_id.get(finding_id)
        if question is None or not question.ranking_labels:
            continue
        labels = question.ranking_labels
        missing_verified = [key for key in labels if key not in verified]
        if missing_verified:
            semantic_failures.append(f"{finding_id}: ranking keys missing {missing_verified}")
            continue
        for finding in by_finding.get(finding_id, []):
            required_claims += 1
            if finding.ranking is not None:
                canonical = _canonical_tokens(finding.ranking, labels)
                if canonical is None:
                    explicit_failures.append(
                        f"{finding_id}: ranking tokens must be declared labels or metric keys")
                    semantic_failures.append(f"{finding_id}: unrecognised ranking tokens {finding.ranking}")
                    continue
                explicit_claims += 1
                if not _ordered(canonical, labels, verified, tolerances):
                    semantic_failures.append(f"{finding_id}: stated order {finding.ranking} is not descending")
                continue

            explicit_failures.append(
                f"{finding_id}: explicit ranking omitted; semantic order recovered from reported_values")
            supplied = finding.reported_values
            if any(key not in supplied or not math.isfinite(supplied[key]) for key in labels):
                semantic_failures.append(
                    f"{finding_id}: ranking omitted and complete finite reported_values are unavailable")
                continue
            inferred = [labels[key] for key in sorted(
                labels, key=lambda key: (-supplied[key], labels[key]))]
            if not _ordered(inferred, labels, verified, tolerances):
                semantic_failures.append(
                    f"{finding_id}: ranking inferred from reported_values is not the verified order")

    semantic = CheckResult(
        name="rankings_correct", passed=not semantic_failures, mandatory=True,
        detail="; ".join(semantic_failures[:8]) or "all ranking semantics correct")
    explicit_rate = explicit_claims / required_claims if required_claims else 1.0
    explicit = CheckResult(
        name="rankings_explicit", passed=not explicit_failures, mandatory=False,
        detail="; ".join(explicit_failures[:8]) or "all required rankings explicitly structured",
        value=explicit_rate)

    checks: list[CheckResult] = []
    for check in base.checks:
        if check.name == "rankings_correct":
            checks.extend([semantic, explicit])
        else:
            checks.append(check)
    return ValidationResult(
        stage=base.stage,
        hard_pass=all(check.passed for check in checks if check.mandatory),
        checks=checks,
        quality=dict(base.quality),
        quality_basis=base.quality_basis,
        validator_version=VALIDATOR_VERSION,
    )
