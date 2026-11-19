import { describe, expect, it } from "vitest";
import { nodesOnCycles, topoSort, weakComponents, wouldCreateCycle } from "../src/lib/workflow/graph";
import { validateWorkflow } from "../src/lib/workflow/validate";
import { makeNode } from "../src/lib/workflow/schema";
import { wf } from "./helpers";

const codes = (w: Parameters<typeof validateWorkflow>[0]) => validateWorkflow(w).issues.map((i) => i.code);

describe("graph helpers", () => {
  it("detects that an edge would close a cycle", () => {
    const edges = [
      { source: "a", target: "b" },
      { source: "b", target: "c" },
    ];
    expect(wouldCreateCycle(edges, "c", "a")).toBe(true);
    expect(wouldCreateCycle(edges, "a", "c")).toBe(false);
    expect(wouldCreateCycle(edges, "a", "a")).toBe(true);
  });

  it("topologically sorts fan-out / fan-in", () => {
    const { order, blocked } = topoSort(["a", "b", "c", "d"], [
      { source: "a", target: "b" },
      { source: "a", target: "c" },
      { source: "b", target: "d" },
      { source: "c", target: "d" },
    ]);
    expect(order[0]).toBe("a");
    expect(order[3]).toBe("d");
    expect(blocked).toEqual([]);
  });

  it("finds nodes on cycles only", () => {
    expect(nodesOnCycles(["a", "b", "c", "d"], [
      { source: "a", target: "b" },
      { source: "b", target: "c" },
      { source: "c", target: "b" },
      { source: "c", target: "d" },
    ])).toEqual(["b", "c"]);
  });

  it("groups weak components", () => {
    expect(weakComponents(["a", "b", "c"], [{ source: "a", target: "b" }])).toHaveLength(2);
  });
});

describe("validateWorkflow", () => {
  it("accepts a valid DAG with parallel branches", () => {
    const r = validateWorkflow(wf(["a", "b", "c", "d"], [["a", "b"], ["a", "c"], ["b", "d"], ["c", "d"]]));
    expect(r.valid).toBe(true);
    expect(r.issues).toEqual([]);
  });

  it("warns on empty workflow", () => {
    expect(codes(wf([], []))).toEqual(["empty"]);
  });

  it("errors on duplicate node ids", () => {
    const w = wf(["a", "b"], [["a", "b"]]);
    w.nodes.push(makeNode({ id: "a" }));
    const r = validateWorkflow(w);
    expect(r.valid).toBe(false);
    expect(r.issues.map((i) => i.code)).toContain("duplicate-node-id");
  });

  it("errors on duplicate edge ids and warns on duplicate parallel edges", () => {
    const w = wf(["a", "b"], [["a", "b"], ["a", "b"]]);
    expect(codes(w)).toContain("duplicate-edge-id");
    w.edges[1].id = "other";
    expect(codes(w)).toEqual(["duplicate-edge"]);
  });

  it("errors on dangling edges", () => {
    const w = wf(["a"], [["a", "ghost"]]);
    const r = validateWorkflow(w);
    expect(r.valid).toBe(false);
    expect(r.issues[0].code).toBe("dangling-edge");
  });

  it("errors on cycles and self loops", () => {
    expect(codes(wf(["a", "b"], [["a", "b"], ["b", "a"]]))).toContain("cycle");
    expect(codes(wf(["a"], [["a", "a"]]))).toContain("self-loop");
  });

  it("warns on disconnected stages and names the strays", () => {
    const r = validateWorkflow(wf(["a", "b", "c"], [["a", "b"]]));
    expect(r.valid).toBe(true);
    const d = r.issues.find((i) => i.code === "disconnected")!;
    expect(d.nodeIds).toEqual(["c"]);
  });
});
