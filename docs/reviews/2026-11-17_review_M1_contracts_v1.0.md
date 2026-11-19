# Review: M1 Bedrock client and contracts v1.0 (commit 54af241)

- **Reviewer:** Research Reviewer (read-only, run as the built-in Plan agent following `.claude/agents/research-reviewer.md`)
- **Date:** 2026-11-17
- **Scope:** `src/bedrock/*`, `configs/models.yaml`, `src/contracts/*`, `tests/test_bedrock_client.py`, `tests/test_contracts.py`, `experiments/m1_smoke.py`, `results/raw/*`
- **Not reviewed:**
  - The test suite was not run.
  - Discovery script, datasets, sandbox, workflow, routing and web code (none of it existed yet).
  - Real Bedrock behaviour: temperature handling for gpt-oss, billing of timed-out requests.
  - Pricing sources.

## Verdict

The basic M1 guarantees are met:
- no model fallback;
- a missing price is recorded as unavailable, not $0;
- single-threaded call and token limits are enforced;
- errors of the caught types are logged.

M1 should not be accepted for concurrent or repeated experiments until B1 and B2 are fixed. The contracts need B3 and M6–M11 before records accumulate.

## Findings and disposition

| ID | Severity | Summary | Owner | Disposition |
|---|---|---|---|---|
| B1 | BLOCKER | Hard limits can be bypassed under concurrency and across processes: `check()` is unlocked, counts rise only after the call, and the ledger is last-writer-wins | Infra | Sent to the Infra agent |
| B2 | BLOCKER | A repeat with the default `use_cache=True` silently reuses a cached response. Experiment-B path prefixes share outputs without being documented. | Infra (client), Workflow (prefix policy) | Client fix sent to Infra. Prefix-sharing policy goes to Wave 2 and needs a user decision. |
| B3 | BLOCKER | The feasibility gate can be bypassed by an incomplete `stages` list | Lead | Fixed in contracts v1.1 |
| M1 | MAJOR | Some exception types escape with no InvocationRecord | Infra | Sent |
| M2 | MAJOR | Limits count logical successes, not attempts; failed calls are not counted | Infra | Sent |
| M3 | MAJOR | Cache hits distort cost and latency (logged as $0 with the original latency) | Infra (record), Lead (`StageRunRecord.cache_hit`) | Client part sent; contract part fixed in v1.1 |
| M4 | MAJOR | `parse_error` record double-counts tokens; `validation_status` is never persisted | Infra | Sent |
| M5 | MAJOR | A missing usage block becomes $0 for a priced model | Infra | Sent |
| M6 | MAJOR | The leakage check is only declarative; evidence carries no `project_id` | Lead | Fixed in v1.1: typed evidence refs validated against training projects, plus `training_data_hash`. The loader-level filter is the XAI Researcher's job. |
| M7 | MAJOR | The counterfactual hash is unstable (nested key order) and can be defeated (reset and re-hash, `model_copy`) | Lead | Fixed in v1.1: canonical JSON over an explicit field list, frozen model, hash required at load. The hash-chained append-only log is the XAI Researcher's job. |
| M8 | MAJOR | `CounterfactualPrediction` is missing uncertainty, strategy/version/config, absolute values and a key convention | Lead | Fixed in v1.1 |
| M9 | MAJOR | Quality has no reference basis (ground truth vs conditional reference); no artifact hashes; no `failure_policy` | Lead | Fixed in v1.1 |
| M10 | MAJOR | `DecisionTrace` can't support a faithfulness check (no selection steps, no consistency validators, no trace hash) | Lead | Fixed in v1.1 |
| M11 | MAJOR | Infra failures count as infeasible | Lead | Fixed in v1.1: `outcome` is `feasible`, `infeasible` or `void_infra` |
| minor | MINOR | Input-token estimate isn't a worst case; `dollar_guard_active` on a fresh client; `Pricing.verified` ignores source/date; duplicate model IDs; non-atomic cache writes; no `run_id` in context | Infra | Sent |
| minor | MINOR | `cost_status` is a free string; `StageBenchmarkRecord` consistency; `parse_path_id` doesn't validate; prompt hash; S4 target project | Lead | Fixed in v1.1 |
| minor | MINOR | Smoke-test content checks are only printed to stdout | Lead | Accepted. The persisted statuses are consistent; content checks will be persisted from M3 onwards. |

## Test-quality notes

- **Tests to add:**
  - concurrency limits;
  - `repeat_index` combined with the default cache setting;
  - the input-token limit;
  - unhandled exception types;
  - cache-hit semantics;
  - token double-counting on parse errors;
  - a missing stage in the feasibility check;
  - reset-and-rehash of the counterfactual hash and nested key order;
  - `DecisionTrace` consistency.
- The Reviewer's full report is in the lead's session transcript; this table is the authoritative disposition.
