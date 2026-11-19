"use client";

import Link from "next/link";
import { CUSTOM, UNASSIGNED, modelLabel, modelOption } from "@/lib/models";
import { TASK_TYPE_LABELS, type WorkflowNode } from "@/lib/workflow/schema";
import { EvidenceStatusBadge, ResultKindTag } from "./Badges";
import { PriceMatchedTable, WorkflowPathsTable } from "./EvidenceTables";
import { useEvidence } from "./useEvidence";

/**
 * "Why this model?" for the selected stage. Shows only saved, measured
 * results for the assigned model, and states plainly that they do not verify
 * the model *for this stage* (status: Unverified).
 */
export function EvidencePanel({ node }: { node: WorkflowNode | null }) {
  const { data, error } = useEvidence();

  if (!node) {
    return (
      <div className="space-y-4 text-sm leading-relaxed text-muted">
        <p>Select a stage to see what saved evidence exists for its assigned model.</p>
        <p>
          Evidence comes from this project&apos;s saved experiments only: a task benchmark (debugging, extraction, literature ranking) and a fixed three-stage data workflow. Neither
          establishes how a model will perform in <em>your</em> workflow.
        </p>
        <Link href="/evidence" className="btn-text text-sm">
          Browse all saved evidence →
        </Link>
      </div>
    );
  }

  const opt = modelOption(node.model);
  const header = (
    <div className="mb-4">
      <p className="text-xs text-soft">Why this model?</p>
      <p className="text-base font-semibold">{modelLabel(node.model, node.customModelLabel)}</p>
      <p className="text-xs text-muted">
        for “{node.name}” · {TASK_TYPE_LABELS[node.taskType]}
      </p>
      <div className="mt-2 flex items-center gap-2">
        <EvidenceStatusBadge status="Unverified" />
        <span className="text-[11px] text-soft">for this stage</span>
      </div>
    </div>
  );

  if (node.model === UNASSIGNED || node.model === CUSTOM || !opt?.tested) {
    return (
      <div>
        {header}
        <ResultKindTag kind="insufficient-evidence" />
        <p className="mt-2 text-sm leading-relaxed text-muted">
          {node.model === UNASSIGNED ? "No model is assigned yet." : "There are no saved results for this model in this project."} Nothing is estimated for it.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {header}
      <div className="text-sm leading-relaxed text-muted">
        <p className="mb-1">Tested in:</p>
        <ul className="list-disc pl-5">
          {opt.testedIn.map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ul>
        <p className="mt-2 text-xs text-soft">
          These results are for specific benchmark tasks or the fixed three-stage workflow. They are shown for context and are not a prediction for this stage.
        </p>
      </div>
      {error && <p className="text-sm text-danger">Evidence could not be loaded: {error}</p>}
      {!data && !error && <p className="text-sm text-soft">Loading saved evidence…</p>}
      {data && opt.priceMatchedAlias && <PriceMatchedTable data={data} modelAlias={opt.priceMatchedAlias} compact />}
      {data && opt.workflowAlias && <WorkflowPathsTable data={data} alias={opt.workflowAlias} />}
      <Link href="/evidence" className="btn-text inline-block text-sm">
        All saved evidence →
      </Link>
    </div>
  );
}
