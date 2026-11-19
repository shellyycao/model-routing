# Price-matched-v2 benchmark results

This compares three specific models callable under this account, not vendors. The selected set spans approximately 4.3× in price. GLM 5 was chosen for generation match; Kimi K3 ran without temperature after the pilot rejected that field; Grok 4.7 was removed after a real-invoke AccessDeniedException.

## Integrity audit

**PASS** — 810 records matched 810 primary invocations and the frozen plan; no logical cell was selectively rerun. The ledger has 834 attempts and totals $23.909231 including pilot.

| Component | USD |
|---|---:|
| Main known responses | 20.758389 |
| Main failed-attempt reserves | 2.479459 |
| Main total | 23.237847 |
| Pilot/re-pilot | 0.671384 |
| Shared total | 23.909231 |

Hashes, IDs and parameters matched: maxTokens 16384; Sonnet/GLM temperature 0; Kimi temperature omitted. Only EndpointConnectionError caused automatic retries.

## Main results (voids excluded)

| Task | Model | n/90 | Primary | Operational | Key secondary | Cost | Cost/success or point | Median latency |
|---|---|---:|---:|---:|---|---:|---:|---:|
| A1 | Sonnet 4.6 | 89/90 | 0.899 | 1.000 | hidden pass 0.978; bug location 0.612 | $1.996 | $0.0249 | 3.382 s |
| A1 | Kimi K3 | 90/90 | 0.900 | 0.989 | hidden pass 0.970; bug location 0.800 | $4.513 | $0.0557 | 7.251 s |
| A1 | GLM 5 | 89/90 | 0.865 | 1.000 | hidden pass 0.962; bug location 0.163 | $0.368 | $0.0048 | 3.464 s |
| A2 | Sonnet 4.6 | 90/90 | 1.000 | 1.000 | content F1 1.000; schema 1.000 | $0.233 | $0.0026 | 1.045 s |
| A2 | Kimi K3 | 90/90 | 0.989 | 1.000 | content F1 0.998; schema 1.000 | $1.065 | $0.0120 | 1.799 s |
| A2 | GLM 5 | 90/90 | 1.000 | 1.000 | content F1 1.000; schema 1.000 | $0.048 | $0.0005 | 1.455 s |
| A3 | Sonnet 4.6 | 90/90 | 0.976 | 0.978 | dedup 0.997; R1 0.999; R2 0.999; citations 1.000 | $2.830 | $0.0322 | 8.296 s |
| A3 | Kimi K3 | 90/90 | 0.999 | 1.000 | dedup 0.999; R1 0.995; R2 0.995; citations 1.000 | $11.698 | $0.1300 | 31.512 s |
| A3 | GLM 5 | 90/90 | 0.914 | 0.922 | dedup 0.988; R1 0.998; R2 0.998; citations 1.000 | $0.487 | $0.0059 | 15.535 s |

A3 cost per valid response and all token/latency fields are in the JSON.

## Output composition (descriptive)

Kimi returned reasoning text for all 90/90 records in each task. Its extra billed output mainly consists of that returned reasoning text; Bedrock did not provide a separate reasoning-token count. The token equivalents below use an explicitly approximate 4 characters/token conversion, while billed output tokens remain authoritative. Kimi's final-answer length is close to Sonnet's.

| Task | Kimi reasoning chars (median) | Kimi final-answer chars (median) | Sonnet final-answer chars (median) | Kimi answer + reasoning, approx tokens | Kimi billed output tokens (median) |
|---|---:|---:|---:|---:|---:|
| A1 | 5,583.5 | 1,180.5 | 1,036.0 | 1,691.0 | 1,726.0 |
| A2 | 1,108.5 | 209.0 | 210.0 | 329.4 | 417.5 |
| A3 | 27,467.0 | 4,385.0 | 4,159.0 | 7,963.0 | 7,718.0 |

Source: `output_composition`; character-derived token values are approximations, not provider-reported reasoning tokens.

## Void sensitivity

The protocol did not specify post-run handling. Main results exclude the two A1 infrastructure voids; sensitivity counts them as failures. They were not rerun, and no rerun is recommended for the frozen primary analysis.

| A1 model | Excluded | Failure sensitivity |
|---|---:|---:|
| Sonnet 4.6 | 0.899 (n=89) | 0.889 (n=90) |
| Kimi K3 | 0.900 (n=90) | 0.900 (n=90) |
| GLM 5 | 0.865 (n=89) | 0.856 (n=90) |

## Repeat stability

| Task | Model | Repeat means (n) | Range | Complete cases | Exact consistency |
|---|---|---|---:|---:|---:|
| A1 | GLM 5 | 0.867 (30), 0.862 (29), 0.867 (30) | 0.005 | 29 | 0.931 |
| A1 | Kimi K3 | 0.867 (30), 0.933 (30), 0.900 (30) | 0.067 | 30 | 0.933 |
| A1 | Sonnet 4.6 | 0.900 (30), 0.897 (29), 0.900 (30) | 0.003 | 29 | 1.000 |
| A2 | GLM 5 | 1.000 (30), 1.000 (30), 1.000 (30) | 0.000 | 30 | 1.000 |
| A2 | Kimi K3 | 1.000 (30), 0.967 (30), 1.000 (30) | 0.033 | 30 | 0.967 |
| A2 | Sonnet 4.6 | 1.000 (30), 1.000 (30), 1.000 (30) | 0.000 | 30 | 1.000 |
| A3 | GLM 5 | 0.890 (30), 0.892 (30), 0.959 (30) | 0.068 | 30 | 0.633 |
| A3 | Kimi K3 | 1.000 (30), 0.998 (30), 1.000 (30) | 0.002 | 30 | 0.967 |
| A3 | Sonnet 4.6 | 0.965 (30), 0.965 (30), 0.997 (30) | 0.032 | 30 | 0.900 |

## Paired case-level statistics

Families were defined before testing; Holm correction is within each three-pair family. Effects use case-level repeat means; bootstrap intervals use 10,000 paired draws.

| Family | Pair | Difference | 95% CI | raw p | Holm p |
|---|---|---:|---|---:|---:|
| a1_primary_mcnemar_majority | Sonnet 4.6 − Kimi K3 | +0.000 | [-0.033, +0.033] | 1.0000 | 1.0000 |
| a1_primary_mcnemar_majority | Sonnet 4.6 − GLM 5 | +0.033 | [+0.000, +0.089] | 1.0000 | 1.0000 |
| a1_primary_mcnemar_majority | Kimi K3 − GLM 5 | +0.033 | [-0.011, +0.089] | 1.0000 | 1.0000 |
| a1_primary_wilcoxon | Sonnet 4.6 − Kimi K3 | +0.000 | [-0.033, +0.033] | 0.6547 | 0.7145 |
| a1_primary_wilcoxon | Sonnet 4.6 − GLM 5 | +0.033 | [+0.000, +0.089] | 0.1797 | 0.5391 |
| a1_primary_wilcoxon | Kimi K3 − GLM 5 | +0.033 | [-0.011, +0.089] | 0.3573 | 0.7145 |
| a2_primary_mcnemar_majority | Sonnet 4.6 − Kimi K3 | +0.011 | [+0.000, +0.033] | 1.0000 | 1.0000 |
| a2_primary_mcnemar_majority | Sonnet 4.6 − GLM 5 | +0.000 | [+0.000, +0.000] | 1.0000 | 1.0000 |
| a2_primary_mcnemar_majority | Kimi K3 − GLM 5 | -0.011 | [-0.033, +0.000] | 1.0000 | 1.0000 |
| a2_primary_wilcoxon | Sonnet 4.6 − Kimi K3 | +0.011 | [+0.000, +0.033] | 0.3173 | 0.9519 |
| a2_primary_wilcoxon | Sonnet 4.6 − GLM 5 | +0.000 | [+0.000, +0.000] | 1.0000 | 1.0000 |
| a2_primary_wilcoxon | Kimi K3 − GLM 5 | -0.011 | [-0.033, +0.000] | 0.3173 | 0.9519 |
| a3_primary_wilcoxon | Sonnet 4.6 − Kimi K3 | -0.024 | [-0.058, +0.000] | 0.1025 | 0.1025 |
| a3_primary_wilcoxon | Sonnet 4.6 − GLM 5 | +0.062 | [-0.004, +0.132] | 0.0350 | 0.0700 |
| a3_primary_wilcoxon | Kimi K3 − GLM 5 | +0.086 | [+0.031, +0.151] | 0.0014 | 0.0043 |

## Quality–cost Pareto frontiers

- A1: GLM 5, Sonnet 4.6, Kimi K3
- A2: GLM 5
- A3: GLM 5, Sonnet 4.6, Kimi K3

## Original-v1 bridge (descriptive only)

Different protocols are not directly comparable; Sonnet 4.6 is the bridge.

| Task | Metric | original-v1 | price-matched-v2 |
|---|---|---:|---:|
| A1 | functional_correct | 0.900 | 0.899 |
| A2 | content_correct | 1.000 | 1.000 |
| A3 | ndcg_at_5 | 0.965 | 0.976 |
