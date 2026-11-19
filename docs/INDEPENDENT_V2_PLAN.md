# Independent Benchmark v2 Frozen Protocol

**Version:** `independent-v2-1.0`

**Status:** v1.1 pricing-and-budget amendment approved for paid execution; no paid calls at freeze

**Relationship to existing tags:** distinct from the workflow tag `benchmark-v2-frozen`

## Research objective

Independent v2 tests whether the v1 model-specialization observations survive increased task difficulty, greater case diversity, and explicit separation of content quality from operational reliability.

The protocol was frozen before any evaluated model saw a v2 case. No prompt, case, label, test, scoring rule, or token limit may be tuned in response to model performance.

## Dataset design

| Task | Cases | Easy | Medium | Hard | Primary additions |
|---|---:|---:|---:|---:|---|
| A1 debugging | 30 | 10 | 10 | 10 | 15 task families, two mutations per family, interacting defects, state/boundary/ordering issues |
| A2 extraction | 30 | 10 | 10 | 10 | 10 document families, heterogeneous formats, conflicts, missing fields, conversions, distractors |
| A3 controlled review | 30 | 10 | 10 | 10 | 20 candidates/query, direct/partial/hard-negative strata, explicit label rationales |

Generated data lives under `datasets/independent_v2/`. The generator is deterministic and validated with:

```bash
.venv/bin/python -m datasets.independent_v2.generate --check
.venv/bin/python -m pytest -q tests/test_independent_v2.py
```

### A1

- Reference code and hidden checks are independently executed during generation.
- Every reference passes every check and every injected bug fails at least one.
- At most two cases share a task family.
- Hard cases include interacting state, ordering, boundary, validation, and mutation defects.
- Scoring reports functional correctness, hidden pass rate, operational execution, and bug-location recall separately.

### A2

- Ground truth comes from the source record used to render each document.
- Formats include email, account tables, protocol amendments, manifests, job cards, timelines, endorsements, funding notices, listings, event notices, and change logs.
- Conversion cases include discounts, annual-to-monthly, weekly-to-monthly, pounds-to-kilograms, square-feet-to-square-metres, and abbreviated monetary amounts.
- Scoring separately reports `content_correct`, `content_f1`, `schema_compliant`, and `operational_success`.
- A recoverable bare object may be content-correct while remaining a schema/operational failure.

### A3

- Retrieval is controlled: the model ranks only the supplied candidates.
- Direct relevance requires both requested topic and method. Partial matches get grade 1; unrelated and prior-work-only mentions get grade 0.
- Ranking, evidence grounding, and citation accuracy are independent outputs.
- Canonical facts contain accepted surface forms, preventing the frozen-v1 canonical/paraphrase mismatch.
- All relevance labels are marked `human_adjudicated` after the locked first pass and targeted rereview.

## Ground-truth provenance and author bias

The candidate labels were generated deterministically by code authored in this workstream, not by an evaluated model. That removes direct Claude-generator reuse but does not prove benchmark neutrality. Provenance and label rationales remain in every case.

Before freeze:

1. A human reviewer must adjudicate all A3 query rules and a minimum of every grade-2 document plus a stratified sample of grade-1/0 documents.
2. Any disputed label must be resolved without viewing evaluated-model outputs.
3. The adjudication manifest and changes must be recorded.
4. The finalized dataset tree, prompts, response schemas, scorers, token limits, pricing provenance, and runner configuration must receive hashes and the `independent-v2-frozen-v1.1` tag.

The first blinded adjudication pass is complete and locked. It agreed on 167/180 proposed grades. All 13 disagreements identified the same source wording defect: `detecting abusive online content` did not establish the query topic `hate speech detection`. Candidate 0.2 corrected the surface form to `detecting hate speech`. The targeted blinded rereview accepted all three corrected query rules and agreed with all 18 proposed labels, leaving no unresolved disagreement.

## Primary and secondary metrics

| Task | Primary | Operational | Secondary |
|---|---|---|---|
| A1 | functional correctness | code loads and harness completes | hidden pass rate, bug-location recall |
| A2 | content correctness/F1 | parse + exact schema wrapper | null accuracy, error type |
| A3 | nDCG@5 | valid five-ID response with minimum claims | grade-2 recall, grounding, citation accuracy |

No single composite score will pool these dimensions.

## Comparison with v1

- v1 and v2 raw scores are not directly interchangeable because case composition and difficulty differ.
- Common conceptual anchors are preserved: Python repair, structured extraction, and controlled evidence ranking.
- Where feasible, saved v1 outputs will be rescored using compatible decomposed metrics.
- Results will be stratified by difficulty and task family.
- Ranking stability will be described under both strict operational and recoverable-content views.
- Confidence intervals will be reported; with n=30 per cell, conclusions remain bounded to these cases and models.

## Prospective inference protocol

- Temperature: 0 for every model.
- One run per model-case cell in the core experiment; repeats require a separately predefined subset and approval.
- A1 max output: 4,096 tokens.
- A2 max output: 4,096 tokens.
- A3 max output: 8,192 tokens. This task-specific cap is fixed prospectively because v1 showed reasoning-token truncation at 4,096 and v2 inputs are harder.
- Identical task prompt and output contract for every model.
- No cache reuse.
- Infrastructure failures are `void_infra`, never model failures, and are retried only under a predefined uniform policy.
- Model-output parse repair is not part of the primary score; recoverable content is a disclosed secondary analysis.

## Approval-ready size and guardrails

The following is a plan, **not authorization to run**.

### Models

| Alias | Exact Bedrock model ID |
|---|---|
| A | `us.anthropic.claude-sonnet-4-6` |
| B | `us.amazon.nova-pro-v1:0` |
| C | `openai.gpt-oss-120b-1:0` |

### Calls and token limits

| Task | Cases | Models | Logical calls | Max output/call | Worst-case output tokens | Estimated input tokens* |
|---|---:|---:|---:|---:|---:|---:|
| A1 | 30 | 3 | 90 | 4,096 | 368,640 | 62,178 |
| A2 | 30 | 3 | 90 | 4,096 | 368,640 | 63,009 |
| A3 | 30 | 3 | 90 | 8,192 | 737,280 | 187,557 |
| **Total** | **90** | **3** | **270** | — | **1,474,560** | **311,568** |

\*Input estimates use rendered character count/4 plus a 512-token structured-output allowance per call. The execution guard should conservatively cap total input at **500,000 tokens**.

Transport attempts may exceed logical calls under the existing bounded five-attempt retry policy. The frozen upper bound is 1,350 API attempts, while successful model generations must not exceed 270 without a new approval.

### Cost status

Official AWS Price List entries retrieved on 2026-11-18 are recorded in `configs/models.yaml`:

- Claude Sonnet 4.6 US Geographic CRIS: $3.30/M input and $16.50/M output tokens;
- Amazon Nova Pro standard on-demand: $0.80/M input and $3.20/M output tokens;
- OpenAI gpt-oss-120b standard on-demand: $0.15/M input and $0.60/M output tokens.

At estimated input and the full per-call output caps, the plan is $10.42. With the aggregate
500,000-input-token guard and all input conservatively priced at the highest rate, completed-call
exposure is $11.63. If every logical call used all five attempts and every attempt were billed at
its full reservation, the conservative exposure is $52.10. The user authorized a hard maximum of
$100.00. Every retry reserves its full input, output, and dollar worst case before it is sent.

### Stopping conditions

- stop before the first call unless the protocol has a frozen tag and explicit user approval;
- stop at 270 successful logical calls, 1,350 API attempts, 500,000 input tokens, or 1,474,560 output tokens;
- stop before admitting an attempt that would exceed the $100.00 conservative dollar ledger;
- stop after five consecutive infrastructure failures or if the verified sandbox gate fails;
- stop if the request would use a different model ID, prompt hash, dataset hash, scorer version, or token cap;
- never stop or modify the protocol because one evaluated model is performing poorly;
- do not selectively rerun model failures; only uniform, predefined infrastructure retries are allowed.

## Freeze checklist

- [x] 30 cases per task and 10 per difficulty tier
- [x] deterministic generation and validator tests
- [x] separate v1 namespace and no historical overwrite
- [x] separate content/schema/operational metrics
- [x] controlled-retrieval wording for A3
- [x] human v1 spot-check returned, locked, and analyzed
- [x] blinded A3 v2 adjudication packet prepared and validated
- [x] first-pass A3 v2 adjudication returned, locked, and analyzed
- [x] systematic hate-speech topic-surface defect corrected before version 1.0
- [x] independent A3 label adjudication completed
- [x] protocol and runner hashes recorded
- [ ] official prices verified or token-only budget explicitly accepted
- [x] original `independent-v2-frozen` tag preserved
- [x] pricing-and-budget amendment frozen as `independent-v2-frozen-v1.1`
- [x] paid execution explicitly approved with a $100.00 maximum
