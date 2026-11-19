# Independent Benchmark v1 Audit

**Date:** 2026-11-18

**Scope:** frozen `independent-v1-frozen` data, prompts, records, saved outputs, and deterministic scorers

**Status:** offline audit complete; no model calls; raw and frozen artifacts unchanged

## Executive finding

The published v1 tables are reproducible from the saved evidence. All 90 records were re-read and every parseable response was rescored with the frozen implementation: there were **zero score mismatches**, **zero case-hash mismatches**, **zero prompt-hash mismatches**, and **zero missing required artifacts**.

The reported headline numbers are therefore traceable, but several benchmark-design and interpretation issues materially limit model-ranking claims:

1. A1 is at the ceiling and its record `status=passed` means operational execution, not functional correctness.
2. A2 conflates extraction content with wrapper/schema compliance unless the two are reported separately.
3. A3 frozen grounding v1 rejects valid surface forms that occur in the candidate abstract itself.
4. All three tasks are small and synthetic; the generator's Claude-family authorship remains a potential design bias even though labels are deterministic.

The planned 18-item blinded human spot-check is now complete. It confirms the A1 functional and A2 decomposed scoring findings, and identifies additional weaknesses in A1 bug localization and A3 prose/citation evaluation. Full results are in `results/reports/human_review_results.md`.

Machine-readable audit evidence is in `results/processed/independent/audit_v1.json`. Reproduce it with:

```bash
.venv/bin/python -m experiments.audit_independent_v1
```

## Evidence integrity

| Check | A1 | A2 | A3 |
|---|---:|---:|---:|
| Records | 30 | 30 | 30 |
| Unique cases | 10 | 10 | 10 |
| Models | 3 | 3 | 3 |
| Missing saved artifacts | 0 | 0 | 0 |
| Case-hash mismatches | 0 | 0 | 0 |
| Prompt-hash mismatches | 0 | 0 | 0 |
| Frozen rescore mismatches | 0 | 0 | 0 |

The audit did not modify the frozen JSONL files or any saved response.

## A1 — Python debugging

### Confirmed

- Reference implementations pass every stored hidden check.
- Each injected buggy implementation fails at least one stored hidden check.
- Saved sandbox outputs reproduce the recorded scores.
- Observed functional correctness is 10/10 for model A, 9/10 for B, and 10/10 for C.

### Issues

**Ceiling effect.** Twenty-nine of 30 outputs pass every hidden test. With only one failing model output, the task has little power to distinguish these models.

**Operational status is not correctness.** `score_a1` hard-passes whenever the submitted module loads and the harness runs. It does not require all hidden checks to pass. Consequently, B's incorrect `a1_10_merge_intervals` output is stored with `status=passed` while `functional_correct=false`. Reports must not describe A1 `status` as functional success.

**Finite-suite vulnerability.** The audit constructed two deliberately non-equivalent implementations that pass every stored hidden check:

- `a1_01_moving_average`: 8/8 hidden checks, but it fails a valid unseen `k=3` example.
- `a1_02_is_leap`: 8/8 hidden checks, but it fails the valid leap year 2800.

These are adversarial demonstrations, not claims that an evaluated model used such code. They establish that test passage is evidence of correctness, not proof of specification equivalence.

**Localization is secondary.** B repaired `a1_09_top_k` functionally but did not name the expected buggy function; the current hard gate does not enforce diagnostic quality.

### v2 response

The candidate v2 set contains 30 cases across 15 task families, with two different mutations per family, 10 cases at each difficulty, and at least 10 multi-defect/interacting-defect cases. Every reference and injected mutation is executable-tested during generation.

## A2 — Information extraction

### Confirmed

- Ground truth is derived from the deterministic source record used to render each document.
- Frozen field normalization, null scoring, and schema-key checks reproduce exactly.
- No evaluated model hallucinated a value for a genuinely missing field.
- B's errors reproduce: two weekly-to-monthly rent failures, one undiscounted purchase-order total, and one invalid response.
- C's seven wrapper-related failures reproduce from saved output.

### Content versus schema versus operation

The seven C failures contain a bare extraction object rather than the required `{"fields": ...}` envelope. Offline recovery gives all seven **content F1 = 1.0** and all fields correct. They remain schema and operational failures under frozen v1.

This yields two simultaneously valid statements:

- strict pipeline result: A 10/10, B 6/10, C 3/10 all-fields-correct;
- recoverable extraction content: A 10/10, B 6/10, C 10/10.

The second is a post-hoc diagnostic and cannot replace the first. It shows that model ranking is sensitive to whether the research question concerns extraction ability or immediate pipeline usability.

**Limited diversity.** v1 uses five synthetic document families, each rendered twice. This is insufficient evidence for broad document-extraction performance.

### v2 response

The candidate v2 set has 10 document families and 30 cases across email, tables, manifests, timelines, listings, notices, logs, and other formats. It includes missing fields, superseded values, distractors, discounts, weekly/annual conversions, pounds-to-kilograms, square-feet-to-square-metres, and boolean conflicts. The scorer returns separate `content_correct`, `schema_compliant`, and `operational_success` fields.

## A3 — Controlled literature review

### Confirmed

- This benchmark is controlled ranking over a supplied synthetic corpus. It is **not live web search**.
- Relevance grades are deterministic by construction and frozen rankings reproduce.
- A3 separately records ranking, grade-2 recall, grounding, citations, and output validity.
- C has four 4,096-token truncations and one five-ID validation failure.
- B's lowest ranking (`a3_03`, nDCG@5 0.668) places hard negatives above direct matches.

### Grounding scorer issue

The generator deliberately paraphrases topic and method terms in abstracts to defeat a lexical baseline, while frozen v1 compares structured claims to canonical labels. A claim can therefore copy the supplied abstract accurately and still fail grounding.

Post-hoc v1.1 accepts only documented surface forms for the cited document. Mean parsed-output grounding changes as follows:

| Model | Frozen v1 | Post-hoc v1.1 |
|---|---:|---:|
| A | 0.838 | 0.996 |
| B | 0.965 | 0.972 |
| C | 0.875 | 0.994 |

This reverses the grounding ranking. v1 remains the frozen primary score; v1.1 is a scorer-sensitivity diagnostic.

### v2 response and remaining gate

The candidate v2 set has 30 queries and 20 controlled candidates per query, with explicit direct-match, partial-match, prior-work hard-negative, and unrelated strata. Ranking, citation validity, and claim grounding are scored separately. Labels were not produced by an evaluated model, but are still marked `candidate_pending_human_review`; A3 v2 must not be frozen or sent to models until those labels receive independent human adjudication.

## Benchmark-author bias

Deterministic labels prevent an evaluated model from judging its own outputs, but they do not eliminate author bias. Claude-family authorship may influence:

- which bug patterns and document ambiguities were selected;
- prose style and instruction phrasing;
- what counts as a difficult distractor;
- canonical terminology and paraphrase lists;
- the distribution of cases on which a Claude-family model may be especially familiar.

The new Codex-authored candidate set changes authorship but does not, by itself, establish neutrality. Mitigations are independent human review, disclosed provenance, greater task diversity, explicit label rationales, anchor cases, and avoiding any prompt/scorer adjustment after model outputs are observed.

## Blinded human spot-check

The user completed all 18 preselected items before model identities and automatic scores were joined. The sample contains two outputs per task-model cell and intentionally over-represents failures, borderline cases, and scorer disagreements. It is descriptive validation, not an unbiased estimate of model accuracy.

| Task | Items | Correct | Mostly correct | Incorrect |
|---|---:|---:|---:|---:|
| A1 | 6 | 5 | 0 | 1 |
| A2 | 6 | 3 | 3 | 0 |
| A3 | 6 | 0 | 5 | 1 |

Confirmed agreement and new findings:

- A1 functional correctness agreed on 6/6 reviewed outputs.
- A1 localization has a concrete false reject: `a1_09_top_k` correctly identifies the mutated `rank_key` helper, while the frozen scorer searches only for `top_k`.
- A2 strict content agreed on 5/6 because a wrapper-only failure has perfect content. Recovered content, schema compliance, and operational usability each agreed on 6/6.
- A3 operational usability agreed on 5/6. The disagreement is a parsed four-ID response that is usable but violates the benchmark's exact-five rule.
- All five parsed reviewed A3 outputs passed frozen `citation_consistent`, but only two received a perfect human citation score. The frozen check establishes citation structure, not accurate prose attribution.
- A3 human review confirms both sides of the grounding problem: v1 rejects faithful paraphrases, while structured-claim scoring can miss unsupported prose not represented in the claim list.

Frozen scores remain unchanged. These judgments are incorporated only as human validation and scorer-design evidence.

## Statistical limits

Each v1 model-task cell has only 10 cases and one run. A 10/10 rate has Wilson 95% interval approximately [0.72, 1.00]; 9/10 is approximately [0.60, 0.98]. Most apparent differences are not stable general rankings. No causal statement about model internals is supported.

## Disposition

The v1 records and scores should remain frozen and citable as exploratory evidence. Future claims should pair correctness with operational reliability and disclose scorer sensitivity. Independent v2 remains a candidate protocol pending the human-review and freeze gates in `docs/INDEPENDENT_V2_PLAN.md`.
