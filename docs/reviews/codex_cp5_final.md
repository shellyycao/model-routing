# Codex CP5 — final report

**Date:** 2026-11-19  
**Scope:** final research synthesis and deferred-note closure; offline only

`docs/FINAL_REPORT.md` now gives the user a verification-first account of the research question, architecture, experiment history, all result families, disclosures, and one-command checks. Every key result table points to a processed JSON path and field. The report distinguishes pre-registered, exploratory, and post-hoc evidence and avoids provider-level rankings.

## Deferred notes closed

- **CP2-1:** the defective frozen A3 score is explicitly audited (including values above 1), while strict invalid-as-zero nDCG@5 is the headline.
- **CP2-2:** the report states that only A1 A–B and B–C survive Holm; no A2 or strict-A3 pair does, with the A3 ceiling disclosed.
- **CP2-3:** C's low normalized A1 location recall is tied to 42 format mismatches and is not interpreted as weak localization skill.
- **CP4-1:** the price-matched summary states A1/A2 non-separation, the one Holm-significant A3 pair, and the observed quality/cost/latency trade-offs.
- **CP4-2:** Kimi's larger billed output is reported without speculating about hidden reasoning; reasoning-token coverage is zero.
- **CP4-3:** GLM's A1 location result is described as names/anchors formatting behavior, not localization ability.
- **CP4-4:** A3 exact repeat consistency (Sonnet 0.900, Kimi 0.967, GLM 0.633) is descriptive only; Kimi's missing temperature field is disclosed.
- **CP4b-1:** cheap early-failing paths are paired with feasibility denominators; C-C-C is shown as 0/12, never as an unqualified cheapest path.
- **CP4b-2:** `experiments/analyze_workflow_cost_posthoc.py` now computes a tested naive unit-price-ordering baseline: 30/32 agreement on the token-conversion subset and 42/50 overall, contrasted with 22/50 feasibility direction.
- **CP4b-3:** customer-churn A-A-A is shown side by side as 0/3 under v3 and 3/3 under v3.1 at identical spend.
- **CP4b-4:** the report discloses that the rules amendment and computation were committed together, so commit history alone does not prove the prescribed ordering.

No raw/frozen data was modified and no model or network call was made. The workflow-cost processed JSON/report were deterministically regenerated to include the new baseline and its regression test. The full offline suite passed: **501 passed, 23 skipped**.
