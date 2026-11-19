import { RESULT_KIND_LABELS, type EvidenceStatus, type ResultKind } from "@/lib/evidence/types";

const STATUS_STYLE: Record<EvidenceStatus, string> = {
  "Directly tested": "border-teal/60 text-teal",
  "Partially supported": "border-warn/60 text-warn",
  Unverified: "border-line2 text-muted",
};

export function EvidenceStatusBadge({ status }: { status: EvidenceStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold ${STATUS_STYLE[status]}`} title={`Evidence status: ${status}`}>
      {status}
    </span>
  );
}

const KIND_STYLE: Record<ResultKind, string> = {
  measured: "bg-teal/15 text-teal",
  prediction: "bg-accent/15 text-accent",
  "retrospective-oracle": "bg-warn/15 text-warn",
  "post-hoc": "bg-warn/15 text-warn",
  "insufficient-evidence": "bg-[#2a2b3a] text-muted",
};

export function ResultKindTag({ kind }: { kind: ResultKind }) {
  return <span className={`inline-flex rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${KIND_STYLE[kind]}`}>{RESULT_KIND_LABELS[kind]}</span>;
}

export function SourceLine({ path, version, field, sha256 }: { path: string; version: string; field?: string; sha256?: string }) {
  return (
    <p className="mt-2 break-all font-mono text-[10.5px] leading-relaxed text-soft">
      {path}
      {field ? ` → ${field}` : ""} · {version}
      {sha256 ? ` · sha256 ${sha256.slice(0, 12)}…` : ""}
    </p>
  );
}
