/**
 * Typed graph-edit actions and workflow diffs.
 *
 * Planner/chat providers never mutate the graph directly: they return
 * GraphEditAction[] (or a whole draft). The UI previews the resulting diff and
 * only commits after the user clicks Apply.
 */
import { edgeIdFor, type Workflow, type WorkflowEdge, type WorkflowNode } from "./schema";
import { validateWorkflow, type ValidationReport } from "./validate";

export type NodePatch = Partial<Omit<WorkflowNode, "id">>;

export type GraphEditAction =
  | { type: "addNode"; node: WorkflowNode }
  | { type: "removeNode"; nodeId: string }
  | { type: "updateNode"; nodeId: string; patch: NodePatch }
  | { type: "addEdge"; source: string; target: string; id?: string }
  | { type: "removeEdge"; edgeId: string };

export interface ApplyResult {
  ok: boolean;
  workflow: Workflow;
  errors: string[];
  validation: ValidationReport;
}

/**
 * Apply actions in order to a copy of `w`. Fails (ok=false, original returned)
 * when an action references a missing item or the result has validation errors
 * (e.g. a cycle). Removing a node also removes its edges.
 */
export function applyEdits(w: Workflow, actions: readonly GraphEditAction[]): ApplyResult {
  const errors: string[] = [];
  let nodes = w.nodes.map((n) => ({ ...n }));
  let edges = w.edges.map((e) => ({ ...e }));

  for (const [i, a] of actions.entries()) {
    switch (a.type) {
      case "addNode":
        if (nodes.some((n) => n.id === a.node.id)) errors.push(`#${i} addNode: id "${a.node.id}" already exists.`);
        else nodes.push({ ...a.node });
        break;
      case "removeNode":
        if (!nodes.some((n) => n.id === a.nodeId)) errors.push(`#${i} removeNode: "${a.nodeId}" not found.`);
        nodes = nodes.filter((n) => n.id !== a.nodeId);
        edges = edges.filter((e) => e.source !== a.nodeId && e.target !== a.nodeId);
        break;
      case "updateNode": {
        const idx = nodes.findIndex((n) => n.id === a.nodeId);
        if (idx < 0) errors.push(`#${i} updateNode: "${a.nodeId}" not found.`);
        else nodes[idx] = { ...nodes[idx], ...a.patch, id: a.nodeId };
        break;
      }
      case "addEdge": {
        const id = a.id ?? edgeIdFor(a.source, a.target);
        if (!nodes.some((n) => n.id === a.source) || !nodes.some((n) => n.id === a.target)) {
          errors.push(`#${i} addEdge: ${a.source} → ${a.target} references a missing stage.`);
        } else if (edges.some((e) => e.source === a.source && e.target === a.target)) {
          errors.push(`#${i} addEdge: ${a.source} → ${a.target} already exists.`);
        } else {
          edges.push({ id, source: a.source, target: a.target });
        }
        break;
      }
      case "removeEdge":
        if (!edges.some((e) => e.id === a.edgeId)) errors.push(`#${i} removeEdge: "${a.edgeId}" not found.`);
        edges = edges.filter((e) => e.id !== a.edgeId);
        break;
    }
  }

  const next: Workflow = { ...w, nodes, edges };
  const validation = validateWorkflow(next);
  if (!validation.valid) {
    errors.push(...validation.issues.filter((x) => x.severity === "error").map((x) => x.message));
  }
  if (errors.length) return { ok: false, workflow: w, errors, validation };
  return { ok: true, workflow: next, errors, validation };
}

// ---------------------------------------------------------------------------
// Diff
// ---------------------------------------------------------------------------

export interface NodeModification {
  id: string;
  fields: string[];
}

export interface WorkflowDiff {
  addedNodes: string[];
  removedNodes: string[];
  modifiedNodes: NodeModification[];
  /** Edges are compared by (source, target), not by id. */
  addedEdges: Pick<WorkflowEdge, "source" | "target">[];
  removedEdges: Pick<WorkflowEdge, "source" | "target">[];
}

const COMPARED_FIELDS: (keyof WorkflowNode)[] = [
  "name",
  "description",
  "taskType",
  "model",
  "customModelLabel",
  "inputs",
  "outputs",
  "mergeStrategy",
  "executionConfig",
];

function sameValue(a: unknown, b: unknown): boolean {
  return JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
}

/** Diff two workflows. Position changes are ignored unless `includePositions`. */
export function diffWorkflows(before: Pick<Workflow, "nodes" | "edges">, after: Pick<Workflow, "nodes" | "edges">, opts: { includePositions?: boolean } = {}): WorkflowDiff {
  const b = new Map(before.nodes.map((n) => [n.id, n]));
  const a = new Map(after.nodes.map((n) => [n.id, n]));
  const fields = opts.includePositions ? [...COMPARED_FIELDS, "position" as const] : COMPARED_FIELDS;

  const addedNodes = after.nodes.filter((n) => !b.has(n.id)).map((n) => n.id);
  const removedNodes = before.nodes.filter((n) => !a.has(n.id)).map((n) => n.id);
  const modifiedNodes: NodeModification[] = [];
  for (const n of after.nodes) {
    const old = b.get(n.id);
    if (!old) continue;
    const changed = fields.filter((f) => !sameValue(old[f], n[f]));
    if (changed.length) modifiedNodes.push({ id: n.id, fields: changed });
  }

  const key = (e: { source: string; target: string }) => `${e.source}\u0000${e.target}`;
  const bE = new Set(before.edges.map(key));
  const aE = new Set(after.edges.map(key));
  const addedEdges = after.edges.filter((e) => !bE.has(key(e))).map(({ source, target }) => ({ source, target }));
  const removedEdges = before.edges.filter((e) => !aE.has(key(e))).map(({ source, target }) => ({ source, target }));

  return { addedNodes, removedNodes, modifiedNodes, addedEdges, removedEdges };
}

export function isEmptyDiff(d: WorkflowDiff): boolean {
  return !d.addedNodes.length && !d.removedNodes.length && !d.modifiedNodes.length && !d.addedEdges.length && !d.removedEdges.length;
}

export function summarizeDiff(d: WorkflowDiff): string {
  const parts: string[] = [];
  const nodeBits = [
    d.addedNodes.length && `+${d.addedNodes.length} stage${d.addedNodes.length === 1 ? "" : "s"}`,
    d.removedNodes.length && `−${d.removedNodes.length} stage${d.removedNodes.length === 1 ? "" : "s"}`,
    d.modifiedNodes.length && `~${d.modifiedNodes.length} modified`,
  ].filter(Boolean);
  const edgeBits = [
    d.addedEdges.length && `+${d.addedEdges.length} connection${d.addedEdges.length === 1 ? "" : "s"}`,
    d.removedEdges.length && `−${d.removedEdges.length} connection${d.removedEdges.length === 1 ? "" : "s"}`,
  ].filter(Boolean);
  parts.push(...(nodeBits as string[]), ...(edgeBits as string[]));
  return parts.length ? parts.join(" · ") : "No changes";
}
