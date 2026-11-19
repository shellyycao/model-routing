# CP4b Results Review: workflow cost analysis

**Verdict: PASS WITH NOTES.** The notes go into CP5.

## Checked
- **Tests:** the full suite passes, 500 passed / 23 skipped.
- **Integrity:** 156 records → 339 billable calls; the ledgers reconcile exactly.
- **Labels and denominators:**
  - v3 is primary and v3.1 is secondary, side by side.
  - `not estimable`, `single-run evidence`, and the pilot-exposure disclosure are present.
  - The Router dollar view is labelled a post-hoc token-prediction conversion.
- **Frozen artifacts unchanged.** The trace and counterfactual hash chains still validate.

## Notes for CP5
1. **Cheap paths are often cheap because they fail early.**
   - Paths starting with Nova cleaning cost about $0.007/run, because the downstream stages were blocked
     and never incurred cost.
   - Mean cost per run must always be read together with feasibility. Cost per feasible completion is
     the decision-relevant figure.
   - State this plainly.
2. **The cost-counterfactual direction (29/32) needs a baseline.**
   - Model prices differ by up to about 27× (C ≪ B ≪ A). A naive rule like "swapping to a cheaper-priced
     model lowers cost" may predict direction almost as well.
   - Report that baseline's agreement next to 29/32, or describe the result as largely implied by price
     ordering.
   - Contrast it with feasibility direction (44%): cost direction is easy, feasibility direction is the
     hard and decision-relevant part.
3. **The validator choice changes conclusions.** For example, customer_churn A-A-A is 0/3 under v3 and
   3/3 under v3.1. Use it as a concrete illustration of validator sensitivity.
4. **Timing:** the rules amendment was uncommitted when the computation ran (the Codex sandbox cannot
   commit). Codex states the amendment was written first. Disclose this as self-reported ordering.
