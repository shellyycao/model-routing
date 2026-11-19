# Independent Task Benchmark Plan: Part A extension (A1 Debugging, A2 Extraction, A3 Literature)

**Status (2026-11-18):** the user approved this plan and then gave a standing instruction not to wait for further approvals. A1–A3 are IMPLEMENTED and FROZEN at tag `independent-v1-frozen`, and the paid run follows the freeze.

**Deviations from the plan:**
- **Spot-check:** not done. The user's standing instruction covers it, so the independence limitation in §7 stands, documented.
- **A1 "2 alternative wrong fixes must fail" mutation check:** not implemented. A1 is verified by "reference passes every hidden test, and the buggy version fails at least one".
- **A3 hard-negative design changed before any run, after the keyword-baseline sanity check failed** (baseline nDCG@5 was 1.0). Relevant documents now use paraphrased topic and method wording, and hard negatives mention the query's exact topic and method in a "prior work" sentence. The baseline now averages 0.07.

**Research structure:**

| Part | Topic | Status |
|---|---|---|
| A | Independent task-specific model evaluation | Phase 1 data-workflow stages (done, Experiment A v3) + the NEW A1–A3 |
| B | End-to-end multi-model workflow evaluation | Experiment B v3 |
| C | Explainable routing and counterfactual validation | M5 |

The A1–A3 extension is **additive**. It never feeds Part B or Part C data unless a separately approved methodology says so.

---

## 1. Reusable components (no changes needed)

| Component | Reused for | Location |
|---|---|---|
| Bedrock client: Converse API, bounded retries, no model substitution, per-call JSONL records, cache with repeat bypass, cross-process ledger with hard call and token limits | All model calls | `src/bedrock/client.py`, `usage.py`, `models.py` |
| Structured output parsing with Pydantic | Model responses for A1–A3 | `src/bedrock/structured.py` |
| Provenance: content hashes, deterministic `make_run_id`, `config_hash` | Run IDs, resume, no silent reruns | `src/bedrock/provenance.py` |
| Docker sandbox and `SandboxGate`: verified image, no network or credentials, limits | A1 only (running patched code and hidden tests) | `src/workflow/executor.py`, `src/workflow/stages.py:SandboxGate` |
| Model registry: A/B/C, identical inference settings | All | `configs/models.yaml` |
| Plan/execute runner pattern (`--plan` default, `--execute` with mandatory limits) | New runner | pattern from `experiments/run_stage_benchmark.py` |

## 2. Files and modules that must remain UNCHANGED

These are kept as they are, including their benchmark versions:
- `src/contracts/`
- `src/workflow/`
- `src/evaluation/{cleaning,analysis,reporting,reporting_v3,reporting_v3_1}.py`
- `src/routing/`, `src/explainability/`, `src/analysis/`
- `datasets/projects/`
- `prompts/v1`, `prompts/v2`, `prompts/v3`
- `experiments/run_stage_benchmark.py`, `experiments/run_workflow_grid.py`
- everything under `results/raw/`, plus the tags `benchmark-v2-frozen` and `benchmark-v3-frozen`

If a compatibility change turns out to be necessary, it is reported and needs approval first.

## 3. Proposed independent structure (all NEW paths)
```
src/independent/
  __init__.py            INDEPENDENT_SCHEMA_VERSION = "indep-1.0"
  records.py             IndependentTaskRecord (own schema; NOT a src.contracts record type)
  runner.py              shared plan/execute loop over cases x models (reuses BedrockClient, limits, provenance)
  a1_debugging.py        prompt rendering, response schema, sandbox test harness, scoring
  a2_extraction.py       prompt, schema, field-level P/R/F1 scoring
  a3_literature.py       prompt, schema, ranking metrics, grounding/citation scoring
datasets/independent/
  a1_debugging/          cases/<case_id>/{buggy.py, task.md(model-visible), hidden_tests.py, reference.py, meta.json}
  a2_extraction/         cases/<case_id>/{document.txt(model-visible), schema.json(model-visible), gold.json, meta.json}
  a3_literature/         corpus/<doc_id>.json + queries/<case_id>/{query.md(model-visible), relevance.json, facts.json}
  generate.py            deterministic, seeded generators; --check for byte-reproducibility
prompts/independent_v1/  a1_debugging.txt, a2_extraction.txt, a3_literature.txt (identical across models)
experiments/run_independent_benchmark.py   --task a1|a2|a3|all --plan / --execute (hard limits required)
experiments/analyze_independent.py         -> results/processed/independent/ + report
tests/test_independent_*.py
results/raw/independent/<experiment_id>.jsonl          (experiment ids: indepA1_debug_v1, indepA2_extract_v1, indepA3_lit_v1)
results/raw/runs/<run_id>/                             per-call artifacts (same convention as today)
results/processed/independent/                          tables + figures (own schema "indep-1.0")
results/reports/independent_task_benchmark.md
```
**Separation is enforced in code:**
- The existing routing loader (`src.routing.data`) accepts only `StageBenchmarkRecord` and `WorkflowRunRecord`. It would reject `IndependentTaskRecord` lines, and the new files sit in a separate directory that existing configs never list.
- The analysis pipeline reads them only through a new, separate entry point.

## 4. Datasets and ground truth

All ground truth is **established by construction with deterministic code** and checked by executable tests. No evaluated model (A, B or C) produces any label.

**Independence caveat:** the lead agent that writes the generators is a Claude model (Opus), from the same vendor as evaluated model A (Claude Sonnet 4.6). Two mitigations:
1. Labels are never written by judgment. They are derived mechanically from the generator (the source record, the injected bug, the constructed relevance).
2. The user spot-checks a sample of cases before the freeze (§7).

### A1: Python debugging (10 cases)
- **Construction:**
  - Start from a clean reference function in pure Python stdlib, with a docstring spec.
  - Inject exactly one bug with a documented mutation operator. Operators include off-by-one, wrong comparison, mutable default argument, wrong variable, missing edge case (empty input or None), integer vs float division, wrong exception type, incorrect sort key, state leak between calls, and string encoding/strip.
  - Difficulty mix: 4 easy, 4 medium, 2 hard (two interacting functions).
- **Model sees:** the buggy code, the spec, and 1–2 *visible* example tests.
- **Model must return:** `{fixed_code, bug_location, explanation}`.
- **Hidden tests:** 8–15 per case, written against the reference and including edge cases. Every hidden test must PASS on the reference and at least one must FAIL on the buggy code; both are verified automatically before the freeze.
- **Execution:** inside the existing verified Docker sandbox: no network, read-only inputs, time and memory limits.

### A2: Information extraction (10 cases)
- **Construction:** a seeded generator first creates a structured gold record, for example a purchase order, clinical-trial summary, job posting or incident report (all synthetic). It then renders the record into unstructured text with templates.
- **Deliberate difficulty:**
  - distractors: similar entities and numbers, such as a second date or a quoted competitor price;
  - ambiguous phrasing with one defined resolution rule in the schema;
  - truly missing fields, where gold = `null` and the model must return null rather than guess;
  - unit and format variations.
- **Model sees:** the document and a JSON schema with field descriptions.
- **Gold:** the generating record, with normalisation rules (dates, numbers, case) written in `meta.json` before any run.

### A3: Literature search and review (10 queries over one controlled corpus)
- **Corpus:** a **synthetic, controlled corpus** of about 60 abstract-like documents with synthetic IDs, authors and venues. They are generated from a topic/attribute grid (topic × method × dataset × finding).
- **Relevance labels by construction:**
  - **graded:** 2 = matches the query's topic and method; 1 = topic only; 0 = otherwise;
  - **hard negatives:** near-miss documents that share keywords but have a different topic.
- **Each query:** gets about 20 candidate documents (relevant documents and distractors shuffled with a seed).
- **Model must return:**
  - a ranked top-K list (K = 5) of document IDs;
  - a short synthesis in which every claim cites document IDs.
- **This is NOT live web retrieval and will never be described as such.** It measures ranking and grounded summarisation over a supplied candidate set.
- **Optional, user-approved variant:** a small real-paper corpus with labels supplied by a human. Not part of the default plan.

## 5. Validators and metrics

| Task | Hard gate (mandatory) | Quality metrics (reported separately; no composite score) | Efficiency |
|---|---|---|---|
| A1 | Parseable response; patched code executes in the sandbox | Hidden-test pass rate (per case and mean); functional correctness = all hidden tests pass; bug localisation correct (line range); no regression on the visible tests | Latency, input and output tokens, reasoning chars, verified cost (else `unavailable`) |
| A2 | Schema-valid JSON | Field-level precision, recall and F1 (micro and macro), with null handling: predicted null when gold is null counts as correct; a value when gold is null is a false positive (hallucination); null when gold has a value is a miss. Also: hallucinated-field rate, distractor-capture rate | Same |
| A3 | Parseable response; every cited ID exists in the candidate set | Precision@5, nDCG@5 (graded labels), recall of grade-2 documents; grounding accuracy = share of synthesis claims whose cited documents contain the claimed attribute (checked against `facts.json`); citation consistency = no cited ID outside the ranked list or candidates, and no uncited claims | Same |

**Scoring rules:**
- Every scorer is deterministic and has regression tests, including deliberately wrong answers that must fail.
- **No LLM judge** in the primary metrics.
- A3 grounding is checked by matching each claim's structured fields to the cited documents' structured facts. The response schema requires each claim as `{attribute, value, cited_ids}` in addition to prose.

## 6. Result schema (`IndependentTaskRecord`, new; does not alter contracts)
Fields:
- `schema_version`, `experiment_id`, `task` (a1, a2 or a3), `case_id`, `model_alias`, `model_id`, `repeat_index`
- `prompt_version`, `prompt_hash`, `dataset_version`, `case_hash`, `invocation_ids`
- `status`: passed, failed or void_infra; plus `failure_type` and `failure_detail`
- `parse_ok`, `execution` (A1 only), `scores` (task metrics), `timings`
- `input_tokens`, `output_tokens`, `reasoning_chars`, `truncated`
- `cost_usd` (null if unpriced) and `cost_status`
- `config_hash`, `artifacts`

Raw records are append-only. Analysis is derived only from saved files.

## 7. Methodological risks and acceptance tests

| Risk | Mitigation and acceptance test |
|---|---|
| Ground truth correlated with one vendor (generator author is Claude) | Labels come from construction, not judgment; the user spot-checks 3 cases per task before the freeze; independence is documented as a limitation |
| A1 hidden tests too weak or wrong | Automatic check: the reference passes 100% and the buggy version fails at least 1 test. Mutation check: 2 alternative wrong fixes per case must fail. |
| A1 code safety | Sandbox only, with the gate and verified image; the existing isolation tests must pass before running |
| A2 ambiguity penalising valid readings | The schema states one resolution rule per ambiguous field; ambiguous fields are reported separately |
| A3 relevance labels too easy (keyword matching) | Hard negatives sharing keywords; a check that a BM25 keyword baseline (deterministic, no LLM) does not reach a perfect nDCG |
| Output-length truncation (as seen for gpt-oss in Phase 1) | Same `maxTokens` (4096) for all models, as in Part A; truncation reported as its own failure type; no per-model change |
| Small n (10 cases per task) | Wilson intervals and per-case tables; exploratory framing; optional repeats (×2) if approved |
| Contamination of Parts B and C | Separate schema, experiment IDs, directories and analysis entry point; a test asserts the routing loader rejects these records |
| Post-hoc tuning | Generators, prompts and scorers frozen and tagged (`independent-v1-frozen`) before any paid call; any later change goes to a new version |

**Acceptance before the freeze:**
- `datasets/independent/generate.py --check` is byte-reproducible.
- Every validator test passes, and the reference solutions or gold answers score 100%.
- The deliberately wrong fixtures fail.
- The full existing test suite still passes, with no regression in Parts A, B or C.

## 8. Estimated new AWS usage (planning target, NOT authorised)

| Task | Cases × models | Calls | Est. input tokens per call | Est. output tokens per call | Est. total input / output |
|---|---|---|---|---|---|
| A1 Debugging | 10 × 3 | 30 | ~2,500 | ~1,500 (gpt-oss more, reasoning) | 75k / 45k |
| A2 Extraction | 10 × 3 | 30 | ~2,000 | ~800 | 60k / 24k |
| A3 Literature | 10 × 3 | 30 | ~8,000 (about 20 abstracts) | ~1,500 | 240k / 45k |
| **Total** | | **90** | | | **~375k / ~115k** (worst-case output cap 90 × 4096 = 369k) |

- **Cost:** prices are unverified, so the cost is recorded as `unavailable`. At approximate public list prices (unverified), the base run is roughly **$1–3**, and worst case under $6. Optional ×2 repeats would roughly triple that.
- **Runtime:** about 10–20 minutes sequentially. A1 includes sandbox runs.

## 9. Website integration (later; no web work now)
- **Separate source:** the website will have a distinct "Part A — Independent tasks" section that reads only `results/processed/independent/` (schema `indep-1.0`).
- **Phase 1 data-workflow stages** (Experiment A) stay in Part A under their own heading. Part B (workflow paths) and Part C (routing, faithfulness, counterfactual validity) keep their own sources.
- **No cross-pooling:** no table or figure pools A1–A3 scores with workflow or routing data. Any cross-part comparison needs a separately approved methodology.

## 10. Decisions requested from the user
1. **Approve the A1–A3 design**, including synthetic-by-construction ground truth and a synthetic controlled corpus for A3. The alternative for A3 is a real-paper corpus with labels you supply.
2. **Approve implementation**, offline: generators, scorers and tests, then the freeze.
3. **After the freeze, approve the paid run:** 90 calls with hard limits. Optionally also approve ×2 repeats.
4. **Spot-check:** confirm you will spot-check about 3 cases per task before the freeze, or waive this and accept the independence limitation as documented.
