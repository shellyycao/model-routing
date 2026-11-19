# Codex compatibility-pilot executor checkpoint

**Date:** 2026-11-18  
**Base commit:** `670fab0`  
**Status:** Ready for manager review; the approved pilot has **not** been run.

The price-matched-v2 compatibility-pilot executor is implemented at
`experiments/run_price_matched_v2_pilot.py`. Its default behavior is plan-only;
paid execution requires the exact `--execute-approved-pilot` flag. It derives
only the nine configured calls, preserves their fixed task-major/model order,
and uses the existing Bedrock client with its unchanged transient-only retry
policy (maximum five attempts). The pilot enforces a reserve-then-settle hard
cap of $15 on the shared `results/raw/ledgers/price_matched_v2.json` ledger, so
any pilot spend also counts toward the later $100 experiment cap.

Each attempted call records success/error, raw input/output/reasoning-token
usage, effective parameters, stop reason, schema-parse status, latency, and
cost. Results are designed for `results/raw/price_matched_v2_pilot/`; response
content is not quality-scored. A parameter-related failure blocks that model's
remaining pilot slots and records the reason, without changing parameters or
adding fallback calls. Resume and orphaned-invocation guards prevent accidental
duplicate or unaccounted calls.

Offline mock tests cover the execution flag, exact order, shared-ledger cap,
stop-on-parameter-failure behavior, record fields, resume behavior, and orphan
refusal. The full suite passes: **481 passed, 23 skipped**. The regenerated plan
and protocol manifest mark the pilot as approved but unexecuted and include the
executor hash (`ae53ee25ac79d48d43d0c06a9ec96a9804fb63b9c09fe29738b276c0cc606ab4`).

No AWS client was invoked, no model or network call was made, no pilot raw-data
directory was created, no ledger was changed, and no tag was created. The main
810-call run remains unauthorized and unfrozen. Per the checkpoint instruction,
work stops here for Claude's review and execution decision.
