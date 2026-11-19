# Independent Benchmark v2 Results

**Protocol:** `independent-v2-1.1` / tag `independent-v2-frozen-v1.1`  
**Execution date:** 2026-11-18  
**Integrity audit:** PASS  

## Execution and accounting

All 270 planned model-case cells completed. The ledger records 270 API attempts, 232,581 input tokens, 224,100 output tokens, and $1.1181174. There were 0 failed attempts, 0 unknown-usage calls, and 0 unpriced calls.

## Primary results

| Task | Model | Operational | Primary result | Parse | Truncated | Cost |
|---|---|---:|---:|---:|---:|---:|
| A1 | Claude Sonnet 4.6 | 100.0% | 27/30 (90.0%) | 30/30 | 0 | $0.2059 |
| A1 | Amazon Nova Pro | 93.3% | 17/30 (56.7%) | 30/30 | 0 | $0.0327 |
| A1 | OpenAI gpt-oss-120b | 96.7% | 26/30 (86.7%) | 29/30 | 0 | $0.0195 |
| A2 | Claude Sonnet 4.6 | 100.0% | 30/30 (100.0%) | 30/30 | 0 | $0.0776 |
| A2 | Amazon Nova Pro | 100.0% | 25/30 (83.3%) | 30/30 | 0 | $0.0156 |
| A2 | OpenAI gpt-oss-120b | 100.0% | 30/30 (100.0%) | 30/30 | 0 | $0.0093 |
| A3 | Claude Sonnet 4.6 | 96.7% | 0.965 | 30/30 | 0 | $0.5791 |
| A3 | Amazon Nova Pro | 96.7% | 0.958 | 30/30 | 0 | $0.0994 |
| A3 | OpenAI gpt-oss-120b | 73.3% | 0.732 | 29/30 | 1 | $0.0790 |

A1 primary is functional correctness; A2 primary is content correctness. For A3, the table uses the disclosed strict sensitivity view in which a response that fails the frozen `ranking_valid` contract receives zero nDCG. Cell-level Wilson or deterministic bootstrap 95% intervals are stored in the JSON artifact.

## Secondary metrics

| Task | Model | Hidden pass / content F1 / valid-only nDCG | Bug-location / null accuracy / grounding | Citation accuracy | Median generation |
|---|---|---:|---:|---:|---:|
| A1 | Claude Sonnet 4.6 | 0.978 | 0.000 | — | 3.22s |
| A1 | Amazon Nova Pro | 0.803 | 0.000 | — | 2.07s |
| A1 | OpenAI gpt-oss-120b | 0.947 | 0.000 | — | 4.78s |
| A2 | Claude Sonnet 4.6 | 1.000 | 1.000 | — | 1.04s |
| A2 | Amazon Nova Pro | 0.970 | 1.000 | — | 0.88s |
| A2 | OpenAI gpt-oss-120b | 1.000 | 1.000 | — | 2.09s |
| A3 | Claude Sonnet 4.6 | 0.998 | 0.000 | 1.000 | 6.09s |
| A3 | Amazon Nova Pro | 0.991 | 0.018 | 1.000 | 3.42s |
| A3 | OpenAI gpt-oss-120b | 0.998 | 0.293 | 0.967 | 16.08s |

## Difficulty stratification

Primary means are functional-correctness rate for A1, content-correctness rate for A2, and strict invalid-as-zero nDCG for A3.

| Task | Model | Easy | Medium | Hard |
|---|---|---:|---:|---:|
| A1 | Claude Sonnet 4.6 | 1.000 | 1.000 | 0.700 |
| A1 | Amazon Nova Pro | 0.700 | 0.700 | 0.300 |
| A1 | OpenAI gpt-oss-120b | 0.900 | 1.000 | 0.700 |
| A2 | Claude Sonnet 4.6 | 1.000 | 1.000 | 1.000 |
| A2 | Amazon Nova Pro | 0.800 | 0.900 | 0.800 |
| A2 | OpenAI gpt-oss-120b | 1.000 | 1.000 | 1.000 |
| A3 | Claude Sonnet 4.6 | 1.000 | 1.000 | 0.895 |
| A3 | Amazon Nova Pro | 0.996 | 0.983 | 0.895 |
| A3 | OpenAI gpt-oss-120b | 0.600 | 0.699 | 0.897 |

## Frozen A3 scorer audit

The frozen scorer computes nDCG and grade-2 recall even when the submitted ranking repeats IDs and fails `ranking_valid`. Duplicates can therefore produce values above 1. The raw frozen values remain unchanged; they are not used as the sole headline view.

| Model | Valid rankings | Frozen all-case nDCG | Valid-only nDCG | Strict invalid=0 nDCG | nDCG > 1 | Recall > 1 |
|---|---:|---:|---:|---:|---:|---:|
| Claude Sonnet 4.6 | 29/30 | 1.002 | 0.998 | 0.965 | 1 | 1 |
| Amazon Nova Pro | 29/30 | 0.995 | 0.991 | 0.958 | 1 | 1 |
| OpenAI gpt-oss-120b | 22/30 | 0.969 | 0.998 | 0.732 | 3 | 3 |

## Interpretation limits

- These are 30 fixed cases per task and one deterministic-temperature run per model-case cell; inference is bounded to this benchmark.
- No single composite pools A1, A2, and A3.
- A1 bug-location recall is a strict string-overlap diagnostic and is not a substitute for functional correctness.
- A3 evidence grounding requires exact accepted fact values in structured claims; it should be read separately from ranking and citation validity.
- The A3 strict and valid-only views are disclosed sensitivity analyses prompted by a frozen-scorer defect; the original scores remain in the raw records.

## Reproducibility

```bash
.venv/bin/python -m experiments.analyze_independent_v2
```
