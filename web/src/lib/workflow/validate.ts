import { nodesOnCycles, weakComponents } from "./graph";
import type { Workflow } from "./schema";

export type IssueSeverity = "error" | "warning";

export type IssueCode =
  | "empty"
  | "duplicate-node-id"
  | "duplicate-edge-id"
  | "duplicate-edge"
  | "self-loop"
  | "dangling-edge"
  | "cycle"
  | "disconnected";

export interface ValidationIssue {
  code: IssueCode;
  severity: IssueSeverity;
  message: string;
  nodeIds?: string[];
  edgeIds?: string[];
}

export interface ValidationReport {
  valid: boolean; // no errors (warnings allowed)
  issues: ValidationIssue[];
}

/**
 * Structural validation of a workflow graph.
 * Errors: duplicate ids, dangling edges, self-loops, cycles.
 * Warnings: empty graph, duplicate parallel edges, disconnected stages.
 */
export function validateWorkflow(w: Pick<Workflow, "nodes" | "edges">): ValidationReport {
  const issues: ValidationIssue[] = [];

  if (w.nodes.length === 0) {
    issues.push({ code: "empty", severity: "warning", message: "The workflow has no stages yet." });
  }

  // Duplicate node ids
  const seenNodes = new Map<string, number>();
  for (const n of w.nodes) seenNodes.set(n.id, (seenNodes.get(n.id) ?? 0) + 1);
  for (const [id, count] of seenNodes) {
    if (count > 1) {
      issues.push({ code: "duplicate-node-id", severity: "error", message: `Stage id "${id}" is used ${count} times.`, nodeIds: [id] });
    }
  }

  // Duplicate edge ids
  const seenEdges = new Map<string, number>();
  for (const e of w.edges) seenEdges.set(e.id, (seenEdges.get(e.id) ?? 0) + 1);
  for (const [id, count] of seenEdges) {
    if (count > 1) {
      issues.push({ code: "duplicate-edge-id", severity: "error", message: `Connection id "${id}" is used ${count} times.`, edgeIds: [id] });
    }
  }

  const nodeIds = new Set(w.nodes.map((n) => n.id));
  const validEdges = [];
  const pairSeen = new Map<string, string>();
  for (const e of w.edges) {
    const missing = [e.source, e.target].filter((x) => !nodeIds.has(x));
    if (missing.length) {
      issues.push({
        code: "dangling-edge",
        severity: "error",
        message: `Connection "${e.id}" points to missing stage(s): ${missing.join(", ")}.`,
        edgeIds: [e.id],
      });
      continue;
    }
    if (e.source === e.target) {
      issues.push({ code: "self-loop", severity: "error", message: `Stage "${e.source}" connects to itself.`, edgeIds: [e.id], nodeIds: [e.source] });
      continue;
    }
    const key = `${e.source}\u0000${e.target}`;
    if (pairSeen.has(key)) {
      issues.push({
        code: "duplicate-edge",
        severity: "warning",
        message: `Stages "${e.source}" → "${e.target}" are connected more than once.`,
        edgeIds: [pairSeen.get(key)!, e.id],
      });
      continue;
    }
    pairSeen.set(key, e.id);
    validEdges.push(e);
  }

  const uniqIds = [...seenNodes.keys()];
  const cyc = nodesOnCycles(uniqIds, validEdges);
  if (cyc.length) {
    issues.push({ code: "cycle", severity: "error", message: `Cycle detected through: ${cyc.join(", ")}. Workflows must be acyclic.`, nodeIds: cyc });
  }

  if (uniqIds.length > 1) {
    const comps = weakComponents(uniqIds, validEdges);
    if (comps.length > 1) {
      // The largest component is the "main" workflow; everything else is disconnected.
      const sorted = [...comps].sort((a, b) => b.length - a.length);
      const stray = sorted.slice(1).flat();
      issues.push({
        code: "disconnected",
        severity: "warning",
        message: `${comps.length} separate groups of stages; ${stray.length} stage(s) are not connected to the main workflow.`,
        nodeIds: stray,
      });
    }
  }

  return { valid: !issues.some((i) => i.severity === "error"), issues };
}
