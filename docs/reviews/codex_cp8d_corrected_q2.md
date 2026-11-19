# Codex CP8d — Corrected Q2 View

## Outputs

Added `experiments/analyze_corrected_q2.py`, machine-readable
`results/processed/corrected_q2.json`, rendered `results/reports/corrected_q2.md`, and six offline
regression tests. `docs/FINAL_REPORT.md` now contains the requested corrected-view section, revised
conclusions 1 and 9, two verification entries, and the frozen-hash reproducibility limitation.

## Main Results

In the 108-cell main grids, original-group v3 feasibility is 17 frozen versus 25 corrected and
v3.1 is 21 versus 30; price-matched v3 is 41 versus 52 and v3.1 is 53 versus 70. Corrected v3
single/cross counts are 2/12 versus 23/96 in the original group and 6/12 versus 46/96 in the second
group. Across all 156 effective cells, corrected cost per feasible completion is $0.2199/$0.1650
(v3/v3.1) for the original group and $0.3168/$0.2440 for the price-matched group, after adding all
continuation spend to the original attempted-run spend.

## Integrity and Scope

The audit reconciles 40 records, 40 distinct `continued_from`, 40 invocations, and the separate
ledger ($1.3973876, zero failed attempts, empty pending). No continuation is `void_infra`. All 11
cleaning recoveries are included; their downstream handoffs saw upstream status `failed`. One cell
belongs to both the cleaning and analysis-recovery evidence sets and is counted once as a workflow
cell. Frozen/raw inputs and Router outputs remain unchanged. Q1 rounding recoveries are not applied
to Q2, and possible changes to 22/50 and 31/64 are left as an explicit Router-validity open item.

## Verification

Targeted corrected-Q2 tests pass (`6 passed`), and the complete suite passes with `565 passed, 23
skipped` in 56.75 seconds. The frozen-hash verifier also reports all four manifests passing. No
model, Bedrock, Docker, or network operation was used.
