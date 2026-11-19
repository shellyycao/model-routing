# Phase 1: Model specialization by task (Experiment A, prospective v3)

**Research question:** which LLM is best suited to which task, and why?

**Scope:** this is a Phase 1 report on independent stage-level evaluation only. It is deliberately separate from the Phase 2 workflow-routing results (Experiment B, which was still running when this was written).

| Item | Value |
|---|---|
| Data | `results/raw/stage_benchmark/expA_stage_v3.jsonl`: 36 `StageBenchmarkRecord`s = 3 models × 3 tasks × 4 projects, 1 run each, no repeats |
| Protocol | v3, frozen at tag `benchmark-v3-frozen` (`22a56e6`): `prompts/v3`, reporting validator v3, cleaning and analysis validators v2 |
| Calls | Fresh; `maxTokens` 4096 and temperature 0 for all models; identical prompts per task |
| Inputs | **Canonical** for every task: raw CSV for cleaning, reference-cleaned CSV for analysis, verified findings for reporting. Upstream errors therefore cannot affect these results. |
| Projects | customer_churn, energy_consumption, retail_sales, support_operations (a two-file join). retail_sales is pilot-exposed (see the protocol, §12). |
| Reproduce | `.venv/bin/python -m experiments.phase1_specialization`, which writes every number below to `results/reports/phase1_tables.json` together with source file hashes |
| Cost | No new paid calls were made for this analysis |

**Evidence status: EXPLORATORY.**
- Each model × task cell has **n = 4** (one run per project).
- A 4/4 pass rate has a Wilson 95% interval of [0.51, 1.00], and 0/4 has [0, 0.49].
- Only differences of about 4/4 vs 0/4 are clearly beyond sampling noise.
- No significance tests were run. These three models do not establish general rankings.

## 1. Model × Task comparison

A stage **passes** when it meets every mandatory requirement: parseable structured output, successful sandbox execution, and all mandatory validator checks.

**Key quality metrics:**
- cleaning: `cleaning_correctness`
- analysis: `numerical_accuracy`
- reporting: `numerical_consistency`

Quality values are medians over the runs that were validated, given as [min–max].

| Task | Model | Pass k/4 (Wilson 95%) | Structured output parsed | Code executed OK | Key quality median [min–max] (n) | Generation latency, median s | Input tokens, median | Output tokens, median | Reasoning text, median chars |
|---|---|---|---|---|---|---|---|---|---|
| Cleaning | Claude Sonnet 4.6 | **3/4** (0.30–0.95) | 4/4 | 4/4 | 1.0 [0.63–1.0] (4) | 19.3 | 2,046 | 3,036 | — |
| Cleaning | Amazon Nova Pro | 0/4 (0–0.49) | 3/4 | 0/3 | 0.0 [0–0] (3) | **10.0** | 2,127 | 1,894 | — |
| Cleaning | OpenAI gpt-oss-120b | 2/4 (0.15–0.85) | 2/4 | 2/2 | 1.0 [1.0–1.0] (2) | 22.8 | 1,845 | 4,088 | 5,813 |
| Analysis | Claude Sonnet 4.6 | **4/4** (0.51–1) | 4/4 | 4/4 | 1.0 [1.0–1.0] (4) | 10.1 | 2,151 | 1,717 | — |
| Analysis | Amazon Nova Pro | 0/4 (0–0.49) | 4/4 | 1/4 | 0.0 [0–0.83] (4) | **6.2** | 2,275 | 1,502 | — |
| Analysis | OpenAI gpt-oss-120b | **4/4** (0.51–1) | 4/4 | 4/4 | 1.0 [1.0–1.0] (4) | 7.7 | 1,923 | 2,171 | 2,544 |
| Reporting | Claude Sonnet 4.6 | **3/4** (0.30–0.95) † | 4/4 | n/a | 1.0 [1.0–1.0] (4) | 14.4 | 3,329 | 1,931 | — |
| Reporting | Amazon Nova Pro | 2/4 (0.15–0.85) | 4/4 | n/a | 1.0 [1.0–1.0] (4) | 8.1 | 3,180 | 1,627 | — |
| Reporting | OpenAI gpt-oss-120b | 2/4 (0.15–0.85) † | 4/4 | n/a | 1.0 [1.0–1.0] (4) | **7.6** | 2,849 | 2,903 | 5,582 |

**Notes on the table:**
- **Latency:** generation latency is the API wall-clock time per stage. Bedrock-reported server latency is within 0.1 s of it in every cell.
- **Sandbox time:** execution is similar for every model, with a median of 0.8–1.2 s, so it does not distinguish them.
- **Reasoning text:** only gpt-oss returns separate reasoning content. Its reasoning tokens are included in its output tokens. The other models expose no reasoning text, so "—" is not zero hidden reasoning.
- **Cost:** verified cost is **unavailable for every cell**. Prices are unverified, so cost is recorded as `unavailable`, never $0. Token counts are reported instead (see §4).
- **† Validator false reject.** One reporting failure each for Claude and gpt-oss (customer_churn q7) is a validator false reject; see §3.3. Scored as frozen, the results are Claude 3/4 and gpt-oss 2/4. Excluding that one identified false reject, they would be 4/4 and 3/4. The frozen scores remain authoritative, and the exclusion is a disclosed post-hoc observation, not a rescore.

### 1a. Reporting under the post-hoc validator v3.1 (secondary; reported beside v3, never replacing it)
The rule and its evidence are in `docs/reviews/2026-11-18_reporting_v3_1_posthoc.md`. The rescore is in `results/processed/v3_1_rescore/expA_stage_v3_reporting.json`.

| Model | Reporting pass, frozen v3 (primary) | Reporting pass, post-hoc v3.1 |
|---|---|---|
| Claude Sonnet 4.6 | 3/4 | 4/4 |
| Amazon Nova Pro | 2/4 | 2/4 |
| OpenAI gpt-oss-120b | 2/4 | 3/4 |

- Only the two customer_churn q7 comparative-clause false rejects change.
- The genuine failures remain: Nova's two wrong rankings, and gpt-oss's number-free statements in retail_sales.
- v3.1 was designed after observing these outputs, so it is not an independent test.

## 2. Best model under each explicitly defined criterion

| Criterion (definition) | Cleaning | Analysis | Reporting |
|---|---|---|---|
| Correctness: pass rate on mandatory requirements | Claude (3/4) | Claude = gpt-oss (4/4) | Claude (v3: 3/4; post-hoc v3.1: 4/4, with gpt-oss 3/4) |
| Schema compliance: structured output parsed, and for cleaning the output CSV satisfies the schema | Claude (4/4 parsed, schema 1.0) | All three parsed 4/4 | All three parsed 4/4 |
| Execution reliability: generated code ran successfully in the sandbox | Claude (4/4) | Claude = gpt-oss (4/4) | n/a (no code) |
| Speed: median generation latency | Nova (10.0 s), but 0/4 correct | Nova (6.2 s), but 0/4 correct; fastest *correct* model: gpt-oss (7.7 s) | gpt-oss (7.6 s) ≈ Nova (8.1 s) |
| Token economy: median output tokens | Nova (1,894) | Nova (1,502); fewest among correct models: Claude (1,717) | Nova (1,627) |
| Verified cost | unavailable | unavailable | unavailable |

**No single overall winner.**
- On correctness, Claude Sonnet 4.6 is the only model that is best or tied-best on every task.
- On speed, it is the slowest or second-slowest on every task.
- gpt-oss-120b matches Claude on analysis while being faster. It is unreliable on cleaning, because of output-length truncation (§3.1).
- Nova Pro is consistently the fastest and most token-frugal, but its generated code failed every cleaning and analysis task here.

Which model is "best" depends on whether correctness or speed and cost is the binding constraint. Among models that reached correctness, the data shows a trade-off rather than a dominant choice.

## 3. Why the models differ: evidence from the saved runs

Every example comes from saved `failure_detail` text and run artifacts under `results/raw/runs/expA_stage_v3-*/`.

### 3.1 Data cleaning (the hardest task: 5/12 passes overall)

**Claude, 3/4.**
- All 4 scripts executed.
- The only failure is support_operations, the two-file join project. The output was schema-valid but had 220 rows, where the reference has 347; 127 reference rows were missing.
- The failure is semantic: row filtering or joining logic dropped valid records. It is not a format error.

**Nova Pro, 0/4**, failing at every layer:
- 1 run produced **invalid JSON** in its structured response (customer_churn: "Expecting ',' delimiter").
- 3 runs produced code that **raised runtime errors** in the sandbox.
  - Two scripts use `DataFrame.applymap`, which is deprecated in the pinned pandas 2.2.3 and emits a warning, and then fail later in the script. The tracebacks end at lines 24 and 31.
  - One fails inside a pandas indexing assignment.
- No cleaned file was produced, so every downstream check failed (`output_exists` 3/3).

**gpt-oss, 2/4.**
- Both failures are **truncation**. The response reached `maxTokens` = 4096 before the JSON closed (customer_churn, retail_sales).
- Its separate reasoning content (median about 5.8k characters on cleaning) counts toward the output budget. A third, passing call used 4,079 of 4,096 tokens.
- When gpt-oss did finish, its cleaning was fully correct (2/2 executed; correctness 1.0).
- So its cleaning failures are an **interaction between its verbose reasoning and the uniform output limit**, not wrong cleaning logic. The limit is part of the frozen protocol and applies to every model identically. Whether a larger budget would change the result was not tested.

### 3.2 Data analysis (canonical clean input)

- **Claude and gpt-oss: 4/4 each.** Every required metric was correct and reproducible across the sandbox's second execution.
- **Nova Pro: 0/4**, with concrete code defects:
  - customer_churn and energy_consumption: `.dt.year` / `.dt.quarter` was applied to date columns read from CSV without parsing them as dates, causing a runtime error.
  - support_operations: `pd.json.dump(...)`, a non-existent pandas API (`AttributeError: module 'pandas' has no attribute 'json'`).
  - retail_sales: the code ran, but every quarterly revenue came out as 0.0 against expected values of 36,108–71,675. This is a wrong date or filter condition, caught by `values_within_tolerance`.
- The common thread for Nova is **type and API handling in generated pandas code**: parsing dates and using real library functions. The analytical intent was usually recognisable; the executable details were not.

### 3.3 Reporting (input: verified canonical findings)

- **All models had numerical consistency 1.0 and finding coverage 1.0.** Every reported value matched the verified findings, so the differences lie in structured claims and wording.
- **Nova Pro, 2 failures:** genuinely wrong ranking claims.
  - retail_sales q2: it stated East > North > South > West, which is alphabetical order, not the values' order.
  - energy_consumption q7: it stated peak > off-peak, which is not descending.
- **gpt-oss: 1 genuine failure.** In retail_sales the q2 and q3 statements contain no supported numeric finding; they are qualitative only.
- **Claude and gpt-oss: one identified validator false reject** (customer_churn q7).
  - Both wrote a correct sentence, for example "Premium LTV is 292.0% higher than Basic". `premium_vs_basic_ltv_change_pct` = 292.005, and the reported value was correct.
  - The frozen `prose_claims_consistent` check attributed "292.0%" to the nearby words "Premium LTV" (`ltv_premium` = 1,816.78) and flagged a contradiction.
  - Nova passed the same finding only because it phrased the sentence differently ("a 292.01% increase from Basic to Premium").
  - This is a **validator limitation**: proximity-based attribution of numbers in prose. It is not a model error.
  - It is disclosed here and **not fixed**, because the benchmark is frozen and Experiment B is being scored with the same validator. Any change would need its own approval and must be reported as post-hoc.
- **Unsupported commentary** (`unsupported_claim_count`, a quality metric, not a gate), median per report:
  - Nova 0, Claude 1, gpt-oss 1 (max 2).
  - Nova's reports were the most conservative.

## 4. Quality–cost trade-offs

- **Cost data:** dollar cost cannot be verified, so the comparison uses tokens and latency.
- **Prices vary widely:** per-token prices differ greatly between these vendors, so equal token counts do not mean equal cost. This report does not convert tokens to dollars.

| Task | Correct models | Faster / cheaper-in-tokens option among correct models | Trade-off |
|---|---|---|---|
| Cleaning | Claude (3/4), gpt-oss (2/4, truncation-limited) | Claude uses fewer output tokens (3,036 vs 4,088) and is slightly faster (19 vs 23 s) | Claude dominates gpt-oss here. Nova is fastest but did not produce usable output. |
| Analysis | Claude (4/4), gpt-oss (4/4) | gpt-oss is faster (7.7 vs 10.1 s) but uses more output tokens (2,171 vs 1,717) | A genuine trade-off. Which is cheaper depends on unverified per-token prices. |
| Reporting | Claude highest pass rate; all three numerically exact | Nova and gpt-oss are about 45% faster than Claude | Claude for structural correctness; Nova and gpt-oss for speed, at a higher rate of ranking or wording failures |

## 5. Uncertainty and limitations
- **Sample size:** n = 4 per cell, with one run per project and no repeats.
  - The Wilson intervals overlap in most cells.
  - Only Claude vs Nova on analysis (4/4 vs 0/4) and Claude vs Nova on cleaning (3/4 vs 0/4) are separated even approximately.
  - Variability across repeated runs is not yet measured. Repeats are scheduled after Experiment B.
- **Projects:** they are synthetic, and one (retail_sales) is pilot-exposed.
- **Configuration dependence:**
  - One uniform `maxTokens` (4096) and temperature 0 for every model.
  - gpt-oss's cleaning results in particular depend on this output limit (§3.1).
  - Nova's runtime errors partly depend on the pinned pandas 2.2.3 (`applymap` deprecated).
  - Neither factor was varied.
- **Validator:** one false-reject mechanism was identified (§3.3). There may be others not yet detected.
- **No causal claims:** the explanations above describe observed artifacts, such as code errors, truncation and wrong rankings. They do not claim why a model internally behaves this way.
- **Generalisation:** three models do not establish general rankings, and results may differ for other tasks, prompts or model versions.

## 6. Relation to Phase 2
- These are independent-stage results on canonical inputs. They correspond to the S2 ("greedy task-only") evidence a router would use.
- Whether these stage-level strengths carry over to end-to-end workflows, with real upstream artifacts and error propagation, is the Phase 2 question.
- Phase 2 will be reported separately, from Experiment B.
