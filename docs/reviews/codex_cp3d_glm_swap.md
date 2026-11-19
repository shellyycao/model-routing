# Codex CP3d — GLM 5 swap and re-pilot executor

**Date:** 2026-11-18  
**Base commit:** `85b7bd6`  
**Status:** Ready for manager review; the approved six-call re-pilot has **not** run.

The final price-matched-v2 model set is Sonnet 4.6, Kimi K3 and GLM 5. The offline
verifier mechanically extracted GLM 5's us-east-1 regional standard on-demand
price as **$1.00/M input and $3.20/M output** and requires saved real-invoke
evidence in addition to control-plane metadata. Grok 4.7 is retained only as a
removed-model record: three real pilot calls returned `AccessDeniedException`
despite AVAILABLE/AUTHORIZED metadata. The disclosed blended-price range grows
from 2.00× to 4.26× because the user's final selection prioritizes generation
match over price match.

The registry and benchmark runner now send `temperature=0` for Sonnet and GLM,
while Kimi alone omits the field following its pilot ValidationException and the
user's approval. The plan, access verification, analysis guard, budget, manifest
and protocol document were regenerated. Static worst-case exposure is **$846.32**
and the stated-assumption realistic estimate is **$24.34**, both including the
existing conservatively recorded pilot spend of **$0.63371**; the shared `$100`
hard cap and repeat-1 checkpoint remain unchanged.

`experiments/run_price_matched_v2_pilot.py` now exposes only
`--execute-approved-repilot` for new paid work. It permits exactly six fixed,
task-major calls: Kimi-without-temperature and GLM-with-temperature-0 across the
three synthetic examples. It uses the same ledger, `$15` pilot cap and unchanged
transient-only retry policy. Re-pilot records are isolated in `repilot_*` files;
a parameter failure stops that model without parameter mutation or replacement
calls. Offline tests cover the flag gate, exact order, cap, effective parameters,
stop-on-failure, append-only separation, resume and orphan protection.

The full suite passes: **484 passed, 23 skipped**. No CP3d AWS client, model call
or network request was made; no re-pilot raw file was created; the shared ledger
was unchanged (SHA-256 `66bb51becd20c624762a9d9a7d5b55847526ca098ae776bea42e07aa80f73d5f`);
and no freeze tag was created. Pilot executor SHA-256:
`483f5b8bdd76199609728549e04efe1555c1de17355ad81e2b8a735f3de1745f`.
Work stops here for Claude's review and execution decision.
