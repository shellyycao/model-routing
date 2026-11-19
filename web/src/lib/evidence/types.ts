/**
 * Evidence vocabulary shared by the auditor, evidence panels and (later) the
 * chat copilot. Statuses follow the M7 handoff exactly.
 */

export const EVIDENCE_STATUSES = ["Directly tested", "Partially supported", "Unverified"] as const;
export type EvidenceStatus = (typeof EVIDENCE_STATUSES)[number];

/** What kind of number a value is. Never mix these in one figure. */
export type ResultKind = "measured" | "prediction" | "retrospective-oracle" | "post-hoc" | "insufficient-evidence";

export const RESULT_KIND_LABELS: Record<ResultKind, string> = {
  measured: "Measured outcome",
  prediction: "Prediction (not executed)",
  "retrospective-oracle": "Retrospective oracle (not deployable)",
  "post-hoc": "Post-hoc analysis",
  "insufficient-evidence": "Insufficient evidence",
};

/** Pointer from a displayed number back to its saved record. */
export interface EvidenceRef {
  sourcePath: string; // repo-relative, e.g. results/processed/...
  field: string; // JSON path inside the source
  version: string; // analysis_version / frozen tag
  sha256?: string;
}

export interface EvidenceRecommendation {
  id: string;
  change: string;
  why: string;
  evidence: EvidenceRef[];
  expectedBenefit: string;
  uncertainty: string;
  status: EvidenceStatus;
  kind: ResultKind;
}

// ---------------------------------------------------------------------------
// Shape of web/public/evidence/summary.json (written by scripts/build-evidence.mjs)
// ---------------------------------------------------------------------------

export interface SourceInfo {
  path: string;
  sha256: string;
  analysisVersion: string;
  analysisDate?: string;
  frozenTag?: string;
  mode?: string;
}

export interface PriceMatchedCell {
  task: string;
  taskLabel: string;
  modelAlias: string;
  modelLabel: string;
  primaryMetric: string;
  primaryMean: number;
  analyzedDenominator: number;
  scheduled: number;
  operationalRate: number;
  knownResponseCostUsd: number;
  ledgerAttributedCostUsd: number;
  meanCostPerCallUsd: number;
  medianLatencyMs: number | null;
  field: string;
}

export interface WorkflowPathRow {
  pathId: string;
  stageModels: string[];
  nRuns: number;
  evidenceLabel: string;
  meanCostPerRunUsd: number | null;
  frozenV3: { nFeasible: number; nNonvoid: number };
  posthocV31: { nFeasible: number; nNonvoid: number };
  field: string;
}

export interface EvidenceSummary {
  generatedAt: string;
  generator: string;
  notice: string;
  priceMatchedV2: {
    source: SourceInfo;
    evidenceLabel: string;
    scope: string;
    caveats: string[];
    cells: PriceMatchedCell[];
    paretoByTask: Record<string, string[]>;
  };
  workflowPaths: {
    source: SourceInfo;
    evidenceLabel: string;
    stages: string[];
    aliases: Record<string, { name: string; inputPerMtok: number; outputPerMtok: number; retrieved: string }>;
    caveats: string[];
    overall: {
      nRuns: number;
      totalSpendUsd: number;
      frozenV3: { nFeasible: number; nNonvoid: number };
      posthocV31: { nFeasible: number; nNonvoid: number };
    };
    pooledPaths: WorkflowPathRow[];
  };
}
