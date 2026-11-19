import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";
import type { EvidenceSummary } from "../src/lib/evidence/types";
import { MODEL_OPTIONS } from "../src/lib/models";

const web = resolve(__dirname, "..");
const repo = resolve(web, "..");
const summary = JSON.parse(readFileSync(join(web, "public/evidence/summary.json"), "utf8")) as EvidenceSummary;

function getPath(obj: unknown, path: string): unknown {
  return path
    .replace(/\[(\d+)\]/g, ".$1")
    .split(".")
    .reduce<unknown>((o, k) => (o as Record<string, unknown>)?.[k], obj);
}

describe("evidence summary", () => {
  it("records source paths, hashes and versions", () => {
    for (const block of [summary.priceMatchedV2, summary.workflowPaths]) {
      expect(block.source.path).toMatch(/^results\/processed\//);
      expect(block.source.sha256).toMatch(/^[0-9a-f]{64}$/);
      expect(block.source.analysisVersion).toBeTruthy();
    }
  });

  const pmPath = join(repo, summary.priceMatchedV2.source.path);
  const wcPath = join(repo, summary.workflowPaths.source.path);
  const haveSources = existsSync(pmPath) && existsSync(wcPath);

  it.skipIf(!haveSources)("matches the committed source files byte-for-byte (hash) and value-for-value", () => {
    const pmBuf = readFileSync(pmPath);
    const wcBuf = readFileSync(wcPath);
    expect(createHash("sha256").update(pmBuf).digest("hex")).toBe(summary.priceMatchedV2.source.sha256);
    expect(createHash("sha256").update(wcBuf).digest("hex")).toBe(summary.workflowPaths.source.sha256);
    const pm = JSON.parse(pmBuf.toString());
    for (const c of summary.priceMatchedV2.cells) {
      const src = getPath(pm, c.field) as Record<string, unknown>;
      expect(src.primary_mean).toBe(c.primaryMean);
      expect(src.analyzed_denominator).toBe(c.analyzedDenominator);
      expect(src.known_response_cost_usd).toBe(c.knownResponseCostUsd);
      expect(src.actual_execution_cost_usd).toBe(c.ledgerAttributedCostUsd);
      expect(src.model_alias).toBe(c.modelAlias);
    }
    const wc = JSON.parse(wcBuf.toString());
    for (const p of summary.workflowPaths.pooledPaths) {
      const src = getPath(wc, p.field) as Record<string, { n_feasible: number }> & { path_id: string; mean_cost_per_run_usd: number };
      expect(src.path_id).toBe(p.pathId);
      expect(src.frozen_v3.n_feasible).toBe(p.frozenV3.nFeasible);
      expect(src.posthoc_v31.n_feasible).toBe(p.posthocV31.nFeasible);
      expect(src.mean_cost_per_run_usd).toBe(p.meanCostPerRunUsd);
    }
  });

  it("only references models that exist in the dropdown (no Grok)", () => {
    const aliases = new Set(MODEL_OPTIONS.map((m) => m.priceMatchedAlias).filter(Boolean));
    for (const c of summary.priceMatchedV2.cells) expect(aliases.has(c.modelAlias as never)).toBe(true);
    expect(JSON.stringify(MODEL_OPTIONS).toLowerCase()).not.toContain("grok");
    expect(Object.keys(summary.workflowPaths.aliases).sort()).toEqual(["A", "B", "C"]);
  });
});
