"use client";

import { EvidenceStatusBadge } from "@/components/evidence/Badges";
import type { AuditReport, FindingSeverity } from "@/lib/auditor/audit";

const SEV: Record<FindingSeverity, { label: string; cls: string }> = {
  error: { label: "Error", cls: "text-danger border-danger/50" },
  warning: { label: "Warning", cls: "text-warn border-warn/50" },
  info: { label: "Note", cls: "text-muted border-line2" },
};

export function AuditPanel({ report, onFocusNode }: { report: AuditReport; onFocusNode: (id: string) => void }) {
  return (
    <div className="space-y-7">
      <section aria-labelledby="structural-title">
        <h3 id="structural-title" className="text-sm font-bold">
          Structural checks
        </h3>
        <p className="mb-3 mt-1 text-xs text-soft">
          Deterministic graph rules · {report.counts.error} error(s), {report.counts.warning} warning(s), {report.counts.info} note(s)
        </p>
        {report.structural.length === 0 ? (
          <p className="text-sm text-teal">No structural problems found.</p>
        ) : (
          <ul className="space-y-2.5">
            {report.structural.map((f, i) => (
              <li key={`${f.code}-${i}`} className="rounded-lg border border-line bg-panel2/60 p-3">
                <div className="flex items-center gap-2">
                  <span className={`rounded-full border px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${SEV[f.severity].cls}`}>{SEV[f.severity].label}</span>
                  <span className="text-sm font-semibold">{f.title}</span>
                </div>
                <p className="mt-1.5 text-[13px] leading-relaxed text-muted">{f.detail}</p>
                {f.nodeIds.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {f.nodeIds.slice(0, 6).map((id) => (
                      <button key={id} type="button" className="btn-text text-xs" onClick={() => onFocusNode(id)}>
                        Show {id} →
                      </button>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="evidence-rec-title" className="border-t border-line pt-5">
        <div className="flex items-center justify-between gap-2">
          <h3 id="evidence-rec-title" className="text-sm font-bold">
            Evidence-based recommendations
          </h3>
          <EvidenceStatusBadge status="Unverified" />
        </div>
        {report.evidence.length === 0 ? (
          <p className="mt-2 text-[13px] leading-relaxed text-muted">{report.evidenceNotice}</p>
        ) : null}
      </section>
    </div>
  );
}
