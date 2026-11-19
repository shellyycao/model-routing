# Parts B and C: Multi-model workflows and explainable routing (prospective v3)

**Primary experiment:** `expB_paths_v3` (tag `benchmark-v3-frozen`, `22a56e6`).
- 4 projects × 27 paths, fresh calls, policy `continue_with_actual_artifact`.
- Plus pre-registered repeats: repeat_index 1–2 of A-A-A, B-B-B, C-C-C, A-C-A, A-A-C and A-C-C on every project.
- **156 WorkflowRunRecords** in total: 108 main runs + 48 repeats, **0 void_infra**.

| Part | What it reports |
|---|---|
| Part A (separate) | `results/reports/phase1_model_specialization.md` |
| Part B | The workflow sections below |
| Part C | The routing and XAI sections below |

**Inputs and tables:**
- All tables are in `results/processed/v3_primary_analysis/` (config `configs/analysis_v3.yaml`, schema `docs/analysis_schema.md`).
- Routing output is in `results/routing/v3_primary/`.

**Data validity** (`results/processed/reconciliation.json`, from `experiments/reconcile_records.py`):

| Check | Result |
|---|---|
| Records validate against contracts v1.2 | All 156 |
| Invocations | 356 logged, 356 referenced, 0 orphans |
| API attempts in the log vs ledger calls | 339 = 339 |
| Sandbox executions in the verified image `88988a15…` | 240 / 240 |
| Cache hits | 0 (every call was fresh) |

**Evidence status: EXPLORATORY.**
- There are 4 projects; most paths have one run, and 6 paths have 3 runs.
- retail_sales is pilot-exposed: its v2 pilot informed the v3 design.
- No significance tests were run. Intervals are Wilson 95% for proportions, or [min, max] ranges.

**Scoring:**
- **Primary:** frozen v3.
- **Secondary:** post-hoc reporting validator v3.1, shown beside v3 and never substituted (`docs/reviews/2026-11-18_reporting_v3_1_posthoc.md`).

---

## Part B: When does combining LLMs help end to end?

### B1. Strict feasibility: single-model vs cross-model (main runs only, repeat 0)

| Group | v3 (primary) | Post-hoc v3.1 (secondary) |
|---|---|---|
| Single-model paths (A-A-A, B-B-B, C-C-C × 4 projects) | 2/12 = 0.17 [0.05, 0.45] | 3/12 = 0.25 [0.09, 0.53] |
| Cross-model paths (24 × 4) | 15/96 = 0.16 [0.10, 0.24] | 18/96 = 0.19 [0.12, 0.28] |

**On average, combining models did not raise feasibility.** The intervals overlap almost completely. Per project, the picture differs:

| Project | Single-model feasible (main + 2 repeats) | Feasible cross-model paths (main run, v3) |
|---|---|---|
| customer_churn | A 0/3, B 0/3, C 0/3 | A-A-B, A-A-C, A-C-B, C-C-B |
| energy_consumption | A 0/3, B 0/3, C 0/3 | A-A-C, A-C-A, A-C-B, C-C-B |
| retail_sales (pilot-exposed) | **A 3/3**, B 0/3, C 0/3 | A-B-A, A-C-A, A-C-B, C-B-B, C-C-A, C-C-B (A-A-A also feasible) |
| support_operations (two-file join) | A 1/3, B 0/3, C 0/3 | B-A-B (A-A-A 1/3) |

**Reading the table:**
- **Where mixing helped:** in 2 of 4 projects, no single model completed the workflow in any of 3 runs, while specific combinations did. This is the situation in which mixing models helps: a stage where the "home" model fails gets covered by a model that succeeds there.
- **Where it didn't:** in retail_sales, Claude alone was the most reliable path (3/3). In support_operations, almost nothing succeeded.
- **Confound in customer_churn:** every feasible path there ends with Nova (B) as reporter, or with C after A. Under v3, Claude's and gpt-oss's churn reports were rejected by the identified validator false reject (q7 comparative clause). Under v3.1, customer_churn rises from 4 to 8 feasible paths. **The apparent "Nova is the best reporter for churn" pattern is a scoring artifact**, not evidence of reporting skill.

### B2. Where workflows break: stage pass rates in Experiment B (main runs, actual upstream inputs)

| Stage | Claude (A) | Nova Pro (B) | gpt-oss (C) |
|---|---|---|---|
| Cleaning (raw input; same conditions as Experiment A) | **28/36** | 1/36 | 15/36 |
| Analysis (ran on actual upstream) | **18/22** (14 blocked) | 5/22 (14 blocked) | 14/20 (16 blocked) |
| Reporting (ran) | 7/16 | 10/17 | 4/14 |

- **First failing stage:** cleaning 64, analysis 13, reporting 14, and none (feasible) 17, out of 108.
- **Cleaning is the bottleneck.** It also gives a larger sample for the Part A cleaning comparison: 36 runs per model under identical raw-input conditions. The ordering is the same as in Part A: Claude > gpt-oss ≫ Nova.
- **Blocked stages:** 44 runs blocked at analysis and 17 at reporting, because the upstream artifact was not structurally usable. These are attributed upstream, not to the downstream model.

### B3. Error propagation: a descriptive decomposition, not a causal switching cost
- **20 analysis runs** received a cleaned file that failed cleaning validation but was structurally consumable. Median upstream error: 1 − cleaning_correctness = 0.137.
  - Their analysis **ground-truth accuracy**: median **0.10**.
  - Their **conditional accuracy**, against the reference recomputed from the file they actually received: median **1.0**.
  - The analysis code was usually right for its input. **The wrong final numbers came from upstream data errors.** In 6 of the 20 runs the cleaning errors happened not to touch the analysed metrics.
- **Matched canonical baseline:** analysis numerical accuracy, Experiment A (canonical input) vs Experiment B (actual upstream), averaged over upstream-model cells.

  | Analysis model | Canonical | Actual upstream |
  |---|---|---|
  | Claude | 1.00 | 0.84 |
  | gpt-oss | 1.00 | 0.76 |
  | Nova | 0.21 | 0.24 |

- **How to read this:** differences mix upstream data errors, format differences and stochasticity. They are not a pure model-switching cost. Per-path values are in `propagation.json` and `matched_baseline.json`.

### B4. Repeat variability (temperature 0)
- 24 repeated cells (6 paths × 4 projects, 3 runs each): **18 have the same outcome all three times, and 6 flip.**
  - The flipping cells are customer_churn A-A-C and A-C-C, energy_consumption A-C-A and A-C-C, retail_sales A-A-C, and support_operations A-A-A.
- **Single-run feasibility of a path is therefore noisy.** One feasible run does not establish that a path is reliable. Several S3 selections below rest on single runs.
- Full spreads are in `variability.json`. No significance tests.

---

## Part C: Explainable routing and counterfactual validation
**Setup:**
- **Leave-one-project-out:** each project is held out in turn, and the router is trained on the other three. The held-out project's records are physically excluded, and this is enforced by contract checks.
- **Objective:** `configs/routing.yaml`, committed 2026-11-17, before any outcome existed:
  - feasibility probability ≥ 0.5;
  - analysis numerical_accuracy ≥ 0.9;
  - unsupported claims ≤ 1;
  - then a preference order of cost (INACTIVE, because prices are unverified), end-to-end time, then tokens.

### C1. Strategies vs the retrospective oracle (S4 is a reference, never deployable)

| Held-out project | S1 single-model (executed) | S2 task-only greedy | S3 workflow-aware | S4 oracle (retrospective) |
|---|---|---|---|---|
| customer_churn | A, B, C all infeasible | A-C-A, infeasible (3 runs) | A-C-B, **feasible** (1 run) | C-C-B |
| energy_consumption | all infeasible | **no feasible path predicted** | A-C-B, **feasible** (1 run) | C-C-B |
| retail_sales | A-A-A feasible 3/3; B and C infeasible | **no feasible path predicted** | C-C-B, **feasible**, = oracle (1 run) | C-C-B |
| support_operations | A-A-A mixed (1/3); B and C infeasible | A-C-A, infeasible | C-C-B, infeasible (1 run) | B-A-B |

- **S3 (workflow-aware)** chose a path that was executed-feasible in 3 of 4 held-out projects; S2 did so in 0 of 4.
- **S2 failed differently by project:** for energy_consumption and retail_sales it predicted no feasible path, because its product of independent stage feasibilities fell below 0.5. For the other two projects, its chosen path was infeasible.
- **S1:** the best fixed single-model choice (A-A-A) was feasible in 1 of 4 projects, and mixed in another.
- **Caveats:**
  - S3's chosen paths have one executed run each, and B4 shows single runs flip.
  - n = 4 held-out projects.
  - S3's churn and energy picks end in B, the reporter partly favoured by the churn validator artifact in the training data.
  - **This is suggestive, not established.**

### C2. Computational faithfulness (does the explanation match the router's actual computation?)
- **20 decision traces, 429 explanation claims checked: 429/429 consistent, 0 inconsistencies.**
- **Replay:** re-running the router from each trace's inputs reproduces the selection in **20/20**.
- **The template explanations are computationally faithful.**

### C3. Empirical validity (did the predicted counterfactual outcomes happen?)
50 counterfactual predictions were written to a hash-chained log before validation; the chain was verified, and all 50 were validated.

| Predicted quantity (alternative − selected) | Direction correct | Interval covers actual | Median absolute error |
|---|---|---|---|
| **Feasibility** | **22/50 (44%)** | 48/50 | 0.42 |
| End-to-end time | 7/9 | 9/9 | 4.7 s |
| Total tokens | 4/9 | 7/9 | 742 |
| Unsupported-claim count | 7/10 | 6/10 | 0.14 |
| Stage quality metrics (cleaning, analysis, reporting) | 9–10 / 9–10 | 9–10 / 9–10 | 0.0 |
| Model switches | 50/50 | 50/50 | 0 |

**Reading the table:**
- **Feasibility, the decision-relevant quantity:** the direction of the predicted change was right in only **44%** of cases, about chance.
  - Interval coverage is high only because the leave-one-project-out ranges are wide. That is not evidence of accuracy.
- **Quality metrics:**
  - "Direction correct" is mostly trivial here: both paths sit at 1.0 when both are measured.
  - Quality is measurable only when both runs reached that stage. That leaves n = 9–10 of 50.
- **Switch count:** correct by construction.

### C4. The central XAI result
**Explanations were faithful but not empirically valid for feasibility.**
- The router's explanations accurately describe what it computed: 429/429 claims consistent, 20/20 replays match.
- But the counterfactual claims it makes about alternative paths ("switching stage X to model Y would change feasibility by Δ") were directionally right only 44% of the time on held-out projects.
- **This supports keeping computational faithfulness and empirical validity separate.** A faithful explanation can still faithfully report a wrong prediction.
- **Likely contributors** (descriptive, not causally identified):
  - stage-level estimates transfer poorly across structurally different projects (support_operations is a two-file join);
  - repeat variability (B4);
  - the q7 validator artifact, which distorts training labels for reporting.

---

## Limitations
- 4 projects, 3 models, 1 run for most paths: exploratory only. These results do not establish general model rankings.
- retail_sales is pilot-exposed.
- **One known validator false reject** (customer_churn q7) affects the primary v3 scores. v3.1 corrects it post hoc for the secondary view only. Other undetected validator issues may exist.
- Dollar cost is unavailable (prices unverified), so cost preferences were inactive in routing.
- **Fixed generation settings:** a uniform `maxTokens` of 4096 and temperature 0. gpt-oss truncation, seen in Part A, also affects its cleaning here.
- Error-propagation and interaction figures are descriptive decompositions, not causal effects.
- **Mac sleep:** the Mac slept for about 28 minutes during the run (00:42–01:10). Runs paused and resumed. Timing fields use a monotonic clock, so sleep is not counted, but wall-clock completion times include the gap.
