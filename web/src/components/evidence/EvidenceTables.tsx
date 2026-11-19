import { fmtFrac, fmtRate, fmtSeconds, fmtUsd, metricLabel } from "@/lib/evidence/format";
import type { EvidenceSummary } from "@/lib/evidence/types";
import { ResultKindTag, SourceLine } from "./Badges";

const th = "px-2 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-soft";
const td = "px-2 py-2 align-top tabular-nums";

export function PriceMatchedTable({ data, modelAlias, compact = false }: { data: EvidenceSummary; modelAlias?: string; compact?: boolean }) {
  const pm = data.priceMatchedV2;
  const cells = modelAlias ? pm.cells.filter((c) => c.modelAlias === modelAlias) : pm.cells;
  return (
    <figure className="min-w-0">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <ResultKindTag kind="measured" />
        <span className="text-xs text-muted">Price-matched-v2 task benchmark · {pm.evidenceLabel}</span>
      </div>
      <div className="overflow-x-auto rounded-lg border border-line">
        <table className="w-full text-[13px]">
          <caption className="sr-only">Measured task-level quality and cost per model (price-matched-v2)</caption>
          <thead className="bg-panel2">
            <tr>
              <th className={th} scope="col">Task</th>
              {!modelAlias && <th className={th} scope="col">Model</th>}
              <th className={th} scope="col">Primary quality</th>
              <th className={th} scope="col">n</th>
              {!compact && <th className={th} scope="col">Operational</th>}
              <th className={th} scope="col">Known-response spend</th>
              {!compact && <th className={th} scope="col">Ledger-attributed</th>}
              {!compact && <th className={th} scope="col">Median latency</th>}
            </tr>
          </thead>
          <tbody>
            {cells.map((c) => (
              <tr key={c.field} className="border-t border-line">
                <td className={td}>{c.taskLabel}</td>
                {!modelAlias && <td className={td}>{c.modelLabel}</td>}
                <td className={td}>
                  {fmtRate(c.primaryMean)} <span className="text-soft">{metricLabel(c.primaryMetric)}</span>
                </td>
                <td className={td}>{fmtFrac(c.analyzedDenominator, c.scheduled)}</td>
                {!compact && <td className={td}>{fmtRate(c.operationalRate)}</td>}
                <td className={td}>{fmtUsd(c.knownResponseCostUsd)}</td>
                {!compact && <td className={td}>{fmtUsd(c.ledgerAttributedCostUsd)}</td>}
                {!compact && <td className={td}>{fmtSeconds(c.medianLatencyMs)}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <figcaption>
        <SourceLine path={pm.source.path} field="main_analysis_void_excluded.cells" version={`${pm.source.analysisVersion} · ${pm.source.frozenTag}`} sha256={pm.source.sha256} />
        <p className="mt-1 text-[11px] text-soft">
          n = analyzed / scheduled calls. Spend columns are totals for each task × model cell: known-response spend uses returned token usage only; ledger-attributed spend adds
          conservative reservations for failed network attempts.
</p>
      </figcaption>
    </figure>
  );
}

export function WorkflowPathsTable({ data, alias }: { data: EvidenceSummary; alias?: string }) {
  const wp = data.workflowPaths;
  const rows = alias ? wp.pooledPaths.filter((p) => p.pathId.split("-").includes(alias)) : wp.pooledPaths;
  return (
    <figure className="min-w-0">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <ResultKindTag kind="measured" />
        <ResultKindTag kind="post-hoc" />
        <span className="text-xs text-muted">Three-stage workflow ({wp.stages.join(" → ")}), pooled across projects</span>
      </div>
      <div className="overflow-x-auto rounded-lg border border-line">
        <table className="w-full text-[13px]">
          <caption className="sr-only">Observed feasibility and cost of executed three-stage model paths</caption>
          <thead className="bg-panel2">
            <tr>
              <th className={th} scope="col">Path</th>
              <th className={th} scope="col">Feasible (frozen v3, primary)</th>
              <th className={th} scope="col">Feasible (v3.1, post-hoc)</th>
              <th className={th} scope="col">Mean cost / run</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.field} className="border-t border-line">
                <td className={td}>
                  <span className="font-mono">{p.pathId}</span>
                  <span className="block text-[11px] text-soft">{p.stageModels.join(" → ")}</span>
                </td>
                <td className={td}>{fmtFrac(p.frozenV3.nFeasible, p.frozenV3.nNonvoid)}</td>
                <td className={td}>{fmtFrac(p.posthocV31.nFeasible, p.posthocV31.nNonvoid)}</td>
                <td className={td}>{fmtUsd(p.meanCostPerRunUsd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <figcaption>
        <SourceLine path={wp.source.path} field="pooled_path_summaries" version={wp.source.analysisVersion} sha256={wp.source.sha256} />
        <ul className="mt-1 list-disc space-y-0.5 pl-4 text-[11px] text-soft">
          {wp.caveats.map((c) => (
            <li key={c}>{c}</li>
          ))}
        </ul>
      </figcaption>
    </figure>
  );
}
