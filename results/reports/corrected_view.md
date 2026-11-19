# Corrected Stage-Level View

**POST-HOC / SENSITIVITY. Frozen v3 results remain authoritative. This report does not compute corrected Part B workflow feasibility.**

## Key Findings

- GLM 5 Part A analysis changes from **0/4 (0.0%)** frozen to **4/4 (100.0%)** combined because all four saved failures were serialization-only and passed the frozen validator after replay.
- Across both groups and both parts, the combined stage view adds **55** int64 recoveries, **15** stated-precision recoveries, and **30** separate v3.1 recoveries. The attribution sets are mutually exclusive.
- In original-group Part B analysis, Nova Pro gains **9** and gpt-oss-120b gains **2** stage passes in the int64 view; no blocked reporting stage is imputed here.
- In price-matched Part B analysis, GLM 5 changes from **27/60 (45.0%)** frozen to **56/60 (93.3%)** combined. This is a stage-level artifact sensitivity, not a revised end-to-end result.
- The reporting corrections remain distinct: **15** reports are recovered by literal stated precision and **30** by v3.1's q7 fix; no record is counted in both.

## Scope and Method

Every row keeps one fixed denominator and shows frozen v3, int64-only, stated-precision-only, v3.1, and combined views side by side. Part B uses all effective stage opportunities after resolving the five append-only Docker reruns; blocked and not-run stages stay in the denominator. Corrections change only the stage with saved evidence. The processed JSON contains aliases only; names are rendered here from the group-specific registries.

Source: `results/processed/corrected_view.json` fields `model_groups`, `assertions`, and `source_hashes`.

## Part A

### Original model group (maxTokens 4096)

| Stage | Model | Frozen | int64 view | Rounding view | v3.1 view | Combined |
|---|---|---:|---:|---:|---:|---:|
| cleaning | Sonnet 4.6 (`A`) | 3/4 (75.0%) | 3/4 (75.0%) | 3/4 (75.0%) | 3/4 (75.0%) | 3/4 (75.0%) |
| cleaning | Nova Pro (`B`) | 0/4 (0.0%) | 0/4 (0.0%) | 0/4 (0.0%) | 0/4 (0.0%) | 0/4 (0.0%) |
| cleaning | gpt-oss-120b (`C`) | 2/4 (50.0%) | 2/4 (50.0%) | 2/4 (50.0%) | 2/4 (50.0%) | 2/4 (50.0%) |
| analysis | Sonnet 4.6 (`A`) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) |
| analysis | Nova Pro (`B`) | 0/4 (0.0%) | 0/4 (0.0%) | 0/4 (0.0%) | 0/4 (0.0%) | 0/4 (0.0%) |
| analysis | gpt-oss-120b (`C`) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) |
| reporting | Sonnet 4.6 (`A`) | 3/4 (75.0%) | 3/4 (75.0%) | 3/4 (75.0%) | 4/4 (100.0%) | 4/4 (100.0%) |
| reporting | Nova Pro (`B`) | 2/4 (50.0%) | 2/4 (50.0%) | 2/4 (50.0%) | 2/4 (50.0%) | 2/4 (50.0%) |
| reporting | gpt-oss-120b (`C`) | 2/4 (50.0%) | 2/4 (50.0%) | 2/4 (50.0%) | 3/4 (75.0%) | 3/4 (75.0%) |

### Price-matched model group (maxTokens 16384)

| Stage | Model | Frozen | int64 view | Rounding view | v3.1 view | Combined |
|---|---|---:|---:|---:|---:|---:|
| cleaning | Sonnet 4.6 (`A`) | 3/4 (75.0%) | 3/4 (75.0%) | 3/4 (75.0%) | 3/4 (75.0%) | 3/4 (75.0%) |
| cleaning | Kimi K3 (`B`) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) |
| cleaning | GLM 5 (`C`) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) |
| analysis | Sonnet 4.6 (`A`) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) |
| analysis | Kimi K3 (`B`) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) |
| analysis | GLM 5 (`C`) | 0/4 (0.0%) | 4/4 (100.0%) | 0/4 (0.0%) | 0/4 (0.0%) | 4/4 (100.0%) |
| reporting | Sonnet 4.6 (`A`) | 2/4 (50.0%) | 2/4 (50.0%) | 3/4 (75.0%) | 3/4 (75.0%) | 4/4 (100.0%) |
| reporting | Kimi K3 (`B`) | 1/4 (25.0%) | 1/4 (25.0%) | 2/4 (50.0%) | 1/4 (25.0%) | 2/4 (50.0%) |
| reporting | GLM 5 (`C`) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) | 4/4 (100.0%) |

## Part B Stage Pass Rates

These are stage pass rates, not corrected workflow feasibility. A recovered upstream stage does not create a downstream result.

### Original model group (maxTokens 4096)

| Stage | Model | Frozen | int64 view | Rounding view | v3.1 view | Combined |
|---|---|---:|---:|---:|---:|---:|
| cleaning | Sonnet 4.6 (`A`) | 52/68 (76.5%) | 52/68 (76.5%) | 52/68 (76.5%) | 52/68 (76.5%) | 52/68 (76.5%) |
| cleaning | Nova Pro (`B`) | 1/44 (2.3%) | 1/44 (2.3%) | 1/44 (2.3%) | 1/44 (2.3%) | 1/44 (2.3%) |
| cleaning | gpt-oss-120b (`C`) | 15/44 (34.1%) | 24/44 (54.5%) | 15/44 (34.1%) | 15/44 (34.1%) | 24/44 (54.5%) |
| analysis | Sonnet 4.6 (`A`) | 30/52 (57.7%) | 30/52 (57.7%) | 30/52 (57.7%) | 30/52 (57.7%) | 30/52 (57.7%) |
| analysis | Nova Pro (`B`) | 5/44 (11.4%) | 14/44 (31.8%) | 5/44 (11.4%) | 5/44 (11.4%) | 14/44 (31.8%) |
| analysis | gpt-oss-120b (`C`) | 27/60 (45.0%) | 29/60 (48.3%) | 27/60 (45.0%) | 27/60 (45.0%) | 29/60 (48.3%) |
| reporting | Sonnet 4.6 (`A`) | 12/52 (23.1%) | 12/52 (23.1%) | 16/52 (30.8%) | 18/52 (34.6%) | 22/52 (42.3%) |
| reporting | Nova Pro (`B`) | 10/44 (22.7%) | 10/44 (22.7%) | 10/44 (22.7%) | 10/44 (22.7%) | 10/44 (22.7%) |
| reporting | gpt-oss-120b (`C`) | 10/60 (16.7%) | 10/60 (16.7%) | 10/60 (16.7%) | 15/60 (25.0%) | 15/60 (25.0%) |

### Price-matched model group (maxTokens 16384)

| Stage | Model | Frozen | int64 view | Rounding view | v3.1 view | Combined |
|---|---|---:|---:|---:|---:|---:|
| cleaning | Sonnet 4.6 (`A`) | 56/68 (82.4%) | 56/68 (82.4%) | 56/68 (82.4%) | 56/68 (82.4%) | 56/68 (82.4%) |
| cleaning | Kimi K3 (`B`) | 43/44 (97.7%) | 43/44 (97.7%) | 43/44 (97.7%) | 43/44 (97.7%) | 43/44 (97.7%) |
| cleaning | GLM 5 (`C`) | 39/44 (88.6%) | 41/44 (93.2%) | 39/44 (88.6%) | 39/44 (88.6%) | 41/44 (93.2%) |
| analysis | Sonnet 4.6 (`A`) | 44/52 (84.6%) | 44/52 (84.6%) | 44/52 (84.6%) | 44/52 (84.6%) | 44/52 (84.6%) |
| analysis | Kimi K3 (`B`) | 40/44 (90.9%) | 40/44 (90.9%) | 40/44 (90.9%) | 40/44 (90.9%) | 40/44 (90.9%) |
| analysis | GLM 5 (`C`) | 27/60 (45.0%) | 56/60 (93.3%) | 27/60 (45.0%) | 27/60 (45.0%) | 56/60 (93.3%) |
| reporting | Sonnet 4.6 (`A`) | 15/52 (28.8%) | 15/52 (28.8%) | 23/52 (44.2%) | 25/52 (48.1%) | 33/52 (63.5%) |
| reporting | Kimi K3 (`B`) | 14/44 (31.8%) | 14/44 (31.8%) | 15/44 (34.1%) | 15/44 (34.1%) | 16/44 (36.4%) |
| reporting | GLM 5 (`C`) | 32/60 (53.3%) | 32/60 (53.3%) | 32/60 (53.3%) | 37/60 (61.7%) | 37/60 (61.7%) |

## Attribution Audit

The correction flow across all **1008** stage opportunities is: frozen pass 518; unique int64 addition 55; unique stated-precision addition 15; unique v3.1 addition 30; not recovered 390. The counts sum to the fixed denominators. The 15 rounding and 30 q7/v3.1 run-ID sets are disjoint.

## Limitations and Reproduction

This additive view diagnoses scorer/environment artifacts; it does not erase model errors, infer missing calls, or replace frozen conclusions. The exact corrected Part B view waits for all 40 approved continuation records. The 11 recovered cleaning cases whose downstream stages already ran will later use those observed outcomes with an explicit disclosure that their handoffs saw upstream status `failed`.

```bash
.venv/bin/python -m experiments.analyze_corrected_view
```
