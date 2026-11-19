# Corrected View Rules

## Status and Scope

**Status: pre-computation rules, 2026-11-19.** This document defines an additive, post-hoc
"corrected view" requested by the user. It is committed before the corrected tables are computed.
The frozen Part A/Part B records, v3 scores, v3.1 rescores, diagnostic replay, protocol tags, and
published conclusions remain immutable and authoritative for their original analyses. The
corrected view is always labelled **post-hoc / sensitivity**, never substituted silently for a
frozen result.

The view covers stage-level results for:

1. Part A in the original 4,096-token model group;
2. Part A in the price-matched 16,384-token model group; and
3. Part B stage pass rates in both groups, using the effective workflow cells after resolving the
   five approved Docker reruns.

It does not infer missing downstream outcomes. Exact end-to-end Part B correction requires the
separate paid continuation protocol in `docs/CONTINUATION_PROTOCOL.md`.

## Views Reported Side by Side

Every output row is keyed by `(model_group, part, stage, model_alias)` and reports one fixed
denominator with five pass counts and rates side by side:

| View | Definition |
|---|---|
| `frozen` | The saved primary v3 stage status, without reinterpretation. |
| `int64_recovered` | `frozen`, plus a failed cleaning/analysis stage only when its saved failure contains the exact NumPy `int64` serialization error and its saved pinned-image replay passes that stage's frozen validator. No downstream stage is imputed. |
| `rounding_recovered` | `frozen`, plus a reporting failure only when `derived_values_correct` is its sole failed mandatory v3 check and every rejected derived value equals the recomputed value rounded half-up to the decimal precision literally present in the saved model report. |
| `v3_1` | The saved post-hoc v3.1 reporting rescore beside frozen v3. Cleaning and analysis are unchanged because v3.1 applies only to reporting. |
| `combined` | The union of frozen passes and uniquely attributed int64, stated-precision, and v3.1 recoveries under the precedence rules below. |

For cleaning and analysis, `rounding_recovered` and `v3_1` equal `frozen`; these columns are retained
so that the table schema is stable. For reporting, `int64_recovered` equals `frozen` unless a future
diagnostic replay explicitly contains a reporting-stage serialization case; the committed CP8
source evidence contains none.

## Attribution and Precedence

Each stage opportunity receives exactly one mutually exclusive `pass_attribution`:

1. `frozen_pass` if the frozen v3 stage passed;
2. otherwise `int64_recovered` if the exact failure and pinned replay conditions hold;
3. otherwise `rounding_recovered` if the stated-precision rule holds;
4. otherwise `v3_1_recovered` if the saved v3.1 ground-truth validation passes;
5. otherwise `not_recovered`.

This precedence is an accounting rule, not a claim that one correction is scientifically more
important. The current evidence is naturally disjoint: int64 recovery affects cleaning/analysis;
the 15 rounding recoveries affect reporting; and the 30 known q7 false rejects are covered by v3.1
and have no run ID in common with the 15 rounding recoveries. The analyzer must assert those
disjointness facts. If a later input violates them, it stops instead of double-counting.

`combined_pass` is true for the first four attribution values. A recovered stage adds at most one
to its row. The report also gives a correction-flow table (`frozen_pass`, each unique addition,
`not_recovered`) whose cells sum to the denominator.

## Part A and Part B Denominators

- **Part A:** the denominator is the saved independent stage records in that exact
  `(group, stage, alias)` cell. Under the completed designs this is four projects per cell. A
  diagnostic replay may change the corrected status of the stage itself only; it does not create a
  workflow or a downstream result.
- **Part B:** first resolve the price-matched group's five append-only Docker reruns using the
  frozen successful-rerun-replaces-void rule. The original group needs no such resolution. The
  denominator is every effective stage opportunity assigned to the alias in the path, including
  frozen `blocked_by_invalid_artifact` and `not_run_upstream_failure` stage records. This makes the
  stage pass rate reflect the frozen workflow grid and prevents selective removal of stalled cells.
- A void-infrastructure stage remains in the displayed denominator and is separately counted; no
  correction in this document converts infrastructure failure into model failure or success.
- Every table prints integer numerators and denominators as well as rates. Groups are never pooled
  into a single provider or vendor comparison.

## Output Contract

The future processed JSON is additive and uses **aliases only**. It must not contain display names,
provider names, or vendor-level labels. Its minimum schema is:

```text
model_groups.<group>.parts.<part>.stages.<stage>.models.<alias>:
  denominator
  frozen: {passed, rate}
  int64_recovered: {passed, rate, unique_additions}
  rounding_recovered: {passed, rate, unique_additions}
  v3_1: {passed, rate, unique_additions}
  combined: {passed, rate}
  attribution_counts
```

The rendered report alone maps aliases to model names using the group-specific frozen registry:
original `A/B/C` = Sonnet 4.6 / Nova Pro / gpt-oss-120b; price-matched `A/B/C` = Sonnet 4.6 /
Kimi K3 / GLM 5. The report must show the five views side by side, label every table post-hoc, and
link each aggregate to the processed JSON field.

## Reproducibility and Non-Mutation

Inputs are the two frozen Part A files, two frozen Part B files, the committed diagnostic JSON and
replay artifacts, and the four committed v3.1 rescore files. The future analyzer records hashes of
all inputs, asserts the exact-error/replay-validator criteria, asserts rounding/q7 disjointness,
and writes only new processed/report paths. It never edits a raw record, a replay, a validator, an
existing processed result, or a frozen conclusion.
