# Corrected Q2 View (Post-hoc)

**POST-HOC / CORRECTED SENSITIVITY. Frozen workflow outcomes remain authoritative and are shown beside every corrected view.**

## Key Findings

- Original-group main-grid feasibility changes from **17/108 (15.7%)** frozen to **25/108 (23.1%)** corrected under v3; the v3.1 comparison is **21/108 (19.4%)** to **30/108 (27.8%)**. Denominator: 108 cells.
- Price-matched-group main-grid feasibility changes from **41/108 (38.0%)** to **52/108 (48.1%)** under v3, and from **53/108 (49.1%)** to **70/108 (64.8%)** under v3.1. Denominator: 108 cells.
- The view uses all **40/40** analysis continuations and all **11/11** cleaning recoveries; one cell belongs to both evidence sets, and continuation infrastructure voids were **0**.
- Continuation spend was **$1.3974**, reconciled across 40 records, 40 invocations, and the separate ledger; failed paid attempts were 0.
- These corrections may change the labels used to assess the frozen Router's 22/50 and 31/64 feasibility-direction results. That is an open item only: no Router validity number was recomputed here.

## Scope and Rules

A corrected analysis-continuation cell combines the original passed or replay-recovered cleaning stage, replay-recovered analysis artifact, and newly executed reporting result under frozen v3. A corrected cleaning-only cell substitutes the replay-passed cleaning status and keeps the already observed analysis/reporting outcomes. One cell needs both cleaning and analysis recovery and therefore uses its continuation reporting result, but it is still counted only once as a workflow cell. All 11 downstream handoffs saw cleaning status `failed`; they are therefore labelled sensitivity evidence, not a reconstruction of how downstream models would respond to a different label. V3.1 is a separate offline rescore of reporting. Q1 stated-precision rounding recoveries are not applied to Q2.

Source: `results/processed/corrected_q2.json`, fields `rules` and `integrity_audit`; inputs and hashes are in `source_hashes`.

## Feasibility

| Group | View | All paths | Single-model | Cross-model |
|---|---|---:|---:|---:|
| Original group (4096) | frozen_v3 | 17/108 (15.7%) | 2/12 (16.7%) | 15/96 (15.6%) |
| Original group (4096) | corrected_v3 | 25/108 (23.1%) | 2/12 (16.7%) | 23/96 (24.0%) |
| Original group (4096) | frozen_v31 | 21/108 (19.4%) | 3/12 (25.0%) | 18/96 (18.8%) |
| Original group (4096) | corrected_v31 | 30/108 (27.8%) | 3/12 (25.0%) | 27/96 (28.1%) |
| Price-matched group (16384) | frozen_v3 | 41/108 (38.0%) | 3/12 (25.0%) | 38/96 (39.6%) |
| Price-matched group (16384) | corrected_v3 | 52/108 (48.1%) | 6/12 (50.0%) | 46/96 (47.9%) |
| Price-matched group (16384) | frozen_v31 | 53/108 (49.1%) | 4/12 (33.3%) | 49/96 (51.0%) |
| Price-matched group (16384) | corrected_v31 | 70/108 (64.8%) | 7/12 (58.3%) | 63/96 (65.6%) |

All numerators and denominators above come from `model_groups.<group>.{main_grid,single_model_main_grid,cross_model_main_grid}` in `results/processed/corrected_q2.json`.

## Single-model and Cross-model Paths

Single-model denominators are 12 per group (three alias-constant paths × four projects); cross-model denominators are 96. The unequal denominators make the rates descriptive, not a causal claim about mixing models. Model mappings for this rendered report are: original A/B/C = Sonnet 4.6 / Nova Pro / gpt-oss-120b; price-matched A/B/C = Sonnet 4.6 / Kimi K3 / GLM 5. The processed JSON contains aliases only.

## Project and Path Changes

Every one of the 108 per-group project/path outcomes is stored in `model_groups.<group>.project_path_outcomes_main_grid`. The table below lists only paths whose v3 or v3.1 outcome changed.

| Group | Project | Path | Correction | v3 frozen → corrected | v3.1 frozen → corrected |
|---|---|---|---|---|---|
| Original | customer_churn | `A-B-A` | analysis_continuation | infeasible → infeasible | infeasible → feasible |
| Original | customer_churn | `A-B-B` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Original | customer_churn | `C-B-B` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Original | energy_consumption | `A-B-C` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Original | retail_sales | `C-A-A` | cleaning_observed_downstream | infeasible → feasible | infeasible → feasible |
| Original | retail_sales | `C-A-C` | cleaning_observed_downstream | infeasible → feasible | infeasible → feasible |
| Original | support_operations | `C-A-B` | cleaning_observed_downstream | infeasible → feasible | infeasible → feasible |
| Original | support_operations | `C-B-A` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Original | support_operations | `C-B-B` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Price-matched | customer_churn | `A-C-A` | analysis_continuation | infeasible → infeasible | infeasible → feasible |
| Price-matched | customer_churn | `A-C-B` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Price-matched | customer_churn | `A-C-C` | analysis_continuation | infeasible → infeasible | infeasible → feasible |
| Price-matched | customer_churn | `B-C-A` | analysis_continuation | infeasible → infeasible | infeasible → feasible |
| Price-matched | customer_churn | `B-C-C` | analysis_continuation | infeasible → infeasible | infeasible → feasible |
| Price-matched | customer_churn | `C-C-A` | analysis_continuation | infeasible → infeasible | infeasible → feasible |
| Price-matched | customer_churn | `C-C-B` | analysis_continuation | infeasible → infeasible | infeasible → feasible |
| Price-matched | customer_churn | `C-C-C` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Price-matched | energy_consumption | `A-C-C` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Price-matched | energy_consumption | `B-C-C` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Price-matched | energy_consumption | `C-C-C` | cleaning_and_analysis_continuation | infeasible → feasible | infeasible → feasible |
| Price-matched | support_operations | `B-C-A` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Price-matched | support_operations | `B-C-B` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Price-matched | support_operations | `B-C-C` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Price-matched | support_operations | `C-C-A` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Price-matched | support_operations | `C-C-B` | analysis_continuation | infeasible → feasible | infeasible → feasible |
| Price-matched | support_operations | `C-C-C` | analysis_continuation | infeasible → feasible | infeasible → feasible |

## First-failure Stage

| Group | View | Cleaning | Analysis | Reporting | None (feasible) |
|---|---|---:|---:|---:|---:|
| Original group | frozen_v3 | 64 | 13 | 14 | 17 |
| Original group | corrected_v3 | 58 | 4 | 21 | 25 |
| Original group | frozen_v31 | 64 | 13 | 10 | 21 |
| Original group | corrected_v31 | 58 | 4 | 16 | 30 |
| Price-matched group | frozen_v3 | 11 | 21 | 35 | 41 |
| Price-matched group | corrected_v3 | 9 | 0 | 47 | 52 |
| Price-matched group | frozen_v31 | 11 | 21 | 23 | 53 |
| Price-matched group | corrected_v31 | 9 | 0 | 29 | 70 |

Source: `results/processed/corrected_q2.json`, `model_groups.<group>.first_failure_stage_main_grid`. Counts include all 108 main-grid cells and sum to 108 in every row.

## Cost per Feasible Completion

Frozen cost-per-feasible values use the original executed spend. Corrected values add each continuation call to its original run, so failed original stages and all extra continuation calls remain charged.

| Group | Scope | Base spend | Added continuation spend | Corrected spend | Frozen v3 cost/success | Corrected v3 cost/success | Frozen v3.1 cost/success | Corrected v3.1 cost/success |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Original | main_grid | $4.4060 | $0.1789 | $4.5849 | $0.2592 | $0.1834 | $0.2098 | $0.1528 |
| Original | all_effective | $7.6923 | $0.2256 | $7.9179 | $0.2747 | $0.2199 | $0.2024 | $0.1650 |
| Price-matched | main_grid | $17.0873 | $1.1185 | $18.2059 | $0.4168 | $0.3501 | $0.3224 | $0.2601 |
| Price-matched | all_effective | $23.2235 | $1.1718 | $24.3953 | $0.3807 | $0.3168 | $0.3016 | $0.2440 |

Source: `results/processed/corrected_q2.json`, `model_groups.<group>.costs`. Base costs come from the previously reconciled workflow cost outputs; added spend reconciles to `results/raw/ledgers/continuations.json`.

## Limitations and Open Items

This is an additive post-hoc view of known serialization artifacts. It does not modify frozen records, apply rounding sensitivity to end-to-end feasibility, retrain the Router, or recompute counterfactual validity. The 11 cleaning recoveries retain observed downstream outcomes even though those downstream prompts saw an upstream `failed` status. No continuation was void-infrastructure; if one had been, it would have remained separately reported with no substantive replacement.

## Sources and Reproduction

```bash
.venv/bin/python -m experiments.analyze_corrected_q2
```

The JSON artifact is the authoritative numerical layer. This renderer is deterministic over the source hashes recorded there.
