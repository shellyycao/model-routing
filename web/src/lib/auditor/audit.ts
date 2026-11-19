/**
 * Auditor MVP: deterministic structural checks only.
 *
 * Evidence-based performance recommendations are a separate list that is
 * intentionally empty until real evidence retrieval is wired (M7.4). This
 * module never estimates quality or cost.
 */
import { CUSTOM, UNASSIGNED, isKnownModel } from "../models";
import { ancestors, incoming, nodesOnCycles, outgoing } from "../workflow/graph";
import { NON_MODEL_TASK_TYPES, type Workflow } from "../workflow/schema";
import { validateWorkflow } from "../workflow/validate";
import type { EvidenceRecommendation } from "../evidence/types";

export type FindingSeverity = "error" | "warning" | "info";

export type FindingCode =
  | "no-entry"
  | "no-terminal"
  | "multiple-entries"
  | "disconnected"
  | "cycle"
  | "invalid-structure"
  | "unassigned-model"
  | "custom-model-unverified"
  | "unknown-model"
  | "fan-in-merge-unspecified"
  | "io-unsatisfied-input"
  | "io-no-overlap"
  | "possible-redundancy";

export interface StructuralFinding {
  code: FindingCode;
  severity: FindingSeverity;
  title: string;
  detail: string;
  nodeIds: string[];
  /** Always "deterministic": these come from graph rules, not evidence. */
  basis: "deterministic";
}

export interface AuditReport {
  structural: StructuralFinding[];
  /** Evidence-based recommendations. Empty until evidence retrieval is wired. */
  evidence: EvidenceRecommendation[];
  evidenceNotice: string;
  counts: Record<FindingSeverity, number>;
}

export const EVIDENCE_NOTICE =
  "No evidence-based recommendations yet. Performance suggestions will appear here only when they can be linked to saved benchmark records; until then every model choice is Unverified for your workflow.";

const norm = (s: string) => s.trim().toLowerCase();

export function auditWorkflow(w: Workflow): AuditReport {
  const f: StructuralFinding[] = [];
  const add = (x: Omit<StructuralFinding, "basis">) => f.push({ ...x, basis: "deterministic" });
  const name = (id: string) => w.nodes.find((n) => n.id === id)?.name ?? id;
  const ids = w.nodes.map((n) => n.id);

  // Structural validity (duplicate ids, dangling edges, self loops)
  const v = validateWorkflow(w);
  for (const issue of v.issues) {
    if (issue.code === "cycle" || issue.code === "disconnected" || issue.code === "empty") continue;
    add({ code: "invalid-structure", severity: issue.severity, title: "Invalid structure", detail: issue.message, nodeIds: issue.nodeIds ?? [] });
  }

  if (w.nodes.length === 0) {
    return { structural: f, evidence: [], evidenceNotice: EVIDENCE_NOTICE, counts: countBy(f) };
  }

  const validEdges = w.edges.filter((e) => ids.includes(e.source) && ids.includes(e.target) && e.source !== e.target);

  // Entry / terminal
  const entries = ids.filter((id) => incoming(id, validEdges).length === 0);
  const terminals = ids.filter((id) => outgoing(id, validEdges).length === 0);
  if (entries.length === 0) add({ code: "no-entry", severity: "error", title: "No entry stage", detail: "Every stage has an upstream dependency, so nothing can start.", nodeIds: [] });
  if (terminals.length === 0) add({ code: "no-terminal", severity: "error", title: "No terminal stage", detail: "Every stage feeds another stage, so the workflow has no final output.", nodeIds: [] });
  if (entries.length > 1 && w.nodes.length > 1) {
    add({
      code: "multiple-entries",
      severity: "info",
      title: `${entries.length} entry stages`,
      detail: `Stages with no inputs: ${entries.map(name).join(", ")}. Fine if each reads its own source; otherwise connect them.`,
      nodeIds: entries,
    });
  }

  // Cycles
  const cyc = nodesOnCycles(ids, validEdges);
  if (cyc.length) add({ code: "cycle", severity: "error", title: "Cycle", detail: `These stages depend on each other in a loop: ${cyc.map(name).join(" → ")}.`, nodeIds: cyc });

  // Disconnected
  const disc = v.issues.find((i) => i.code === "disconnected");
  if (disc) {
    add({
      code: "disconnected",
      severity: "warning",
      title: "Disconnected stages",
      detail: `Not connected to the main workflow: ${(disc.nodeIds ?? []).map(name).join(", ")}.`,
      nodeIds: disc.nodeIds ?? [],
    });
  }

  // Models
  for (const n of w.nodes) {
    if (n.model === UNASSIGNED && !NON_MODEL_TASK_TYPES.has(n.taskType)) {
      add({ code: "unassigned-model", severity: "warning", title: "Unassigned model", detail: `"${n.name}" has no model assigned.`, nodeIds: [n.id] });
    } else if (n.model === CUSTOM) {
      add({
        code: "custom-model-unverified",
        severity: "info",
        title: "Custom model (unverified)",
        detail: `"${n.name}" uses ${n.customModelLabel?.trim() ? `"${n.customModelLabel.trim()}"` : "a custom model"}, which has no saved evidence in this project.`,
        nodeIds: [n.id],
      });
    } else if (!isKnownModel(n.model)) {
      add({ code: "unknown-model", severity: "warning", title: "Unknown model id", detail: `"${n.name}" references model id "${n.model}", which is not in the tested list.`, nodeIds: [n.id] });
    }
  }

  // Fan-in merge semantics
  for (const n of w.nodes) {
    const ins = incoming(n.id, validEdges);
    if (ins.length >= 2 && (!n.mergeStrategy || n.mergeStrategy === "unspecified")) {
      add({
        code: "fan-in-merge-unspecified",
        severity: "warning",
        title: "Fan-in without merge rule",
        detail: `"${n.name}" receives ${ins.length} inputs (${ins.map(name).join(", ")}) but does not say how to combine them (wait for all, first available, concatenate…).`,
        nodeIds: [n.id],
      });
    }
  }

  // Declared input/output contracts
  const byId = new Map(w.nodes.map((n) => [n.id, n]));
  for (const n of w.nodes) {
    if (!n.inputs.length) continue;
    const ups = [...ancestors(n.id, validEdges)].map((id) => byId.get(id)!).filter(Boolean);
    const declaringUps = ups.filter((u) => u.outputs.length > 0);
    if (!declaringUps.length) continue; // nothing declared upstream: can't judge
    const produced = new Set(declaringUps.flatMap((u) => u.outputs.map(norm)));
    const missing = n.inputs.filter((i) => !produced.has(norm(i)));
    if (missing.length) {
      add({
        code: "io-unsatisfied-input",
        severity: "warning",
        title: "Input not produced upstream",
        detail: `"${n.name}" requires ${missing.map((m) => `"${m}"`).join(", ")}, but no upstream stage declares it as an output.`,
        nodeIds: [n.id],
      });
    }
  }
  for (const e of validEdges) {
    const s = byId.get(e.source)!;
    const t = byId.get(e.target)!;
    if (!s.outputs.length || !t.inputs.length) continue;
    const outs = new Set(s.outputs.map(norm));
    if (!t.inputs.some((i) => outs.has(norm(i)))) {
      add({
        code: "io-no-overlap",
        severity: "info",
        title: "Connection passes nothing declared",
        detail: `"${s.name}" → "${t.name}": none of ${s.name}'s outputs match ${t.name}'s declared inputs.`,
        nodeIds: [s.id, t.id],
      });
    }
  }

  // Possible redundancy: same name + task type + same direct parents
  const seen = new Map<string, string>();
  for (const n of w.nodes) {
    const key = `${norm(n.name)}|${n.taskType}|${incoming(n.id, validEdges).sort().join(",")}`;
    const prev = seen.get(key);
    if (prev) {
      add({
        code: "possible-redundancy",
        severity: "info",
        title: "Possibly redundant stages",
        detail: `"${n.name}" appears twice with the same task type and the same inputs.`,
        nodeIds: [prev, n.id],
      });
    } else seen.set(key, n.id);
  }

  return { structural: f, evidence: [], evidenceNotice: EVIDENCE_NOTICE, counts: countBy(f) };
}

function countBy(f: StructuralFinding[]): Record<FindingSeverity, number> {
  return {
    error: f.filter((x) => x.severity === "error").length,
    warning: f.filter((x) => x.severity === "warning").length,
    info: f.filter((x) => x.severity === "info").length,
  };
}
