# Tier-Matched Model Comparison — SUPERSEDED

**Status:** SUPERSEDED on 2026-11-18 by `docs/PRICE_MATCHED_V2_PLAN.md`. Do not freeze or execute this
protocol. Four of its five conditional selections were unavailable on the account, and the user could
not enable them. This file is retained only as an audit trail; no paid calls are authorized by it.
**Drafted:** 2026-11-18, by Claude. Claude is a party with an interest (a Claude model is evaluated), so the
model-selection step below is rule-based and must be executed and frozen by Codex, then reviewed by Claude.

## Why

The three current models are not matched:

| Model | Output $/M | Generation | Notes |
|---|---:|---|---|
| Claude Sonnet 4.6 | 16.50 | not the newest Claude (Sonnet 5 / 5.5 are ACTIVE) | |
| Amazon Nova Pro v1 | 3.20 | oldest of the three (Nova 2 Lite is ACTIVE) | |
| gpt-oss-120b | 0.60 | open-weight reasoning model | reasoning tokens count toward the 4,096-token cap |

That is a roughly 27× output-price spread and a mixed set of generations. Existing results support
claims about *these three versions at this budget*, not vendor comparisons. This run adds same-tier
comparisons.

## Research questions (pre-register before running)

- **RQ1:** Within a price tier, do the per-task differences seen in v2 persist across vendors?
- **RQ2:** Within each vendor, how much does the tier change task performance? Is the cheaper tier "good enough" on any task?
- **RQ3:** Does a larger output budget remove the reasoning-model truncation and format failures seen for gpt-oss-120b? (Anchor rerun.)

## Model selection: a rule, not a hand-pick

1. **Candidate pool:** text-in/text-out models from Anthropic, OpenAI and Amazon with lifecycle ACTIVE in
   `results/raw/model_discovery_2026-11-18.json`, callable on demand or through a US system inference
   profile, and passing a one-call access probe.
2. **Prices:** standard on-demand us-east-1 prices from the official AWS Price List JSON (same procedure as
   `configs/models.yaml`). Record the source URL and the retrieval date.
3. **Tiers by blended price** = (3 × input + 1 × output) / 4 per M tokens. Fix the bands *before* looking at
   the price list output. Proposal:
   - **Low tier:** blended ≤ $1.50
   - **High tier:** blended $3.00–$10.00 (vendor workhorse, excluding top-priced flagships)
4. **Within each vendor × tier:** pick the newest ACTIVE model, by vendor version number, whose blended price
   falls in the band. Exclude safeguard, speech and vision-only variants.
5. **If a vendor has no model in a band, leave the cell empty.** Do not substitute a near miss. The gap is
   itself a reported finding. For example, no Nova 2 Pro appears in the discovery file, so Amazon may have no
   high-tier entry.
6. Write the full price table, the band each candidate falls in and the selected IDs into the protocol before
   any evaluation call.

**Expected shape:** up to 2 tiers × 3 vendors = at most 6 new models. The offline application of the
rule produced five conditional selections and one empty cell; see the CP3 record below.

## Benchmark

- Reuse the frozen `datasets/independent_v2` cases (30 × A1/A2/A3), unchanged. This keeps comparability
  with the 270 existing cells and avoids new benchmark authorship.
- **Known ceiling risk:** in v2, A2 already has two models at 100% and A3 valid-only nDCG ≥ 0.99. High-tier
  models will likely saturate them. Pre-register that the high-tier comparison is expected to be informative
  mainly on A1 hard cases and on operational reliability. A harder dataset would be a separate, separately
  frozen project. Do not add cases after seeing results.

## Scorer: dependency on the post-hoc work

Run the new models with a corrected scorer **v2.2** that is frozen *before* this run. v2.2 covers:
- A1 location matching
- A3 duplicate-ID handling
- A3 grounding matching

The prospective v2.2 definitions are mechanical translations of the committed rules:
- A1 uses normalized function/line matching for `bug_location_recall`; functional scoring is unchanged.
- A3 nDCG and grade-2 recall use `deduplicated_first5`, while duplicate/unknown IDs still fail the
  operational-validity check.
- A3 `evidence_grounding` uses R2 (canonical attribute plus any cited document supports); R1
  (all citations support) remains a reported secondary diagnostic.

Its rules come from `docs/POSTHOC_V2_RULES.md` (see `POSTHOC_V2_ANALYSIS_BRIEF.md`).
- Rescore the existing 270 cells with v2.2 as well, and report frozen-v2 and v2.2 side by side.
- **Order:** post-hoc rules committed → Claude review → v2.2 frozen → tier-matched protocol frozen → run.

## Generation settings (identical for all, documented deviations only)

- Temperature 0.
- `maxTokens` large enough that budget is not the bottleneck. Proposal: 16,384 for every model.
- For reasoning-capable models, use the vendor default reasoning setting. Record reasoning tokens separately.
  Do not tune per model.
- A1/A2 use the unchanged `prompts/independent_v2` prompts. A3 alone uses the new
  `prompts/independent_v2_2/a3_literature.txt`, which enumerates the seven allowed attributes.
- **Anchor rerun:** gpt-oss-120b on all 90 cases at the new budget. This answers RQ3, and its difference
  from v2 isolates the budget effect from the model effect.

## Repeats and statistics

- **3 repeats per model × case.** v3 workflow runs flipped at temperature 0, so single runs are not enough.
- **Pre-registered analyses:**
  - **Within tier, across vendors:** paired comparisons on the same cases, using case-level majority or mean
    over the repeats.
  - **Tests:**
    - exact McNemar for binary primaries;
    - paired bootstrap of the mean difference for A3;
    - Holm correction within each tier × task family.
  - **Within vendor, across tiers:** the same tests.
  - **Report alongside:**
    - cost per correct answer;
    - median latency;
    - truncation and format-failure rates.
- **No composite score** across A1, A2 and A3.

## Budget (CP3 computation; not approved for execution)

- **Planned calls:** 5 conditional selections + 3 anchors, each on 90 cases × 3 repeats = **2,160
  logical calls**.
- **Probe + retry reservation:** reserve up to two probe calls per model (temperature 0, then the
  conditional no-temperature fallback) and five attempts per logical call = **2,176 logical-call
  reservations** and at most **10,880 API attempts**.
- **Worst case:** the conservative byte-based input upper bound plus 16,384 output tokens for every
  reserved attempt costs **$1,076.81** at the verified snapshot prices. This does **not** fit $100.
- **Proposed cut (requires user and manager approval):** run only the three selected low-tier models,
  preserving all 90 cases, three repeats, 16,384 tokens and five-attempt reservations. Worst case is
  **$88.69**, including those three models' probe reservations. This preserves low-tier RQ1 but
  defers both high-tier models, all anchors, RQ2, RQ3 and
  separation of protocol effects. The cap is not raised and the cut is not applied at CP3.

## Bias controls

- Model selection is fully determined by the rule plus the official price list. Selection is done and frozen by
  Codex. Claude reviews the frozen table but does not choose models.
- Analysis uses blinded aliases until all numbers are final.
- **Disclose:**
  - **Prompts and benchmark:** these were developed with Claude- and Codex-family agents in the loop.
  - **Evaluated models:** both Anthropic and OpenAI models are being evaluated.

## User decisions (recorded 2026-11-18)

1. **Tiers:** low and high tiers, up to 6 new models, using the bands above.
2. **Repeats:** 3 per model × case.
3. **Hard dollar cap:** $100, covering everything, including the worst-case retry reservations.
4. **A3 prompt:** add the attribute vocabulary (`dataset, first_author, method, metric, topic, value, year`)
   to the A3 prompt and to the claim schema as an enum.
   - The A1 and A2 prompts stay unchanged.
   - A3 grounding from this run is not comparable with v2 grounding. A3 ranking remains comparable,
     subject to the anchors below.
5. **Dataset:** reuse the frozen v2 cases despite the ceiling, as described above.

## Manager decision (Claude, 2026-11-18)

- **Anchors widened:** rerun all **three original models** (not only gpt-oss-120b) on all 90 cases × 3
  repeats under the new budget and the new A3 prompt.
- **Why:** the new run changes the budget, the A3 prompt and the repeat count at once. Anchors are the
  only way to separate those protocol effects from model effects.
- **Cost:** v2 cost about $1.12 for 270 calls, so the extra cost is small.
- **Total calls:** up to (6 + 3) × 90 × 3 = **2,430 calls**.

## Selection-rule clarifications (Claude, 2026-11-18; written after the price snapshots were downloaded)

These remove ambiguities that the rule must resolve mechanically.
**Disclosure:** Claude had seen the price list when it wrote them.

1. **Price used:** the **regional (non-global) standard on-demand** us-east-1 input and output prices, the
   same basis as `configs/models.yaml`. Ignore global, batch, cache, priority, flex, latency-optimized,
   custom-model and provisioned SKUs.
2. **Eligibility:** a model must be **both**
   - ACTIVE in `model_discovery_2026-11-18.json`, **and**
   - priced in the snapshots.

   A model in only one of the two is ineligible. Record such models in the table.
3. **"Newest":** the highest version number within the vendor's naming. **Tie-break:** the lower blended
   price. This replaces the informal "excluding top-priced flagships"; the band's upper bound already
   does that job.
4. A model whose blended price falls between the bands (> $1.50 and < $3.00) is in no tier.

## Pricing input

Official AWS Price List JSON snapshots are downloaded into `results/raw/pricing/` before selection.
- The download is mechanical: Claude fetched the public files, and there is no judgment in it.
- Codex applies the rule offline to those snapshots and records their hashes.

## CP3 offline selection record

The normative full 55-row candidate table is
`results/processed/independent_v2/tier_matched_selection.json`. It records every union member from
the target-provider discovery rows and standard regional price rows, including input/output price,
blended price, band, lifecycle/call path, eligibility and an exclusion or pending reason. Reproduce it
offline with:

```bash
.venv/bin/python -m experiments.select_tier_matched_models --check --markdown
```

The selection is conditional because the required access probes have not been run:

| Vendor | Tier | Base model | Callable ID | Price (in/out/blended $/M) | CP3 status |
|---|---|---|---|---:|---|
| Amazon | low | `amazon.nova-2-lite-v1:0` | `us.amazon.nova-2-lite-v1:0` | 0.33 / 2.75 / 0.935 | selected pending probe |
| Amazon | high | — | — | — | empty; no offline-eligible model |
| Anthropic | low | `anthropic.claude-haiku-5-5` | `us.anthropic.claude-haiku-5-5` | 0.11 / 0.55 / 0.22 | selected pending probe |
| Anthropic | high | `anthropic.claude-sonnet-5-5` | `us.anthropic.claude-sonnet-5-5` | 2.20 / 11.00 / 4.40 | selected pending probe |
| OpenAI | low | `openai.gpt-6-luna` | `us.openai.gpt-6-luna` | 0.11 / 0.55 / 0.22 | selected pending probe |
| OpenAI | high | `openai.gpt-6.1-sol` | `us.openai.gpt-6.1-sol` | 2.20 / 11.00 / 4.40 | selected pending probe |

No near miss fills Amazon-high. `Nova Premier` is priced in the snapshot but absent from the
foundation-model discovery rows, while no discovered Nova high-tier model has a complete eligible
price pair.

### Immutable local price inputs

| Snapshot | Official source | Retrieved | SHA-256 |
|---|---|---|---|
| `AmazonBedrockFoundationModels_us-east-1_2026-11-18.json` | `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/20261109224312/us-east-1/index.json` | 2026-11-18 | `c7b653975fc04981d8dc936e8a571af662a6b1cc3eff8e2f790d9925349c71c2` |
| `AmazonBedrock_us-east-1_2026-11-18.json` | `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/20261111013037/us-east-1/index.json` | 2026-11-18 | `f1ac6a175fb27b3ad80d2c5d8970be8c2e5f957906349e52d15ec11d43e97896` |

Discovery SHA-256: `16ae14b5bc69e6a82808b185b7dd631c678f3ab83d94eb833043904f53939263`.
The script rejects global, batch, cache, priority, flex, latency-optimized, custom, provisioned,
long-context and duplicate Mantle SKUs.

## Generation/API parameter record

All eight planned models use `maxTokens=16384` and vendor-default reasoning (no reasoning-control
field). The three anchors previously accepted `temperature=0` in v2. The five selected models remain
`pending_access_probe`; their primary probe sends temperature 0, and a fallback without temperature is
allowed only after a parameter-validation error. Omitting temperature is a documented API deviation,
not model-specific tuning.

| Model group | Models | Temperature at CP3 | Reasoning parameter |
|---|---|---|---|
| Conditional selections | five IDs in the table above | pending probe; send 0 if supported, otherwise omit | omitted (vendor default) |
| Anchors | Claude Sonnet 4.6, Nova Pro v1, gpt-oss-120b | prior v2 calls verified 0 | omitted (vendor default) |

The plan lists, but CP3 does not execute, one `Reply with exactly: OK` Converse probe per planned
callable ID using `maxTokens=16384`, temperature 0 and no reasoning-control field. If and only if that
call returns a temperature-parameter validation error, one fallback probe omits temperature. A failed
access probe empties that selected slot; it never triggers a near-miss substitution. Exact request
skeletons and statuses are in `results/processed/independent_v2/tier_matched_plan.json`.

## CP3 protocol artifacts (not a freeze)

- Additive scorer: `src/independent/v2_2.py`; frozen `src/independent/v2.py` is unchanged.
- New A3 prompt: `prompts/independent_v2_2/a3_literature.txt`; A1/A2 retain hashes
  `c9fa8de2…` and `e383be6d…` respectively.
- Plan-by-default runner: `experiments/run_tier_matched_v2_2.py`. `--execute` is deliberately locked at
  CP3 until probes, a budget decision, manager review, manifest freeze and tag are complete.
- Offline plan: `results/processed/independent_v2/tier_matched_plan.json`.
- CP3 hash manifest: `results/processed/independent_v2/tier_matched_protocol_manifest.json`.

The requested eight-model design is not freezeable under the final $100 decision. The proposed
low-tier-only cut is not silently adopted; it is an explicit CP3 decision request.
