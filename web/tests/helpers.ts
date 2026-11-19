// SYNTHETIC_FIXTURE: hand-built workflows for unit tests only. Not research results.
import { SCHEMA_VERSION, edgeIdFor, makeNode, type Workflow } from "../src/lib/workflow/schema";

export const NOW = "2026-11-19T00:00:00.000Z";

export function wf(nodeIds: string[], pairs: [string, string][], extra: Partial<Workflow> = {}): Workflow {
  return {
    schemaVersion: SCHEMA_VERSION,
    id: "wf_test",
    name: "Test",
    description: "SYNTHETIC_FIXTURE",
    nodes: nodeIds.map((id, i) => makeNode({ id, name: id.toUpperCase(), position: { x: i * 100, y: 0 } })),
    edges: pairs.map(([s, t]) => ({ id: edgeIdFor(s, t), source: s, target: t })),
    meta: { createdAt: NOW, updatedAt: NOW, origin: "blank" },
    ...extra,
  };
}
