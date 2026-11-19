# Codex CP3f — repeat-1 resume bookkeeping fix

**Date:** 2026-11-18  
**Base/tag:** `b1ad4d5` / `price-matched-v2-frozen-v1`  
**Status:** v1.1 amendment ready for manager commit and tag; main run not resumed.

Repeat 1 remains complete and valid: 270 calls, 0 `void_infra`, `$6.8974832`
evaluation cost, and checkpoint projection `$21.3638336 <= $100`. The attempted
resume crashed before any repeat-2/3 call or ledger reservation because
`_completed()` scanned `invocations.jsonl` as though it were a task record and
looked for a top-level `run_id`. The ledger remained at 283 calls.

The fix is deliberately narrow: `_completed()` now reads only
`price_matched_v2_a1.jsonl`, `price_matched_v2_a2.jsonl`, and
`price_matched_v2_a3.jsonl`. A regression test creates those task records beside
an invocation log whose run ID is nested under `context`; the completed set is
recovered without reading the invocation row. No data, prompt, scorer, model,
parameter, ordering, call-count, budget or checkpoint rule changed.

The freeze manifest remains `protocol_frozen_paid_execution_approved`, retains
the user's “Approve main run” approval, records the execution-only amendment and
new runner SHA-256
`c61f8854639acbcd31b6333de8cc8cdab1e9df6ad498939ba7c723f7ac3549ef`,
and now requires `price-matched-v2-frozen-v1.1`. The old v1 tag is explicitly
retained. Offline tests confirm v1 alone is rejected and a simulated exact v1.1
tag passes `verify_frozen_protocol()`.

After Claude commits the amendment and creates the new tag, the approved resume
command remains:

```bash
.venv/bin/python -m experiments.run_price_matched_v2 --execute --continue-after-repeat-1
```

The full suite passes: **487 passed, 23 skipped**. Hashes of the ledger,
invocation log, three task JSONLs, checkpoint and the aggregate run-artifact tree
are unchanged from the start of this turn. No raw repeat-1 data was modified,
deleted or rewritten; no model/network call was made; and no tag was created or
deleted by Codex. Work stops here for Claude's review, commit and v1.1 tag.
