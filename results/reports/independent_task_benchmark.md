# Part A extension: Independent task benchmarks (A1 Debugging, A2 Extraction, A3 Literature)

**Part A, independent task-specific model evaluation.** This report is separate from Part B (workflows) and Part C (routing). No score here enters routing data.

| Item | Value |
|---|---|
| Frozen benchmark | tag `independent-v1-frozen` (`45a1d74`); plan in `docs/INDEPENDENT_BENCHMARK_PLAN.md` |
| Prompts | `prompts/independent_v1` |
| Settings | `maxTokens` 4096 and temperature 0 for every model |
| Runs | 10 cases per task × 3 models = **90 runs, 0 void_infra** |
| Calls and tokens (ledger) | 90 calls, 98.7K input and 73.7K output tokens, 0 failed attempts |
| Cost | `unavailable` (prices unverified) |
| Sandbox | A1 code ran only in the verified sandbox, 30/30 executions |
| Reproduce | `python -m experiments.analyze_independent` (tables) and `python -m experiments.rescore_independent_posthoc` (secondary views) |

**Ground truth:**
- Every label is built by code: the reference function behind each injected bug, the source record of each rendered document, and relevance defined by construction. No evaluated model produced a label.
- **Limitation:** the generators were written by a Claude model (Opus). That is the same vendor as model A, Claude Sonnet 4.6. The user waived the planned spot-check.

**Evidence status: EXPLORATORY.**
- There are n = 10 cases per model × task, and one run each.
- For example, 10/10 has a Wilson 95% interval of [0.72, 1.00], and 6/10 has [0.31, 0.83].
- No significance tests were run. Three models do not establish general rankings.

## 1. Model × Task comparison (frozen v1 scoring, primary)

| Task | Model | Hard gate passed | Primary correctness | Secondary quality | Generation latency, median s | Input / output tokens, median | Reasoning chars, median |
|---|---|---|---|---|---|---|---|
| **A1 Debugging** | Claude Sonnet 4.6 | 10/10 | **functional 10/10** [0.72–1] | hidden tests 100%; named the buggy function 10/10 | 2.1 | 496 / 194 | — |
| | Amazon Nova Pro | 10/10 | functional 9/10 [0.60–0.98] | hidden tests 98.8%; named the function 8/10 | **1.4** | 451 / 180 | — |
| | OpenAI gpt-oss-120b | 10/10 | **functional 10/10** [0.72–1] | hidden tests 100%; named the function 10/10 | 2.4 | 488 / 319 | 636 |
| **A2 Extraction** | Claude Sonnet 4.6 | **10/10** | **all fields correct 10/10** [0.72–1] | F1 1.00; null handling 1.00; 0 hallucinated | 1.1 | 470 / 101 | — |
| | Amazon Nova Pro | 9/10 | all fields correct 6/10 [0.31–0.83] | F1 0.94 (on the 9 parsed); null handling 1.00; 0 hallucinated | **0.9** | 423 / 94 | — |
| | OpenAI gpt-oss-120b | 3/10 | all fields correct 3/10 [0.11–0.60] | F1 1.00 on the 3 parsed; see §3, A2 | 2.3 | 475 / 385 | 1,146 |
| **A3 Literature** | Claude Sonnet 4.6 | **10/10** | **nDCG@5 0.995** | grade-2 recall 1.00; grounding 0.84 (v1.1: 1.00); citations consistent 10/10 | 7.6 | 2,573 / 1,469 | — |
| | Amazon Nova Pro | **10/10** | nDCG@5 0.962 (minimum 0.67) | grade-2 recall 0.95; grounding 0.97 (v1.1: 0.97) | **4.3** | 2,314 / 806 | — |
| | OpenAI gpt-oss-120b | 5/10 | nDCG@5 0.992 (on the 6 parsed) | grade-2 recall 1.00; grounding 0.88 (v1.1: 0.99) | 22.2 | 2,240 / 3,833 | 10,855 |

**Notes on the table:**
- **Precision@5:** each query has exactly 4 grade-2 documents, so precision@5 can be at most 0.8. All models came close: Claude 0.80, Nova 0.76, gpt-oss 0.80 (on the parsed runs).
- **Keyword baseline:** a deterministic keyword baseline scores nDCG@5 = 0.07 on the same A3 queries, so the relevance task is not lexically trivial.
- **v1.1 grounding:** a post-hoc secondary score (§3); the frozen v1 score is primary.

## 2. Best model under each explicitly defined criterion

| Criterion | A1 Debugging | A2 Extraction | A3 Literature |
|---|---|---|---|
| Correctness (primary metric) | Claude = gpt-oss (10/10); Nova 9/10, within noise | **Claude** (10/10 all fields correct) | Claude (nDCG 0.995) ≈ gpt-oss (0.992 on parsed runs) > Nova (0.962) |
| Schema compliance / reliability | all 10/10 | **Claude** 10/10 > Nova 9/10 ≫ gpt-oss 3/10 | Claude = Nova 10/10 ≫ gpt-oss 5/10 |
| Evidence grounding (v1, primary) | n/a | n/a | Nova (0.97) > gpt-oss (0.88) > Claude (0.84); **v1.1: Claude ≈ gpt-oss (≥0.99) > Nova (0.97)** |
| Speed (median latency) | Nova 1.4 s | Nova 0.9 s | Nova 4.3 s (gpt-oss 22 s) |
| Token economy (median output) | Nova 180 | Nova 94 | Nova 806 |
| Verified cost | unavailable | unavailable | unavailable |

**No single winner on every criterion:**
- **Claude Sonnet 4.6** is the only model at or near the top for correctness *and* reliability on all three tasks.
- **Nova Pro** is consistently the fastest and most token-frugal, at a small to moderate accuracy cost.
- **gpt-oss-120b** is as accurate as Claude when it produces a valid response. But it failed the required output format (A2) or the output-length limit (A3) in about half of those cases.

## 3. Concrete failure patterns (from saved artifacts in `results/raw/runs/indepA*`)

**A1, debugging (near the ceiling).**
- Nova's one functional failure is the mutable-default-argument case: it kept the shared-state bug. Nova also named the wrong location in 2 of 10 bug reports while still fixing the code.
- Otherwise every model fixed every bug, so **A1 shows a ceiling effect** and does not discriminate well. The single-bug, single-function cases are too easy for these models.

**A2, extraction.**
- **Nova: 3 value errors and 1 broken JSON.**
  - Rental listings, 2 errors: it did not convert the weekly rent to monthly (weekly × 52 / 12), as the field description requires.
  - Purchase order, 1 error: it reported the list price instead of the total *after* the discount.
  - In both cases, the rule for resolving the ambiguity was in the schema description and was not applied.
- **gpt-oss: 7 schema failures, all the same.** It returned the extracted object without the required `{"fields": …}` wrapper. **Post-hoc content diagnostic** (`results/processed/independent/posthoc.json`): unwrapped, all 7 have **F1 = 1.0, every field correct, 0 hallucinations**. Its extraction content was perfect; its compliance with the response schema was not. That matters in a pipeline that parses structured output, but it is a different failure from wrong extraction.
- **No model hallucinated a value for a genuinely missing field:** null handling was 1.00 for every model.

**A3, literature.**
- **gpt-oss:**
  - 4 of 10 responses were truncated at 4,096 output tokens. Its separate reasoning text had a median of about 10.9K characters, and the reasoning counts toward the output limit. This is the same mechanism seen in Part A cleaning.
  - 1 response ranked only 4 documents.
- **Nova's ranking errors:** its lowest nDCG was 0.67, on a query where it placed hard negatives (documents that mention the query's topic and method only in a "prior work" sentence) above true matches.
- **Grounding, primary v1 scorer:**
  - Nova 0.97, gpt-oss 0.88, Claude 0.84.
  - **Most of Claude's and gpt-oss's "ungrounded" claims are a scorer artifact.** They are topic or method claims that quote the abstract's paraphrase ("message-passing networks over relational graphs"), while the frozen scorer compares against the canonical label ("graph neural networks"). This mismatch came from the pre-run fix that paraphrased abstracts to defeat keyword matching.
  - **Post-hoc v1.1** accepts the documented paraphrases of the cited document's own topic or method; anything else still fails. Under v1.1, grounding is Claude 1.00, gpt-oss 0.99 and Nova 0.97.
  - The remaining genuine errors:
    - Claude and Nova each cited "satellite imagery" (the data description) as a dataset name.
    - Nova attributed a wrong value (0.957 vs 0.614).
    - Nova made 2 wrong method attributions.
- **Claim volume:** Claude made the most claims (median 30, vs Nova 13), so it had more opportunities to err. Grounding rates are per claim.

## 4. Quality–cost trade-offs (tokens and latency; dollars unavailable)

| Task | Trade-off |
|---|---|
| A1 | All three models are correct, so the trade-off is purely efficiency: **Nova** is fastest and cheapest in tokens, with one shared-state miss. |
| A2 | **Claude** is the only model that was both correct and reliable, at about 1.1 s and about 100 output tokens. Nova is about 20% faster but got 4 of 10 documents wrong. |
| A3 | **Claude** gave the best rankings and, under v1.1, grounding at 7.6 s and 1.5K output tokens. **Nova** is about 45% faster and uses about half the tokens, with slightly worse ranking. gpt-oss is about 3× slower, uses about 2.6× the output tokens, and was truncated in 4 of 10. |

## 5. Uncertainty and limitations
- **Sample size:** n = 10 per cell and single runs, so most differences are within the Wilson intervals. The only clear separations are:
  - A2: Claude vs gpt-oss on schema compliance (10/10 vs 3/10);
  - A3: Claude and Nova vs gpt-oss on reliability (10/10 vs 5/10).
- **Ceiling effect:** A1 does not discriminate between the models.
- **Synthetic data:** the A3 corpus is synthetic and controlled, **not live literature search**. A2 documents are template-rendered.
- **Ground-truth author:** a Claude-family model wrote the generators. Labels are mechanical, but the case design could still favour one vendor's style. The spot-check was waived.
- **Interface effects:**
  - The A2 `{"fields": …}` wrapper and the uniform 4,096-token limit affect gpt-oss specifically.
  - These are fixed protocol choices applied identically to every model, and they are reported as such.
- **Post-hoc secondary scores:** A3 grounding v1.1 and the A2 content diagnostic were created after seeing outputs. They are reported beside the frozen scores and never replace them.
- **Scorer flaw:** the A3 grounding mismatch was introduced by the pre-run paraphrase fix and caught only after the run, which is why the frozen v1 grounding numbers understate Claude and gpt-oss.
- **No causal claims:** the explanations above describe observed artifacts (truncation, missing wrapper, unconverted units, ranking of hard negatives). They make no claims about model internals.
