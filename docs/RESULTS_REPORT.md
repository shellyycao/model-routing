# Results report: motivation, method, results

Date: 2026-11-19. This is the reader-facing write-up. The source of every number, and how to verify each one, is in
[FINAL_REPORT.md](FINAL_REPORT.md) (section 6 is the verification guide).
Evidence labels: **pre-registered** = rules frozen before the paid runs; **post-hoc** = analysis added after the
results were seen, which is weaker evidence.

## 1. Motivation

In my work I inevitably use several AI models at once, but which one to use and how to combine them is mostly based on
personal experience, with no way of knowing whether those choices are better than the alternatives. Existing tools
recommend workflows for a task, but most do not validate their recommendations against real outcomes. So I tested
it myself:

- **Q1** What is each model good at?
- **Q2** Does passing work between several models beat using one model?
- **Q3** Can the reasons and predictions given by a recommender (router) be checked?

The three questions are equally important, and cost is part of the evaluation. XAI (explaining "why") is also applied
to Q1 and Q2: every conclusion asks for a cause, and causes that can be tested are tested by re-running.

## 2. Method

- **Task:** one data-analysis workflow with three steps: clean the data → analyze → write a report. Four synthetic
  projects (customer churn, energy consumption, retail sales, support operations) with known correct answers.
- **Environment:** real calls on AWS Bedrock. Model-written code runs in a pinned Docker sandbox. Scoring uses fixed
  rules. Cost is computed from real prices and per-call token counts, with a hard cap per experiment ($100), reserved
  before each call and settled after.
- **Experiments:**
  1. Single-step tests: each model does each step on its own.
  2. Full workflows: 3 models × 3 steps = 27 paths, run on every project, some repeated 3 times.
  3. Root causes: every run's code, errors and outputs are saved, failure causes are grouped, and testable causes are
     verified by re-running.
  4. Supplement: 3 standalone tasks (bug fixing, information extraction, literature ranking) compare the models,
     including real cost.
  5. Router (Q3): a program that recommends model combinations from past data (strategies S1–S4), trained on 3
     projects and tested on the 4th. Explanations are generated from fixed templates over the computation record.
     "What if you swapped" predictions are locked into a tamper-evident log before the outcomes are known, then
     compared with the real results.
- **Two model groups (the aliases A/B/C refer to different models in each group and must not be mixed):**
  - Group 1: Claude Sonnet 4.6, Amazon Nova Pro, gpt-oss-120b (output limit 4096 tokens).
  - Group 2 (closer in price): Claude Sonnet 4.6, Kimi K3, GLM 5 (output limit 16384 tokens).
- **Rules frozen first:** scoring rules and protocols were frozen and tagged before the runs. Problems found later are
  handled by additive "corrected" versions; frozen files are never edited, the official numbers are kept, and the
  corrected numbers are shown beside them.
- **On bias:** Claude is itself one of the models being evaluated, so execution was done by Codex and Claude only
  reviewed at checkpoints. Every post-hoc analysis Claude did had its rules committed before computing, and is
  disclosed.

## 3. Results

### Q1: each model has its own strengths

No model is best at every step. Single-step tests (4 projects per cell):

| Model | Clean | Analyze | Report | Notes |
|---|---|---|---|---|
| Sonnet 4.6 (Group 1) | 3/4 | 4/4 | 3/4 | Most balanced, but slowest and fairly expensive |
| Nova Pro | 0/4 | 0/4 | 2/4 | Fastest and cheapest, but its code often has errors |
| gpt-oss-120b | 2/4 | 4/4 | 2/4 | Strong at analysis; cleaning often cut off by the output limit |
| Sonnet 4.6 (Group 2) | 3/4 | 4/4 | 2/4 | Stable, fast responses |
| Kimi K3 | 4/4 | 4/4 | 1/4 | Strong at cleaning and analysis, weak at reporting; outputs long reasoning, so actually the most expensive |
| GLM 5 | 4/4 | 0/4 | 4/4 | Strong at cleaning and reporting, failed all analyses; cheapest |

**Many "failures" are actually small bugs.** In the last step, saving results as JSON, pandas number types could not
be serialized. Fixing only that and re-running the original code: GLM 5's analysis was correct in 33 of 35 runs
(single-step test 0/4 → 4/4); Nova Pro's analysis in 9 of 12; gpt-oss's cleaning in 9 of 12. In the reporting step,
another 15 failures were only rounding being stricter in the scorer, and 30 were one known false rejection.

Post-hoc corrected stage pass rates (official numbers kept): for example, Group 2 GLM 5 analysis (repeated runs) goes
from 27/60 to 56/60. This is a sensitivity analysis of scoring and environment problems, not a new end-to-end
conclusion.

Grouped causes: Nova Pro repeatedly tripped on deprecated functions, unparsed dates, and calls to functions that do not
exist. gpt-oss's cleaning failures came from answers too long for the 4096 limit (14 times); with the limit raised to
16384 this did not happen. Kimi is expensive because it outputs a lot of reasoning text first. Apart from the GLM
cause, which was verified by re-running, these causes were grouped from failure records and not individually verified
counterfactually.

### Q2: are multiple models better than one?

**Not necessarily. Mixing was not consistently better than a single model.**

| | Group 1 official | Group 1 corrected | Group 2 official | Group 2 corrected |
|---|---|---|---|---|
| Single-model paths succeeded | 2/12 | 2/12 | 3/12 | 6/12 |
| Mixed paths succeeded | 15/96 | 23/96 | 38/96 | 46/96 |
| All 108 paths | 17 | 25 | 41 | 52 |

- Group 2's official numbers seem to favor mixing (25% vs 40%), but **the difference disappears after correction**:
  50% vs 48%.
- Group 1 has only 12 single-model samples. In 2 projects no single model succeeded in three tries, while some mixed
  paths did.
- Cleaning is the biggest bottleneck: in Group 1, 64 of 108 runs failed first at cleaning. Upstream errors pass
  downstream: in 20 runs where analysis received wrong data, median accuracy against the true answer was only 0.10,
  but against the data it actually received it was 1.00.
- How the correction was done: for 40 paths blocked by the serialization bug, only the "write report" step was re-run
  (cost $1.40); 11 more were re-judged from existing results. The corrected view is post-hoc and the two rates have
  different sample sizes, so it cannot show a causal benefit of mixing.

### Q3: can the router's explanations and predictions be trusted?

**Explanations are faithful; predictions show no skill.**

- Explanation sentences match the computation: 429/429 in Group 1, 451/451 in Group 2. Because explanations are
  generated from templates over the computation record, they are almost guaranteed to be faithful; "faithful" and
  "accurate prediction" are two different things.
- "Will it succeed after a swap" predictions had the right direction in 22/50 (44%) for Group 1 and 31/64 (48%) for
  Group 2.
- **Re-scored with corrected labels (post-hoc): the router did not get better.** Group 1 21/50, Group 2 24/64. The
  baseline that always says "no change" is more accurate: 26/50 and 36/64; in 7 of 8 comparisons it is at least as
  good as the router. The router is only much better than "always says better". Most cases really are "no change", so
  the router's correct answers come mainly from ties. This re-scoring depends on the 40 re-runs and 11 re-judgements,
  so it is a sensitivity analysis, not a reconstruction.
- Failure-cause classification (post-hoc): about half of directly failed records belong to known scoring or
  environment problems. But "the rest" is a broad catch-all that does not decide whether the model or the scorer was
  at fault, and a residual of 0 follows from the rules; it does not mean every failure is understood.

### Cost

- Looking only at success is not enough; cost changes the choice. Cost per successful run (failed calls included):
  about $0.27 for Group 1 and $0.38 for Group 2.
- The cheapest combination is not always the best value: some cost under 1 cent per run but fail at step one, with
  0 successes.
- Unit price can mislead: Kimi and Sonnet have the same unit price, but actual spend differs by about 4.5× (reasoning
  text is billed as output).
- Letting the router choose by cost (post-hoc): in Group 1, 1 of 8 selectable decisions changed; in Group 2, 7 changed.
  Cost predictions are far more accurate than success predictions: 64/64 in Group 2, better than unit price alone
  (56/64).
- Total spend: about $24 and $26 for the two main experiments, plus $1.40 for the re-runs.

## 4. Corrections and limitations

- **Corrections:** official (frozen) numbers were never changed; corrected versions are listed separately. Problems
  found and handled: the number-type JSON bug, an over-strict scorer, one false rejection, Docker occasionally not
  finding its image (re-run), and dataset hashes not matching on a clean checkout (resolved with an additive amendment;
  see `docs/HASH_REPRODUCIBILITY_AMENDMENT.md`).
- **Small sample:** 4 synthetic projects, 4 per cell in single-step tests, and most combinations run only once; the
  conclusions are exploratory.
- **Only one workflow shape:** clean → analyze → report; the results do not generalize to arbitrary workflows.
- **Model choice limited by account access:** this compares these specific models, not which vendor is better.
- **The two groups had different settings:** different output limits, and Kimi does not support the temperature
  setting.
- **Many failures are small bugs or over-strict scoring, not lack of ability**; the corrected view is post-hoc and is
  weaker evidence than the pre-registered parts.
- **Router conclusions are limited to this small dataset:** intervals are computed as if samples were independent,
  but they are actually clustered by project and strategy, so they are optimistic.
- **Tasks and analysis were written with AI assistance** (Claude and Codex); reviewing each other is not the same as
  independent replication by a separate team.
- Commit hashes and tags refer to the original repository; the public repository is a fresh-history snapshot (see
  `PROVENANCE.md`).
