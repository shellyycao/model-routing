# Independent Benchmark v2 Post-hoc / Exploratory Analysis

**Status:** post-hoc / exploratory; not prospectively registered  
**Rules:** `posthoc-v2-rules-1.0.1`, committed before rescoring  
**Frozen results remain unchanged.**

The base rules were committed before post-hoc computation. Implementation began before the manager's CP1 review was relayed, but no rescoring had been run; the required R-1 disclosure and R-2 implementation amendment were handled before this report was computed.

## Prospective frozen results

The frozen primary outcomes are repeated for context; none is replaced by a relaxed view.

| Task | Model | Frozen primary |
|---|---|---:|
| A1 | Claude Sonnet 4.6 | 90.0% |
| A1 | Amazon Nova Pro | 56.7% |
| A1 | OpenAI gpt-oss-120b | 86.7% |
| A2 | Claude Sonnet 4.6 | 100.0% |
| A2 | Amazon Nova Pro | 83.3% |
| A2 | OpenAI gpt-oss-120b | 100.0% |
| A3 | Claude Sonnet 4.6 | nDCG 1.002 |
| A3 | Amazon Nova Pro | nDCG 0.995 |
| A3 | OpenAI gpt-oss-120b | nDCG 0.969 |

## A1 location-format sensitivity

The normalized rule credits a gold semantic region when the response identifies its containing function by name or by an overlapping line range. Multiple gold regions in one function can therefore receive the same function-level credit.

| Model | Frozen recall | Normalized recall | Wrong location | Format mismatch | Bare `N-M` only | Fixed span only |
|---|---:|---:|---:|---:|---:|---:|
| Claude Sonnet 4.6 | 0.000 | 0.650 | 6 | 11 | 0 | 0 |
| Amazon Nova Pro | 0.000 | 0.617 | 10 | 7 | 0 | 0 |
| OpenAI gpt-oss-120b | 0.000 | 0.150 | 2 | 42 | 0 | 0 |

## A2 frozen errors and manual taxonomy

Two aliases are at the 100% frozen content-correctness ceiling. Categories below follow the fixed field/family map and do not alter frozen labels.

| Model | Frozen correct | Error fields | Frozen labels | Manual categories |
|---|---:|---:|---|---|
| Claude Sonnet 4.6 | 100.0% | 0 | `{}` | `{}` |
| Amazon Nova Pro | 83.3% | 5 | `{"wrong_value": 5}` | `{"field_omission": 2, "unit_scale_conversion": 3}` |
| OpenAI gpt-oss-120b | 100.0% | 0 | `{}` | `{}` |

## A3 ranking sensitivity

Valid-only nDCG is at or above the ceiling described in the brief for every alias. The strict view sets invalid rankings to zero; the deduplicated view keeps first occurrences in the submitted top five and pads removed duplicates with zero gain.

| Model | Valid | Frozen | Valid-only | Strict invalid=0 | Deduplicated | Frozen >1 |
|---|---:|---:|---:|---:|---:|---:|
| Claude Sonnet 4.6 | 29/30 | 1.002 | 0.998 | 0.965 | 0.997 | 1 |
| Amazon Nova Pro | 29/30 | 0.995 | 0.991 | 0.958 | 0.990 | 1 |
| OpenAI gpt-oss-120b | 22/30 | 0.969 | 0.998 | 0.732 | 0.954 | 3 |

## A3 grounding sensitivity

R1 normalizes only the fixed attribute-key vocabulary and retains the all-citations rule. R2 additionally allows any cited document to support the claim. Values always use the frozen equality rule.

| Model | Attribute-key coverage | Frozen stored | Frozen recomputed | R1 normalized keys | R2 any citation | Failure reasons |
|---|---:|---:|---:|---:|---:|---|
| Claude Sonnet 4.6 | 3.1% | 0.000 | 0.000 | 0.022 | 0.022 | `{"attribute_key_mismatch": 218}` |
| Amazon Nova Pro | 28.6% | 0.018 | 0.018 | 0.281 | 0.284 | `{"attribute_key_mismatch": 229, "supported": 6}` |
| OpenAI gpt-oss-120b | 72.9% | 0.293 | 0.293 | 0.456 | 0.456 | `{"attribute_key_mismatch": 175, "supported": 111, "value_mismatch": 61}` |

The prompt never specified the allowed claim-attribute vocabulary while the schema accepted arbitrary strings. Frozen, R1, and R2 grounding values are therefore lower bounds conditional on an unspecified attribute vocabulary; differences between models must not be interpreted as grounding ability. A future protocol should provide an enumerated attribute vocabulary in both prompt and schema. Doing so changes comparability with the existing 270 cells and requires a user decision before a new freeze.

## Exploratory paired statistics

Effects are first model minus second model. Holm correction is within the pre-defined A1 (3), A2 (3), and A3 (9) families. Non-significance is not evidence of equivalence.

### Binary primary outcomes

| Task | Pair | Difference | 95% paired bootstrap CI | Discordant first/second | Exact p | Holm p |
|---|---|---:|---:|---:|---:|---:|
| A1 | Claude Sonnet 4.6 − Amazon Nova Pro | +0.333 | [+0.167, +0.500] | 10/0 | 0.0020 | 0.0059 |
| A1 | Claude Sonnet 4.6 − OpenAI gpt-oss-120b | +0.033 | [-0.067, +0.133] | 2/1 | 1.0000 | 1.0000 |
| A1 | Amazon Nova Pro − OpenAI gpt-oss-120b | -0.300 | [-0.467, -0.133] | 0/9 | 0.0039 | 0.0078 |
| A2 | Claude Sonnet 4.6 − Amazon Nova Pro | +0.167 | [+0.033, +0.300] | 5/0 | 0.0625 | 0.1875 |
| A2 | Claude Sonnet 4.6 − OpenAI gpt-oss-120b | +0.000 | [+0.000, +0.000] | 0/0 | 1.0000 | 1.0000 |
| A2 | Amazon Nova Pro − OpenAI gpt-oss-120b | -0.167 | [-0.300, -0.033] | 0/5 | 0.0625 | 0.1875 |

### A3 paired nDCG

| View | Pair | Difference | 95% paired bootstrap CI | Nonzero | Wilcoxon p | Holm p |
|---|---|---:|---:|---:|---:|---:|
| `frozen_all_case (defective)` | Claude Sonnet 4.6 − Amazon Nova Pro | +0.007 | [-0.005, +0.019] | 9 | 0.2337 | 1.0000 |
| `frozen_all_case (defective)` | Claude Sonnet 4.6 − OpenAI gpt-oss-120b | +0.033 | [-0.012, +0.108] | 11 | 0.6528 | 1.0000 |
| `frozen_all_case (defective)` | Amazon Nova Pro − OpenAI gpt-oss-120b | +0.026 | [-0.019, +0.103] | 12 | 0.7825 | 1.0000 |
| `strict_invalid_zero` | Claude Sonnet 4.6 − Amazon Nova Pro | +0.007 | [-0.093, +0.105] | 9 | 0.2838 | 1.0000 |
| `strict_invalid_zero` | Claude Sonnet 4.6 − OpenAI gpt-oss-120b | +0.233 | [+0.065, +0.401] | 11 | 0.0093 | 0.0840 |
| `strict_invalid_zero` | Amazon Nova Pro − OpenAI gpt-oss-120b | +0.226 | [+0.058, +0.420] | 13 | 0.0505 | 0.3536 |
| `deduplicated_first5` | Claude Sonnet 4.6 − Amazon Nova Pro | +0.007 | [-0.002, +0.017] | 9 | 0.2050 | 1.0000 |
| `deduplicated_first5` | Claude Sonnet 4.6 − OpenAI gpt-oss-120b | +0.043 | [+0.003, +0.112] | 11 | 0.0229 | 0.1834 |
| `deduplicated_first5` | Amazon Nova Pro − OpenAI gpt-oss-120b | +0.036 | [-0.006, +0.108] | 12 | 0.2972 | 1.0000 |

The project environment did not contain SciPy. The Wilcoxon calculation therefore uses the committed standard-library implementation of the same two-sided, zero-dropped, tie-corrected normal approximation without continuity correction; this deviation is explicit in processed metadata.
The A3 Holm family pools nine highly correlated tests across three related ranking views, so its correction is deliberately conservative.

## Limits

- All analyses in this document are post-hoc / exploratory.
- A1 normalized matching is function-level and may credit multiple semantic regions in one function.
- A3 grounding relaxations test formatting and citation aggregation only; they do not validate prose quality.
- The committed `task → topic` attribute alias is a judgment call; no outcome-based vocabulary was added.
- Paired tests have n=30 and ceiling/tie effects; effect intervals matter more than thresholded p-values.
- Frozen results and raw records were not changed.

## Reproduction

```bash
.venv/bin/python -m experiments.analyze_independent_v2_posthoc
.venv/bin/python -m pytest -q tests/test_independent_v2_posthoc.py
```
