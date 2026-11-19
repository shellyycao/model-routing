# Codex CP7a — price-matched workflow plan

## Task 1 correction

The price-matched-v2 analyzer now computes returned-output composition directly from immutable
records and `response.txt` artifacts. Kimi has returned `reasoning_chars` coverage of 90/90 in each
task; median reasoning characters are 5,583.5 / 1,108.5 / 27,467 and final-answer characters are
1,180.5 / 209 / 4,385 for A1/A2/A3. Sonnet final-answer medians are 1,036 / 210 / 4,159. The JSON
labels four characters/token as an approximation: for A3, component medians imply about 7,963
tokens versus 7,718 median billed output tokens. `FINAL_REPORT.md` and
`price_matched_v2_benchmark.md` now state that Kimi's extra billed output mainly consists of its
returned reasoning text, while Bedrock still exposes no separate reasoning-token count. A regression
test locks coverage, medians, approximation labeling, and final-answer comparability. The derived
price-matched analysis and protocol-manifest analysis hash were regenerated; the paid scientific
protocol, tag, raw records, and results are unchanged.

## CP7a protocol preparation

`docs/PRICE_MATCHED_WORKFLOW_PLAN.md`, the plan-by-default
`experiments/run_price_matched_workflow.py`, and
`configs/analysis_price_matched_workflow_v3.yaml` prepare the second-model-set Parts A/B/C
replication. The design fixes 9 structural pilot calls and 504 potential main calls (36 Part A, 324
main-grid stage calls, and 144 repeat stage calls), retrains LOPO routing only on the new records,
and keeps the prospective and post-hoc cost-aware outputs separate. Kimi omits temperature; Sonnet
and GLM send zero. Sandbox lookup/build/lease failures are classified as `sandbox_unavailable` /
`void_infra`, never model failures.

The user choices remain open. At maxTokens 4,096, combined pilot+main budget is $21.962 realistic
and $198.648 static worst case; at 16,384 it is $42.817 realistic and $572.437 static worst case.
The document states all token/retry assumptions and comparability trade-offs without selecting an
option or cap. Pilot and main each require separate future approval, an exact frozen tag, matching
hashes, and a positive hard cap before the runner can construct paid clients.

## Verification and stop point

Full offline suite: **513 passed, 23 skipped**. The default runner prints a plan only; both paid
flags refuse because no approval manifest exists. No model/network call was made, no CP7 paid raw
record or ledger was created, and the work stops before the user decisions and compatibility pilot.
