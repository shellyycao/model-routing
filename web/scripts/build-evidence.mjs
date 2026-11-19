#!/usr/bin/env node
/**
 * Copy a small, read-only evidence summary from ../results/processed into
 * public/evidence/summary.json. Every number is copied from a saved file; the
 * script never computes new metrics (it only selects fields and renames keys).
 * Each block records its source path, sha256 and analysis version.
 *
 * Run from web/:  npm run evidence
 * The output is committed so that `npm run build` (and Vercel, which only sees
 * web/) does not need the research results directory.
 */
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = resolve(webRoot, "..");
const outFile = join(webRoot, "public", "evidence", "summary.json");

const PRICE_MATCHED = "results/processed/independent_v2/price_matched_v2_analysis.json";
const WORKFLOW_COST = "results/processed/workflow_cost_posthoc.json";

function load(rel) {
  const abs = join(repoRoot, rel);
  if (!existsSync(abs)) {
    console.error(`[evidence] missing ${rel}; leaving existing ${outFile} untouched.`);
    process.exit(existsSync(outFile) ? 0 : 1);
  }
  const buf = readFileSync(abs);
  return { data: JSON.parse(buf.toString("utf8")), sha256: createHash("sha256").update(buf).digest("hex") };
}

const req = (v, what) => {
  if (v === undefined) throw new Error(`[evidence] expected field missing: ${what}`);
  return v;
};

const TASK_LABELS = { a1: "A1 debugging", a2: "A2 structured extraction", a3: "A3 literature ranking" };
const STAGES = ["cleaning", "analysis", "reporting"];

// --- price-matched-v2 -------------------------------------------------------
const pm = load(PRICE_MATCHED);
const main = req(pm.data.main_analysis_void_excluded, "main_analysis_void_excluded");
const cells = req(main.cells, "main_analysis_void_excluded.cells").map((c, i) => ({
  task: c.task,
  taskLabel: TASK_LABELS[c.task] ?? c.task,
  modelAlias: c.model_alias,
  modelLabel: c.model_label,
  primaryMetric: c.primary_metric,
  primaryMean: req(c.primary_mean, "primary_mean"),
  analyzedDenominator: c.analyzed_denominator,
  scheduled: c.scheduled,
  operationalRate: c.operational_rate,
  knownResponseCostUsd: c.known_response_cost_usd,
  ledgerAttributedCostUsd: c.actual_execution_cost_usd,
  meanCostPerCallUsd: c.mean_cost_per_call_usd,
  medianLatencyMs: c.latency_ms?.median ?? null,
  field: `main_analysis_void_excluded.cells[${i}]`,
}));
const paretoByTask = Object.fromEntries(
  Object.entries(req(main.pareto_frontier_by_task, "pareto_frontier_by_task")).map(([t, v]) => [t, v.model_aliases]),
);

// --- workflow cost / feasibility (post-hoc) ----------------------------------
const wc = load(WORKFLOW_COST);
const prices = req(wc.data.prices, "prices");
const aliases = Object.fromEntries(
  Object.entries(prices).map(([k, p]) => [k, { name: p.name, inputPerMtok: p.input_per_mtok, outputPerMtok: p.output_per_mtok, retrieved: p.retrieved }]),
);
const pooled = req(wc.data.pooled_path_summaries, "pooled_path_summaries");
const pooledPaths = pooled
  .map((r, i) => ({ r, i }))
  .filter(({ r }) => r.project_id === null || r.project_id === undefined)
  .map(({ r, i }) => ({
    pathId: r.path_id,
    stageModels: r.path_id.split("-").map((a) => aliases[a]?.name ?? a),
    nRuns: r.n_runs,
    evidenceLabel: r.evidence_label,
    meanCostPerRunUsd: r.mean_cost_per_run_usd ?? null,
    frozenV3: { nFeasible: r.frozen_v3.n_feasible, nNonvoid: r.frozen_v3.n_nonvoid },
    posthocV31: { nFeasible: r.posthoc_v31.n_feasible, nNonvoid: r.posthoc_v31.n_nonvoid },
    field: `pooled_path_summaries[${i}]`,
  }));
const ov = req(wc.data.overall, "overall");

const summary = {
  generatedAt: new Date().toISOString(),
  generator: "web/scripts/build-evidence.mjs",
  notice:
    "Read-only copy of saved research results. Task-level and three-stage-workflow evidence only; it does not transfer to arbitrary user workflows.",
  priceMatchedV2: {
    source: {
      path: PRICE_MATCHED,
      sha256: pm.sha256,
      analysisVersion: pm.data.analysis_version,
      analysisDate: pm.data.analysis_date,
      frozenTag: pm.data.frozen_tag,
    },
    evidenceLabel: "Pre-registered protocol; measured outcomes (void-infrastructure cells excluded, denominators shown).",
    scope: pm.data.scope?.account_constraint ?? "",
    caveats: [
      "Task benchmark (A1–A3), not end-to-end workflow evidence.",
      "Three specific models callable on one account; no vendor-wide claim.",
      "Ledger-attributed spend includes conservative reservations for failed network attempts.",
    ],
    cells,
    paretoByTask,
  },
  workflowPaths: {
    source: {
      path: WORKFLOW_COST,
      sha256: wc.sha256,
      analysisVersion: wc.data.analysis_version,
      analysisDate: wc.data.analysis_date,
      mode: wc.data.mode,
    },
    evidenceLabel: "Post-hoc cost analysis of executed runs; frozen v3 feasibility is primary, v3.1 is a secondary post-hoc view.",
    stages: STAGES,
    aliases,
    caveats: [
      "Only the fixed three-stage cleaning → analysis → reporting workflow was executed. Do not extrapolate to other DAGs.",
      ...(wc.data.limitations ?? []),
    ],
    overall: {
      nRuns: ov.n_runs,
      totalSpendUsd: ov.total_spend_usd,
      frozenV3: { nFeasible: ov.frozen_v3.n_feasible, nNonvoid: ov.frozen_v3.n_nonvoid },
      posthocV31: { nFeasible: ov.posthoc_v31.n_feasible, nNonvoid: ov.posthoc_v31.n_nonvoid },
    },
    pooledPaths,
  },
};

mkdirSync(dirname(outFile), { recursive: true });
writeFileSync(outFile, JSON.stringify(summary, null, 2) + "\n");
console.log(`[evidence] wrote ${outFile}: ${cells.length} price-matched cells, ${pooledPaths.length} pooled workflow paths.`);
