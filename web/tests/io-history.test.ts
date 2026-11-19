import { describe, expect, it } from "vitest";
import { commit, commitFrom, createHistory, redo, replacePresent, undo } from "../src/lib/workflow/history";
import { exportWorkflowJson, exportWorkflowYaml, importWorkflowText } from "../src/lib/workflow/io";
import { parseWorkflow } from "../src/lib/workflow/schema";
import { NOW, wf } from "./helpers";

describe("import / export", () => {
  const w = wf(["a", "b"], [["a", "b"]]);

  it("round-trips JSON", () => {
    const r = importWorkflowText(exportWorkflowJson(w), { now: NOW });
    expect(r.ok && r.workflow).toEqual(w);
    expect(r.format).toBe("json");
  });

  it("round-trips YAML", () => {
    const r = importWorkflowText(exportWorkflowYaml(w), { now: NOW });
    expect(r.ok && r.workflow).toEqual(w);
    expect(r.format).toBe("yaml");
  });

  it("accepts the prototype's {label,x,y,from,to} shape with defaults", () => {
    const r = importWorkflowText(JSON.stringify({ name: "Old", nodes: [{ id: "n1", label: "Collect", x: 10, y: 20 }, { id: "n2", label: "Analyze" }], edges: [{ from: "n1", to: "n2" }] }), { now: NOW });
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.workflow.nodes[0]).toMatchObject({ name: "Collect", position: { x: 10, y: 20 }, model: "unassigned" });
    expect(r.workflow.edges[0]).toMatchObject({ source: "n1", target: "n2" });
    expect(r.warnings.join(" ")).toMatch(/schemaVersion missing/);
  });

  it("rejects unsupported versions, malformed text and bad shapes", () => {
    expect(parseWorkflow({ schemaVersion: 2, nodes: [] }).ok).toBe(false);
    expect(importWorkflowText("{ not json").ok).toBe(false);
    expect(importWorkflowText("").ok).toBe(false);
    expect(parseWorkflow({ nodes: [{ name: "no id" }] }).ok).toBe(false);
    expect(parseWorkflow({ nodes: [], edges: [{ source: "a" }] }).ok).toBe(false);
  });
});

describe("history", () => {
  it("undoes and redoes; commit clears redo", () => {
    let h = createHistory(1);
    h = commit(h, 2);
    h = commit(h, 3);
    h = undo(h);
    expect(h.present).toBe(2);
    h = redo(h);
    expect(h.present).toBe(3);
    h = undo(h);
    h = commit(h, 9);
    expect(h.future).toEqual([]);
    expect(redo(h)).toBe(h);
  });

  it("records a drag as a single undo step", () => {
    let h = createHistory("start");
    const origin = h.present;
    h = replacePresent(h, "mid");
    h = replacePresent(h, "end");
    h = commitFrom(h, origin);
    expect(h.past).toEqual(["start"]);
    expect(undo(h).present).toBe("start");
  });

  it("caps history length", () => {
    let h = createHistory(0);
    for (let i = 1; i <= 10; i++) h = commit(h, i, 3);
    expect(h.past).toEqual([7, 8, 9]);
  });
});
