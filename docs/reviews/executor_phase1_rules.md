# Executor Phase 1 hand-off: rules only (post-hoc / exploratory)

Files: `docs/ROUTER_RELABEL_RULES.md`, `docs/FAILURE_TAXONOMY_RULES.md`. No result was computed; no
accuracy or category count was aggregated. Only record formats, field names and code were read.

## Ambiguities found in the frozen aggregation

1. `corrected_q2.json` holds only the 108 repeat-0 rows per group, but the frozen validator
   aggregates every effective run (156 per group, all repeats). The re-scorer must rebuild per-run
   corrected rows (same logic as `analyze_corrected_q2.py`) and assert repeat-0 equality with the
   saved JSON.
2. Feasibility per path is a fraction over repeats, not a vote; agreement uses `>= 0.5`, direction
   uses a 1e-12 tolerance sign; a predicted tie matches only an actual tie.
3. The frozen validator does not exclude price-matched rerun/void records explicitly; it relies on
   `void_infra` exclusion. Corrected rules use resolved effective records; the reproduction gate
   will show whether the two agree.
4. "22/50, 31/64" is not named in the saved summary (`direction_or_agreement_rate` per quantity).
   Rules assume it is `direction_correct["feasible"]`, S2+S3 pooled; a reproduction gate stops the run if not.
5. S2 and S3 predictions of one project are not independent; Wilson/binomial values are optimistic.
   A 3-class sign match has no natural 0.5 chance level, so baselines (a)-(d) carry the argument.

## Decisions for the manager

- D1: `api_error` failure_type placed under infrastructure void (not a model-output failure). Move?
- D2: Baseline (c) primary uses frozen Part A statuses (what the router saw); corrected Part A is a sensitivity variant. Agree?
- D3: Residual review sample = 6 per (group, alias) stratum, max 36, seed `failure-taxonomy-residual-review-v1`. Size OK?
- D4: Replaced Docker-void originals are excluded from the failure units and audited separately. OK?
- D5: Blocked/not-run units are their own category with a non-exclusive `upstream_root_category` annotation.
