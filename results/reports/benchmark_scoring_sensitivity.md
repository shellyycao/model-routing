# Independent Benchmark Scoring Sensitivity

**Mode:** offline saved-output analysis

**Primary evidence:** frozen v1 scores

**Alternative views:** post-hoc diagnostics; never substitutes for or pools with v1

Reproduce with:

```bash
.venv/bin/python -m experiments.analyze_independent_sensitivity
```

Machine-readable output is `results/processed/independent/scoring_sensitivity.json`.

## A1 — Ceiling and criterion choice

| Model | Operational status | Functional correctness | Mean hidden pass rate | Bug-location rate | Median latency |
|---|---:|---:|---:|---:|---:|
| A | 10/10 | 10/10 | 1.000 | 1.00 | 2.13 s |
| B | 10/10 | 9/10 | 0.988 | 0.80 | 1.41 s |
| C | 10/10 | 10/10 | 1.000 | 1.00 | 2.39 s |

Operational status alone produces a three-way tie because the hard gate asks whether code loaded, not whether all hidden checks passed. Functional scoring places A and C above B, while latency places B first. The n=10 Wilson intervals overlap broadly: 10/10 is approximately [0.72, 1.00], and 9/10 approximately [0.60, 0.98]. The model ranking is therefore criterion-dependent and underpowered.

## A2 — Content versus pipeline reliability

| Model | Strict all-fields correct | Schema/parse operational | Recoverable content correct | Content F1 when parsed |
|---|---:|---:|---:|---:|
| A | 10/10 | 10/10 | 10/10 | 1.000 |
| B | 6/10 | 9/10 | 6/10 | 0.944 |
| C | 3/10 | 3/10 | 10/10 | 1.000 |

Under the frozen pipeline question, the ranking is A > B > C. Under recoverable extraction content, A = C > B. This is not a contradiction: C omitted the required wrapper seven times but its inner field objects were correct. The recovery was designed after observing outputs and is a diagnostic only.

The result is strongly interface-sensitive. Any claim that C is poor at extraction based solely on 3/10 would conflate content with schema compliance; any claim that it is fully reliable based on 10/10 recovered content would ignore pipeline failure.

## A3 — Parsed-only, all-call, and grounding sensitivity

| Model | Valid output | nDCG parsed only | nDCG with invalid calls = 0 | Grounding v1 | Grounding v1.1 | Median latency |
|---|---:|---:|---:|---:|---:|---:|
| A | 10/10 | 0.995 | 0.995 | 0.838 | 0.996 | 7.59 s |
| B | 10/10 | 0.962 | 0.962 | 0.965 | 0.972 | 4.29 s |
| C | 5/10 | 0.992 | 0.595 | 0.875 | 0.994 | 22.15 s |

Parsed-only nDCG ranks A ≈ C > B. Counting invalid or truncated calls as operational failures ranks A > B > C. Frozen grounding v1 ranks B > C > A; post-hoc v1.1 ranks A ≈ C > B. Both changes are large enough to alter a verbal “best model” conclusion.

## Difficulty and sample size

v1 difficulty tiers are too sparse and inconsistent across the three tasks for a reliable difficulty-response curve. The candidate v2 protocol pre-registers exactly 10 easy, 10 medium, and 10 hard cases per task so this analysis can be performed prospectively.

Each v1 cell is n=10 with one generation per case. Latency and token medians are descriptive; no repeat-based variability is available. No significance claim is made.

## Human spot-check sensitivity

The completed 18-item blinded review was purposively stratified across every task-model cell and emphasized disagreements. It is not an accuracy sample.

| Comparison | Agreement |
|---|---:|
| A1 functional correctness | 6/6 |
| A2 strict content correctness | 5/6 |
| A2 recoverable content correctness | 6/6 |
| A2 schema compliance | 6/6 |
| A2 operational usability | 6/6 |
| A3 operational usability | 5/6 |

The A2 result supports reporting recoverable content beside, not instead of, strict pipeline success. A3 shows lower construct alignment: all five parsed reviewed outputs passed structural `citation_consistent`, but only two received a perfect human citation score. Human review also found that high nDCG does not rule out important fifth-rank or synthesis-framing errors, and that structured grounding can miss unsupported prose omitted from the claim list.

## Stable conclusions

- A is the only model with both high content correctness and high operational reliability on all v1 tasks.
- B is consistently faster and more token-efficient, with task-specific correctness costs.
- C often has strong content when a response is usable, but v1 output-format and token-limit interactions sharply reduce operational reliability.
- The exact ranking is not stable across content, schema, grounding, and operational criteria.

## Reporting rule

Future tables must name the criterion in the column heading, show invalid-output denominators, and keep post-hoc scores beside rather than in place of frozen scores. Scores from v1 and v2 must not be treated as directly interchangeable.
