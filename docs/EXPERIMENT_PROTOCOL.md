# Experiment Protocol

_Frozen version: contracts v1.2, dataset generator v2.0, benchmark v2, prompts v2, cleaning/analysis validators v1.0, reporting validator v2.0. Frozen before any pilot or full evaluation under tag `benchmark-v2-frozen`._

Each section marks what is **[implemented]**, meaning code exists and is tested, and what is **[planned]**.

## 1. Models [implemented]
**Region:** us-east-1. **AWS profile:** `xai-bedrock`. **API:** Bedrock Converse.

| Alias | Model | Bedrock ID | Type |
|---|---|---|---|
| A | Claude Sonnet 4.6 (Anthropic) | `us.anthropic.claude-sonnet-4-6` | US cross-region inference profile |
| B | Amazon Nova Pro (Amazon) | `us.amazon.nova-pro-v1:0` | US cross-region inference profile |
| C | gpt-oss-120b (OpenAI, open-weight) | `openai.gpt-oss-120b-1:0` | On-demand, in-region |

- **Selection basis:** live access checks on 2026-11-17. Sonnet 5.x and Haiku 5.5 were denied; Llama is legacy and blocked; GPT-5/6 were denied; Gemini is not on Bedrock.
- **Inference settings, identical for all models:** `maxTokens` 4096 by default, `temperature` 0.0.
- **gpt-oss-120b:** its reasoning tokens count toward output tokens. The reasoning text is logged separately.
- **Prices:** none verified, because the Pricing API is denied for this IAM user and the public page shows no us-east-1 rows. Cost is recorded as `unavailable`, never $0. A price can be added by hand in `configs/models.yaml`, and only with a source and date.

## 2. Benchmark projects [v2 frozen]
| Project | Raw rows | Cleaned rows | Metric keys | Questions |
|---|---|---|---|---|
| retail_sales | 636 | 520 | 24 | 7 |
| customer_churn | 840 | 749 | 24 | 7 |
| energy_consumption | 1,560 | 1,428 | 25 | 7 |
| support_operations | 380 tickets + 18 agent-roster rows | 347 | 21 | 7 |

- Data is synthetic and generated from a seed with stdlib `random`. Files are byte-reproducible (`python -m datasets.generate --check`).
- **Imperfections:** duplicates, 5 date formats, missing-value tokens, currency strings, unit mixes, category variants, out-of-range values.
- **Ground truth:** a pure-Python reference implementation, never an LLM. An independent pandas implementation reaches the same result.
- **Validators:** cleaning and analysis remain version 1.0; reporting is version 2.0.
- **Revision v2 implementation (2026-11-18, before any model outcomes):** findings M1–M5 and m2–m4 of `docs/reviews/2026-11-18_review_benchmark_validity.md` were implemented as pre-experiment design changes:
  - reporting now requires every metric under its own finding, requires each statement to include at least one supported numeric finding, rejects empty “See values” findings, renders all authoritative structured values/directions/rankings, rejects explicit cross-key/group numeric attribution, and verifies declared difference/ratio/percentage-change/share derivations;
  - unsupported numeric commentary remains the separately reported `unsupported_claim_count`; the pre-set advisory threshold is **2 claims per report** (chosen to tolerate a small amount of non-critical commentary) and is not a hard feasibility gate;
  - derived-step questions, value-disagreeing duplicate copies, and questions using retail `customer_id`, churn `lifetime_value`, and energy `meter_id`/`tariff` were added;
  - `support_operations` adds a structurally different two-file ticket/agent join using the explicit input allow-list;
  - example answer values were removed from analysis question text; UTF-8 BOM headers are accepted; monetary tolerances use 0.011;
  - prompt v2 preserves the v1 cleaning/analysis instructions and makes the reporting validator's minimum requirement explicit: every finding statement contains at least one verified numeric value;
  - regression tests cover each previously demonstrated false accept/false reject; the independent re-review approved the freeze (`docs/reviews/2026-11-18_review_benchmark_v2_t1.md`).
- **Freeze metadata:** dataset generator 2.0; contracts 1.2; cleaning validator 1.0; analysis validator 1.0; reporting validator 2.0; prompt version v2; full offline/Docker suite 291 passed and 8 paid-live tests skipped; all four projects byte-reproducible.

## 3. Experimental design
- **Experiment A [implemented and tested offline; no real-model run yet]:** each model × stage × project on CANONICAL inputs. Analysis gets the canonical cleaned CSV; reporting gets the canonical findings. Records are `StageBenchmarkRecord`.
- **Experiment B [implemented and tested offline, plus real-model retail_sales pilots]:** every path, enumerated as a Cartesian product: `enumerate_paths(["A","B","C"])` gives 27 paths per project in 3-stage mode and 9 in the 2-stage development mode. Records are `WorkflowRunRecord`. The two-stage pilot is complete; the initial three-stage execution produced 22 model outcomes and 5 `void_infra` records after the Docker image disappeared. Outcomes are recorded separately in `docs/reviews/2026-11-17_retail_sales_pilot_2stage.md` and `docs/reviews/2026-11-17_retail_sales_pilot_3stage.md`; they do not modify this frozen design.
- **Execution policy (user decision):** FRESH CALLS PER PATH.
  - No cached outputs or artifacts are shared across paths.
  - Each run has its own artifact directory.
  - An optional shared-prefix mode must use a different `experiment_id`, and its results are kept separate.
- **Known prompt difference (rule 5):** Experiment A handoffs describe the canonical upstream input as "Canonical reference …", so Experiment A prompts differ slightly in wording from Experiment B. This has to be documented in the methodology.
- **Matched canonical baseline:** the analysis stage is evaluated on canonical input (Experiment A) and on actual upstream output (Experiment B), under the same requirements and validators. Differences are not interpreted as pure model-switching cost; upstream data errors, formatting differences and stochasticity all contribute.

## 4. Failure propagation policy [implemented and tested: contracts v1.2, orchestrator, real-sandbox end-to-end test]
- **Policy name:** `continue_with_actual_artifact`.
- **When a stage runs:** a downstream stage runs on the ACTUAL upstream artifact whenever it is structurally consumable (the file exists, parses, and has the required columns or keys), even if the upstream stage failed semantic validation.
- **Never:** the artifact is never replaced with canonical or ground-truth data.
- **When it is blocked:** if the artifact isn't consumable, the stage is `blocked_by_invalid_artifact`. That is attributed upstream, not to the downstream model, and every later stage is blocked too.
- **What each run records:**
  - strict feasibility (`outcome`: `feasible` only if every stage passed; `void_infra` for infrastructure failures);
  - downstream executability;
  - upstream error severity;
  - end-to-end accuracy;
  - propagation impact (conditional quality minus ground-truth quality);
  - blocked stages.
- **Infrastructure failures:** sandbox unavailable, throttling exhausted, access denied and budget refusal all give `void_infra`. They never count as model failures.

## 5. Ground-truth isolation [implemented and tested: contracts, sandbox, orchestrator allow-list, prompt-leak tests]
- Models see only `ProjectSpec.model_view()`. `notes`, canonical paths, the ground-truth path and validator metadata are hidden.
- Only `ProjectSpec.model_input_files()` are mounted into the sandbox (cleaning), or the actual upstream artifact (later stages).
- Validator details contain expected values and never reach a model. Handoff status is limited to `passed`, `failed`, `not_run` or `blocked_by_invalid_artifact`.
- **Sandbox:** model code runs only in the currently verified Docker image (`results/verification/sandbox_verification.json`, 20/20 executor tests). It has no network, no credentials, read-only inputs, non-root execution, and memory, CPU, PID and time limits. The original raw verification record remains preserved at `results/raw/sandbox_verification.json`. Rebuilding the image requires re-verification.

## 6. Evaluation metrics (no weighted composite score) [contracts implemented]
- **A. Feasibility:** the hard gate described above.
- **B. Stage quality**, each metric reported on its own:
  - cleaning: `cleaning_correctness`, `data_integrity`, `schema_compliance`;
  - analysis: `numerical_accuracy`, `calculation_coverage`, `reproducibility` (only when repeats exist);
  - reporting: `numerical_consistency`, `finding_coverage`, `unsupported_claim_count`.

  Each is computed against `ground_truth`, and also against `conditional_reference` (the reference recomputed from the actual upstream artifact).
- **C. Efficiency:**
  - end-to-end time, kept separate from API latency;
  - execution time;
  - tokens;
  - verifiable cost (`None` while prices are unverified);
  - model switches;
  - handoff size.
- **Reporting rules (revision v2, implemented):**
  - Critical factual contradictions are hard failures.
  - Correct derived values are accepted.
  - Unsupported commentary is a quality metric with a pre-set threshold.

## 7. Routing strategies [implemented and tested on synthetic fixtures only; no results]
- **S1:** each of the three single-model paths.
- **S2:** greedy task-only selection, using the best model per stage from Experiment A and ignoring interactions.
- **S3:** workflow-aware selection. It adds interaction terms estimated from the training projects' Experiment B runs, shrunk when evidence is thin, and labelled "interaction terms", never "handoff cost".
- **S4:** the retrospective oracle. It is a reference only and never a prospective prediction.
- **Objective:** a pre-defined `RoutingObjective`:
  - a minimum feasibility probability;
  - quality constraints on `<stage>.<metric>`;
  - a lexicographic preference order with a tie tolerance.

  Unavailable criteria (for example cost) are marked inactive. When nothing qualifies, the result is "no feasible path". Pareto sets are reported.

## 8. Counterfactual protocol [implemented and tested on synthetic fixtures only; no results]
- For each selected path, predict alternatives: each single-stage swap and each single-model baseline.
- Each prediction is a `CounterfactualPrediction`: frozen, with a canonical content hash, and written to an append-only hash-chained log before any validation.
- Validation compares predictions with the executed Experiment B outcomes of the held-out project: absolute error, direction, interval coverage, feasibility agreement and repeat spread. It refuses to run if a prediction or the chain has changed. Wrong predictions are kept and reported.
- **Computational faithfulness** (do the explanation's claims match the trace, and does replaying the router give the same selection?) and **empirical validity** are separate outputs.

## 9. Leakage safeguards
- Leave-one-project-out: the training view physically excludes the held-out project's records. **[implemented, tested]**
- `DecisionTrace` rejects evidence from projects outside training and checks `training_data_hash`. **[implemented]**
- Routing thresholds and parameters are never tuned on held-out outcomes.
- The benchmark may not change after full outcomes have been inspected unless the change is documented as post-hoc. The changes so far were all made before any outcomes existed.

## 10. Repeat-run policy [client implemented]
- Repeats: the three single-model paths plus a small set of relevant mixed paths.
- Each repeat carries `repeat_index` and must bypass the cache; the client raises if a repeat tries to use the cache.
- Every repeat's records are kept, and variability is reported without significance claims.

## 11. Budget and approvals
- Hard call and token limits are enforced across threads and processes (`UsageLimits`, shared ledger). The dollar guard is inactive while prices are unverified.
- **Paid usage so far:** 70 tracked calls: smoke test 6 and live tests 7 (1,193 input and 636 output tokens), two-stage retail pilot 13 (28,976 input and 31,058 output tokens), and initial three-stage retail execution 44 (103,895 input and 105,047 output tokens). Combined tracked usage is 134,064 input and 136,741 output tokens, plus about 30 tiny untracked probe calls made during model selection.
- **Needs explicit user approval:**
  - any pilot or full benchmark run, shown with an estimate from `--plan`;
  - rerunning the live tests;
  - any change to scope, the benchmark or the methodology.

## 12. Post-freeze reporting v3 and infrastructure repair [additive; offline only]

The retail pilot exposed an interface mismatch in frozen v2: the model received metric keys but not
the validator's display-label mapping, q3 was described as a trend while its ranking was mandatory,
and the optional schema field did not communicate that requirement. This does not alter frozen v2.
The full audit is `docs/reviews/2026-11-18_post_freeze_v3_audit.md`.

- Reporting validator `3.0-post-freeze` and `prompts/v3/` are separate artifacts. The active runner
  remains on prompt v2; no saved v2 score is overwritten.
- V3 distinguishes ranking semantics from explicit structured-field compliance. Wrong explicit
  orders remain hard failures. Missing orders are semantically recoverable only from complete finite
  reported values and are still recorded as non-explicit.
- Offline rescoring of ten saved reports yields 0 v2 passes and 7 v3 secondary-analysis passes.
  Three genuine factual/derived/ranking failures remain. These results are not directly comparable
  to a prospective run prompted under v3.
- The Docker image disappearance is attributable only to external daemon state loss/cleanup at the
  evidence available. Both paid runners now preflight before client construction and hold a
  restricted exact-image lease for the entire execution. No auto-build or host fallback exists.
- The five original `void_infra` records remain infrastructure-invalidated. A possible retry is
  predefined as all five paths once, with new run IDs and the original records retained. It has not
  been approved or executed.

## 12. Prospective v3 is the PRIMARY experiment (user decision, 2026-11-18)
- **Decision:** the user chose a separately named prospective v3 experiment as primary. Frozen v2 (tag `benchmark-v2-frozen`) and its retail_sales pilot records are kept unchanged as a **pilot**. They are never pooled with v3.
- **Disclosure (pilot-informed design change):**
  - v3 was designed after inspecting the v2 retail_sales pilot reports (`docs/reviews/2026-11-18_post_freeze_v3_audit.md`).
  - The change is limited to the reporting interface and validator:
    - the prompt exposes the metric-key-to-label contract and which findings need a direction or ranking;
    - metric keys and labels are accepted as ranking aliases;
    - an omitted explicit ranking is a visible non-mandatory check when the reported values determine the order;
    - wrong rankings stay mandatory failures.
  - Cleaning and analysis prompts and validators are unchanged from v2; only the version label differs.
  - Datasets and ground truth are unchanged.
  - **retail_sales is "pilot-exposed":** its outputs informed the v3 design. Results must be reported with and without retail_sales wherever it matters, and the methodology must state this.
- **Configuration:**

  | Item | Value |
  |---|---|
  | Command switch | `--protocol v3` |
  | Experiment IDs | `expA_stage_v3`, `expB_paths_v3` (enforced: v3 cannot write into v2 IDs and vice versa) |
  | Prompts | `prompts/v3/` |
  | Reporting validator | `src/evaluation/reporting_v3.py` |
  | Failure policy | `continue_with_actual_artifact` |
  | Calls | fresh per path |
  | Inference settings | as before |
- **Plan for all 4 projects** (worst case, from `--plan`):
  - Experiment B: 108 runs, 324 calls, 3.79M input and 1.33M output tokens.
  - Experiment A: 36 calls, 0.42M input and 0.15M output tokens.
- **Budget:** the user confirmed $200 of credit and relaxed per-phase spending monitoring. Hard call and token limits still apply as a safety net. Prices remain unverified, so cost is recorded as `unavailable`.
- **Sandbox:** re-verified on the rebuilt image `sha256:88988a15…`, 20/20 tests.
- **Frozen at:** tag `benchmark-v3-frozen`.

## 13. Post-hoc reporting validator v3.1 (user-approved secondary analysis, 2026-11-18)
- **Change:** one comparative-clause false reject in `prose_claims_consistent` is corrected (see `docs/reviews/2026-11-18_reporting_v3_1_posthoc.md`).
- **Score status:** frozen v3 remains primary. v3.1 is reported only beside v3, from saved outputs (`results/processed/v3_1_rescore/`), and is never pooled or substituted.
- **Experiment B:** still runs and scores with v3, unchanged.
