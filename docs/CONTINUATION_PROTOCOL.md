# Continuation Protocol

## Status and Ordering

**Status: post-hoc / exploratory protocol; paid execution approved pending freeze tag, 2026-11-19.**
Claude asked: **“花费上限 $15（预计实际约 $1.41），补跑这 40 次，行吗？”** The user's exact reply
was **“批准了”**. The approval covers exactly the 40 reporting calls below and the separate $15
reserve-then-settle ledger; it does not authorize a larger inventory or cap. These rules and runner
were committed before approval. The CP8b manifest freezes that approval and all hashes, but Claude
must still commit it and create exact tag `continuation-v1` before a Bedrock client can be built.

No corrected Part B feasibility number may be computed before the continuation records are
complete. Frozen raw records, diagnostic replays, tags, scores, and conclusions are never modified.

## Eligible Inventory

Eligibility is mechanical and outcome-blind. Start from the effective Part B cells: all 156 original
group cells, and the 156 price-matched cells after the five approved Docker reruns are resolved.
A cell is eligible only when:

1. a frozen stage failed with the exact text `Object of type int64 is not JSON serializable`;
2. the committed pinned-image diagnostic replay says that stage passes its frozen validator; and
3. every downstream stage is saved as `blocked_by_invalid_artifact` or
   `not_run_upstream_failure`—that is, it was never called.

The committed inventory contains 40 eligible cells, all stalled after analysis:

| Group | Recovered-stage model | Recovered stage | Eligible cells | Remaining stage calls |
|---|---|---|---:|---:|
| Original 4096 | Nova Pro (`B`) | analysis | 9 | 9 reporting |
| Original 4096 | gpt-oss-120b (`C`) | analysis | 2 | 2 reporting |
| Price-matched 16384 | GLM 5 (`C`) | analysis | 29 | 29 reporting |
| **Total** | | | **40** | **40** |

Eleven cleaning replays pass the frozen validator but are not eligible: their downstream stages
already ran, so continuing them would duplicate observed calls. Analysis replays that still fail
the frozen validator are also excluded. The runner freezes a SHA-256 of the 40-cell inventory and
refuses any mismatch.

### Exact corrected Part B treatment of the 11 cleaning recoveries

The 11 recovered cleaning cases **are included** in the later exact corrected Part B view even
though they receive no new call. That view substitutes the replay-validated cleaning artifact/status
for the serialization failure and then uses the already observed analysis and reporting stage
records exactly as saved. It does not rerun, repair, or selectively discard those downstream
outcomes. The report must disclose that their original downstream handoffs contained upstream
cleaning status `failed`; consequently those downstream outcomes are conditional on seeing that
label even though the corrected cleaning status is `passed`. At least these cases remain a labelled
sensitivity rather than a reconstruction of what the downstream models would have done under a
different status label.

No exact corrected Part B feasibility count, rate, or model comparison is computed until all 40
continuation records exist (40 JSONL lines, with any infrastructure voids explicitly resolved or
reported). Q1 may compute stage-level corrected rates earlier because it does not infer downstream
workflow outcomes.

## Continuation Semantics

The continuation reconstructs `StageArtifacts` and calls the same `build_handoff` /
`build_and_save` code used by `WorkflowOrchestrator`:

- A prior stage that genuinely ran contributes its saved model structured output, original model
  code, actual output files, verified-result summary, and saved passed/failed status.
- The recovered analysis stage contributes the **model's original structured output and original
  code text**, not rewritten model logic. Its files are the serialization-only replay's recovered
  `findings.json`; the file hash, frozen-validator hard pass, and pinned replay image are verified
  before use. Its handoff validation status is `passed`.
- Consequently the reporting prompt receives the same categories of information as any ordinary
  workflow handoff: original objective, completed stages, model output descriptions, original
  executed code, actual recovered file and verified findings, and only `passed`/`failed` status.
  Validator details and ground-truth expected values do not enter the prompt.

Only the missing reporting stage runs for the current frozen inventory. It uses the reporting model
already specified by the original path, prompt version v3, the original repeat index, fresh/no-cache
mode, and the same reporting validator. Each result has a new deterministic run ID and an explicit
`continued_from` link to the stalled run. The continuation record also stores the recovered output
hash and validation evidence. Originals and replays remain append-only and unchanged.

In the later exact corrected Part B view, the original passed cleaning stage, recovered analysis
stage, and newly executed reporting stage form the corrected cell. A non-infrastructure reporting
pass or failure yields an exact corrected feasibility result. A `void_infra` continuation produces
no substantive replacement until a separately permitted infrastructure retry succeeds. Every
replacement is labelled corrected-view-only; the frozen cell is always shown beside it.

## Models, Parameters, and Sandbox

The continuation uses the original group-specific registries and verified prices:

| Group | Models available to remaining calls | maxTokens | Temperature |
|---|---|---:|---|
| Original | Sonnet 4.6 (`A`), Nova Pro (`B`), gpt-oss-120b (`C`) | 4096 | `0` for all |
| Price-matched | Sonnet 4.6 (`A`), Kimi K3 (`B`), GLM 5 (`C`) | 16384 | `0` for A/C; field omitted for Kimi |

The existing transient-only retry policy is unchanged (maximum five paid attempts; no semantic
retry, re-prompt, model substitution, or automatic parameter removal). The recovered artifacts
must show execution in immutable image
`sha256:88988a15503bdb96538c3dd62244a79879d5c7848397db18b1267ccfd0a9727a`.
All current missing stages are reporting and execute no model-generated code; if a frozen inventory
ever required a code stage, Docker run/availability/lease would have to use that exact ID and an
unavailable sandbox would be `void_infra`, never model failure. `continuation-v1` instead refuses an
inventory containing anything other than the reviewed 40 reporting-only calls.

No compatibility smoke test is needed. These exact six models, prompt/schema version, maxTokens,
temperature behavior (including Kimi's omitted field), and Bedrock Converse path already completed
the source experiments. A smoke test would spend money without testing the scientifically new
operation, which is the offline recovered-artifact handoff and is covered by mocks and hash checks.

## Call Inventory and Budget

The 40 logical calls are fixed before execution:

| Group | Reporting model | Calls | Static worst case | Realistic estimate |
|---|---|---:|---:|---:|
| Original 4096 | Sonnet 4.6 (`A`) | 4 | $2.2776 | $0.1780 |
| Original 4096 | Nova Pro (`B`) | 5 | $0.6101 | $0.0411 |
| Original 4096 | gpt-oss-120b (`C`) | 2 | $0.0457 | $0.0043 |
| Price-matched 16384 | Sonnet 4.6 (`A`) | 7 | $11.0759 | $0.3138 |
| Price-matched 16384 | Kimi K3 (`B`) | 7 | $11.0873 | $0.7592 |
| Price-matched 16384 | GLM 5 (`C`) | 15 | $4.9898 | $0.1129 |
| **Total** | | **40** | **$30.0864** | **$1.4093** |

Static worst case is 200 paid attempts: for every logical call, five attempts each use the
project/stage conservative prompt-token bound and the group's full maxTokens output allowance. It
totals 2,814,045 input and 2,600,960 output tokens.

The realistic estimate assumes one successful attempt per call. For each group/model/reporting
cell it uses the observed mean input and output tokens from successful effective Part B invocations
in that original run—not a cross-model proxy. The source sample sizes are original A/B/C =
30/17/35 and price-matched A/B/C = 43/37/43. It totals approximately 128,048 input and 99,268 output
tokens. This is a planning estimate, not a guarantee.

## Ledger and Runtime Cap

Use the new ledger `results/raw/ledgers/continuations.json`, invocation log
`results/raw/continuations/invocations.jsonl`, and the approved **$15 hard cap**. The ledger uses the
existing atomic reserve-then-settle mechanism and counts successful, failed, and retry attempts.
Missing usage is conservatively charged; it is never zero. The cap is below the $30.0864 five-retry
static exposure but more than ten times the $1.4093 realistic estimate. The accepted implication is
that the runner stops with `budget_refused` rather than raising the cap if
usage or retries consume the allowance. Maximum ledger limits are 200 attempts, 2,814,045 input
tokens, and 2,600,960 output tokens; the $15 constraint is additionally authoritative.

## Runner, Freeze Gate, and Approval

`experiments/run_continuations.py` is plan-by-default:

```bash
.venv/bin/python -m experiments.run_continuations
```

The approved paid command remains inoperative until the CP8b manifest is committed and tagged:

```bash
.venv/bin/python -m experiments.run_continuations --execute-approved-continuations
```

Before constructing any Bedrock client, the paid path requires:

1. manifest `results/processed/continuation_protocol_manifest.json` with status
   `continuation_frozen_paid_execution_approved`, exact approval wording/date,
   `paid_execution_approved=true`, and hard cap `$15`;
2. exact tag `continuation-v1` at HEAD;
3. matching hashes for both rule documents, runner, diagnostics JSON and replay tree, both frozen
   Part B stores, registries/pricing evidence, prompts, projects, handoff/stage/executor code, and
   reporting validator; and
4. exactly 40 eligible cells with the frozen inventory hash.

CP8b creates the approval manifest but does not create the tag. Claude will review and commit the
manifest, create exact tag `continuation-v1`, verify the gate, and only then execute.

Execution/progress contract:

- exact command: `.venv/bin/python -m experiments.run_continuations --execute-approved-continuations`;
- append-only task records: `results/raw/workflow_continuations/continuation_v1.jsonl`;
- per-run artifacts: `results/raw/continuations/runs/<run_id>/`;
- invocation log: `results/raw/continuations/invocations.jsonl`;
- separate ledger: `results/raw/ledgers/continuations.json`;
- **40 task-record lines means the planned inventory is complete**. Progress is the number of
  distinct `continued_from` values in that task-record file, never the invocation-log line count.

## Failure Classification and Resume Safety

Outputs are append-only under `results/raw/workflow_continuations/` and
`results/raw/continuations/runs/`. The runner reads only the dedicated continuation record file for
resume bookkeeping; invocation JSONL is never mistaken for a task record. A cell with an existing
`continued_from` record is not called again. A run directory collision without a record fails
closed for manual audit.

API validation/access errors and exhausted transient retries retain the existing infrastructure
classification. Sandbox/Docker unavailability, image mismatch, or a missing recovered artifact is
`void_infra`/execution infrastructure evidence, never a model-quality failure. The runner never
selects replacement models, changes parameters, or adds calls based on observed answer quality.

## Outputs and Corrected-View Use

Each new record stores the new run ID, `continued_from`, group, original cell coordinates,
recovered stage/output hash/frozen validation, only the newly run stage record, and an outcome. Raw
continuations are not written into either frozen Part B JSONL. A later analyzer combines them only
in a new explicitly labelled corrected-view processed JSON and report; it must show frozen and
corrected feasibility side by side and report continuation voids separately.

## Offline Verification

Offline tests cover exact inventory and call counts, budget arithmetic and observed-mean sources,
plan-only behavior without runtime construction, manifest/tag/hash/approval refusal, recovered
artifact hash and image checks, handoff contents (original code plus recovered output, without
validator details), and idempotent `continued_from` resume selection. Mocks exercise record writing
and infrastructure classification without Bedrock, Docker, model, or network calls.
