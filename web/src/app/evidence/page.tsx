"use client";

import { EvidenceStatusBadge, ResultKindTag } from "@/components/evidence/Badges";
import { PriceMatchedTable, WorkflowPathsTable } from "@/components/evidence/EvidenceTables";
import { useEvidence } from "@/components/evidence/useEvidence";
import { fmtFrac, fmtUsd } from "@/lib/evidence/format";

export default function EvidencePage() {
  const { data, error } = useEvidence();
  return (
    <main className="min-h-[calc(100vh-4rem)] bg-[radial-gradient(ellipse_at_top_right,#30234753,transparent_60%)] px-5 py-12 sm:px-[max(5vw,24px)]">
      <div className="mx-auto max-w-[1100px]">
        <span className="eyebrow">READ-ONLY RESEARCH RESULTS</span>
        <h1 className="mb-3 mt-3 text-[clamp(32px,4vw,52px)] font-semibold tracking-tight">Saved evidence</h1>
        <p className="max-w-[760px] leading-relaxed text-muted">
          Every number on this page is copied from a committed results file, with its path, version and hash. Nothing here was produced by the website, and nothing here
          is a prediction for a workflow you design.
        </p>
        <div className="mt-5 flex flex-wrap items-center gap-2 text-xs text-muted">
          <span>Labels used across ModelFlow:</span>
          <ResultKindTag kind="measured" />
          <ResultKindTag kind="prediction" />
          <ResultKindTag kind="retrospective-oracle" />
          <ResultKindTag kind="post-hoc" />
          <ResultKindTag kind="insufficient-evidence" />
          <span className="ml-2">Status:</span>
          <EvidenceStatusBadge status="Directly tested" />
          <EvidenceStatusBadge status="Partially supported" />
          <EvidenceStatusBadge status="Unverified" />
        </div>

        {error && (
          <p role="alert" className="mt-8 text-danger">
            Evidence summary could not be loaded: {error}
          </p>
        )}
        {!data && !error && <p className="mt-8 text-soft">Loading…</p>}

        {data && (
          <div className="mt-10 space-y-14">
            <section aria-labelledby="pm-title">
              <h2 id="pm-title" className="mb-1 text-2xl font-semibold">
                Task benchmark: price-matched-v2
              </h2>
              <p className="mb-4 max-w-[760px] text-sm leading-relaxed text-muted">
                {data.priceMatchedV2.caveats.join(" ")} Per-task Pareto sets (quality vs. cost):{" "}
                {Object.entries(data.priceMatchedV2.paretoByTask)
                  .map(([t, a]) => `${t.toUpperCase()}: ${a.map((x) => data.priceMatchedV2.cells.find((c) => c.modelAlias === x)?.modelLabel ?? x).join(", ")}`)
                  .join(" · ")}
                .
              </p>
              <PriceMatchedTable data={data} />
            </section>

            <section aria-labelledby="wf-title">
              <h2 id="wf-title" className="mb-1 text-2xl font-semibold">
                Three-stage workflow: path feasibility and cost
              </h2>
              <p className="mb-4 max-w-[760px] text-sm leading-relaxed text-muted">
                {data.workflowPaths.evidenceLabel} Overall: {fmtFrac(data.workflowPaths.overall.frozenV3.nFeasible, data.workflowPaths.overall.frozenV3.nNonvoid)} feasible
                under frozen v3 and {fmtFrac(data.workflowPaths.overall.posthocV31.nFeasible, data.workflowPaths.overall.posthocV31.nNonvoid)} under v3.1, total spend{" "}
                {fmtUsd(data.workflowPaths.overall.totalSpendUsd)} across {data.workflowPaths.overall.nRuns} runs. Aliases:{" "}
                {Object.entries(data.workflowPaths.aliases)
                  .map(([k, v]) => `${k} = ${v.name}`)
                  .join(", ")}
                .
              </p>
              <WorkflowPathsTable data={data} />
            </section>

            <p className="text-xs text-soft">
              Summary generated {new Date(data.generatedAt).toISOString().slice(0, 10)} by {data.generator}. {data.notice}
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
