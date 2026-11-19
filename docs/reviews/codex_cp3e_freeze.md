# Codex CP3e — price-matched-v2 freeze

**Date:** 2026-11-18  
**Base commit:** `f582184`  
**Status:** `protocol_frozen_paid_execution_approved`; ready for manager commit and tag.

The six-call re-pilot is incorporated as immutable evidence: Kimi K3 without a
temperature field and GLM 5 with `temperature=0` both succeeded on all three
synthetic task schemas (6/6 calls, 6/6 parsed). The shared ledger baseline is 13
API attempts and `$0.671384` conservatively priced spend. The frozen manifest
records the user's exact approval wording, **“Approve main run”**, the 2026-11-18
date, 810 logical calls, `$100` shared hard cap, mandatory repeat-1 stop, all
protocol/code/data/evidence hashes, and the pre-main ledger state. Re-pilot
records, invocation log and summary are included in the immutable hash set.

After Claude commits this work and places `price-matched-v2-frozen-v1` on that
exact HEAD, the initial paid command from the repository root is:

```bash
.venv/bin/python -m experiments.run_price_matched_v2 --execute
```

It runs repeat 1 only (270 logical calls), writes
`results/raw/price_matched_v2/repeat1_cost_checkpoint.json`, and stops. After
manual review confirms the checkpoint projection is within `$100`, repeats 2–3
are resumed explicitly with:

```bash
.venv/bin/python -m experiments.run_price_matched_v2 --execute --continue-after-repeat-1
```

Task JSONL and invocation records go to `results/raw/price_matched_v2/`; per-run
prompts, responses, usage, parsed outputs and A1 harness artifacts go to
`results/raw/runs/<run_id>/`; accounting remains in
`results/raw/ledgers/price_matched_v2.json`. The realistic estimate is `$24.24`;
the uncapped static worst case is `$841.39`, so reserve-then-settle enforcement
and the repeat-1 checkpoint remain mandatory.

The full suite passes: **485 passed, 23 skipped**. An offline test substitutes the
required tag and confirms `verify_frozen_protocol()` accepts the exact manifest;
the untagged paid path still refuses before client creation. This turn made no
AWS/model/network call, created no main-run output, changed no raw record or
ledger, and created no tag. Claude will now commit, create the tag, verify, and
execute after review.
