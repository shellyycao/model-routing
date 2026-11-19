import { describe, expect, it } from "vitest";
import { applyEdits, diffWorkflows, isEmptyDiff, summarizeDiff } from "../src/lib/workflow/edits";
import { makeNode } from "../src/lib/workflow/schema";
import { wf } from "./helpers";

describe("applyEdits", () => {
  const base = wf(["a", "b"], [["a", "b"]]);

  it("adds a node and edges (fan-out)", () => {
    const r = applyEdits(base, [
      { type: "addNode", node: makeNode({ id: "c" }) },
      { type: "addEdge", source: "a", target: "c" },
    ]);
    expect(r.ok).toBe(true);
    expect(r.workflow.nodes.map((n) => n.id)).toEqual(["a", "b", "c"]);
    expect(base.nodes).toHaveLength(2); // input untouched
  });

  it("removing a node removes its edges", () => {
    const r = applyEdits(base, [{ type: "removeNode", nodeId: "b" }]);
    expect(r.ok).toBe(true);
    expect(r.workflow.edges).toEqual([]);
  });

  it("updates a node but never its id", () => {
    const r = applyEdits(base, [{ type: "updateNode", nodeId: "a", patch: { name: "Load", model: "glm_5" } }]);
    expect(r.workflow.nodes[0]).toMatchObject({ id: "a", name: "Load", model: "glm_5" });
  });

  it("rejects cycles, duplicates and missing references without mutating", () => {
    expect(applyEdits(base, [{ type: "addEdge", source: "b", target: "a" }]).ok).toBe(false);
    expect(applyEdits(base, [{ type: "addEdge", source: "a", target: "b" }]).ok).toBe(false);
    expect(applyEdits(base, [{ type: "addNode", node: makeNode({ id: "a" }) }]).ok).toBe(false);
    expect(applyEdits(base, [{ type: "removeEdge", edgeId: "nope" }]).ok).toBe(false);
    const bad = applyEdits(base, [{ type: "updateNode", nodeId: "zzz", patch: {} }]);
    expect(bad.ok).toBe(false);
    expect(bad.workflow).toBe(base);
  });
});

describe("diffWorkflows", () => {
  it("reports added/removed/modified nodes and edges", () => {
    const before = wf(["a", "b", "c"], [["a", "b"], ["b", "c"]]);
    const after = applyEdits(before, [
      { type: "removeNode", nodeId: "c" },
      { type: "addNode", node: makeNode({ id: "d" }) },
      { type: "addEdge", source: "a", target: "d" },
      { type: "updateNode", nodeId: "b", patch: { name: "Renamed", inputs: ["x"] } },
    ]).workflow;
    const d = diffWorkflows(before, after);
    expect(d.addedNodes).toEqual(["d"]);
    expect(d.removedNodes).toEqual(["c"]);
    expect(d.modifiedNodes).toEqual([{ id: "b", fields: ["name", "inputs"] }]);
    expect(d.addedEdges).toEqual([{ source: "a", target: "d" }]);
    expect(d.removedEdges).toEqual([{ source: "b", target: "c" }]);
    expect(summarizeDiff(d)).toBe("+1 stage · −1 stage · ~1 modified · +1 connection · −1 connection");
  });

  it("ignores position unless asked, and compares edges by endpoints", () => {
    const a = wf(["a", "b"], [["a", "b"]]);
    const b = structuredClone(a);
    b.nodes[0].position = { x: 999, y: 999 };
    b.edges[0].id = "renamed-edge";
    expect(isEmptyDiff(diffWorkflows(a, b))).toBe(true);
    expect(diffWorkflows(a, b, { includePositions: true }).modifiedNodes[0].fields).toEqual(["position"]);
  });
});
