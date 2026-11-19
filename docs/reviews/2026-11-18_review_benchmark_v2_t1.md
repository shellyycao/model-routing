# Independent review: benchmark v2 / T1

- **Reviewer:** independent read-only Codex sub-agent following `.claude/agents/research-reviewer.md`
- **Date:** 2026-11-17 EST / 2026-11-18 UTC
- **Scope:** the complete uncommitted T1 diff against handover commit `140a2ad`, the original benchmark-validity review, T1 acceptance criteria, generated artifacts and regression tests
- **Method:** read-only inspection. The reviewer made no file changes and did not run paid or live-model calls.

## Final verdict

**APPROVE BENCHMARK-V2 FREEZE.** No BLOCKER, MAJOR or MINOR finding remains in the reviewed T1 implementation.

## Review history and dispositions

The reviewer initially blocked the freeze and the lead fixed each finding before requesting another read-only pass:

1. Near-empty `"See values"` findings could pass. A mandatory substantive-statement check and literal regression were added; all authoritative structured values, directions, rankings and derivations are now rendered.
2. Structured claims could contradict prose. Deterministic checks now reject explicit metric/group swaps and novel wrong values under machine-checkable aliases, with regressions for values before/after aliases and non-ranking metrics.
3. Cleaning-log counts were not connected to workflow validation. Trusted canonical counts now reach ground-truth reporting validation; conditional validation correctly receives none.
4. Requiring every metric in prose exceeded the prompt. The rule was narrowed to one supported numeric finding per statement, and prompt v2 states that requirement explicitly.
5. Context-free direction-word parsing could false-reject correct prose. It was removed; validated structured direction is authoritative and rendered.
6. Broad prose association could false-reject natural multi-metric sentences. Hard attribution was restricted to adjacent machine-checkable forms; both natural sentence orders have passing regressions.
7. Natural churn aliases such as `Basic churn rate` and `2021 churn rate` could escape group-swap checks. Natural aliases now remove metadata tokens while retaining the group label; canonical q2/q3 swap regressions fail as required.
8. The advisory unsupported-claim threshold is preregistered as 2 claims per report.

The final focused pass confirmed that the churn aliases remain scoped to ranking-labelled metrics, prefer the longest overlap, require strict numeric adjacency, and introduce no observed surrounding false-positive regression.

## Verified by inspection

- Dataset generator v2.0, four structurally varied synthetic projects, semantic duplicates, derived-step questions and previously unused columns.
- Explicit two-file input allow-list for `support_operations`.
- BOM handling and 0.011 monetary tolerance.
- Reporting validator v2.0: structured value, direction, ranking, derived-value, substantive-statement and explicit prose-attribution checks.
- Prompt v2, with v1 preserved.
- Ground-truth isolation and no new credential, pricing, routing, oracle or causal-claim issue in the T1 diff.

## Lead verification supplied to the reviewer

- `.venv/bin/python -m pytest -q`: **291 passed, 8 paid-live tests skipped**.
- Docker isolation: **16/16**; real-sandbox end-to-end: **2/2**.
- `.venv/bin/python -m datasets.generate --check`: all four projects byte-reproducible.

## Not reviewed

- Real Bedrock/model behavior or actual phrasing distributions.
- Paid-live tests, pricing and live ledgers.
- Empirical ceiling effects and statistical validity of future results.
- Independent Docker execution; the reviewer relied on the lead's recorded verification.
- Unchanged contracts, routing/XAI and Bedrock infrastructure outside the T1 diff.
