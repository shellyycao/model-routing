/**
 * Built-in example patterns for the Studio palette. Models are deliberately
 * left "unassigned": examples never pre-select a model.
 */
import { layoutLayered } from "./layout";
import { SCHEMA_VERSION, edgeIdFor, makeNode, type TaskType, type Workflow } from "./schema";

type Spec = [id: string, name: string, taskType: TaskType, after: string[]];

function build(name: string, specs: Spec[], now: string, merge: string[] = []): Workflow {
  const nodes = specs.map(([id, n, t]) => makeNode({ id, name: n, taskType: t, mergeStrategy: merge.includes(id) ? "wait-all" : undefined }));
  const edges = specs.flatMap(([id, , , after]) => after.map((p) => ({ id: edgeIdFor(p, id), source: p, target: id })));
  return {
    schemaVersion: SCHEMA_VERSION,
    id: "example",
    name,
    description: "Example pattern. Models are not assigned.",
    nodes: layoutLayered(nodes, edges),
    edges,
    meta: { createdAt: now, updatedAt: now, origin: "example" },
  };
}

export function exampleParallel(now: string): Workflow {
  return build(
    "Parallel branches example",
    [
      ["src", "Input data", "source", []],
      ["prep", "Prepare", "cleaning", ["src"]],
      ["branch_a", "Branch A", "analysis", ["prep"]],
      ["branch_b", "Branch B", "analysis", ["prep"]],
      ["branch_c", "Branch C", "analysis", ["prep"]],
      ["combine", "Combine results", "merge", ["branch_a", "branch_b", "branch_c"]],
      ["out", "Deliverable", "output", ["combine"]],
    ],
    now,
    ["combine"],
  );
}

export function examplePipeline(now: string): Workflow {
  return build(
    "Simple pipeline example",
    [
      ["src", "Input data", "source", []],
      ["step1", "Step 1", "custom", ["src"]],
      ["step2", "Step 2", "custom", ["step1"]],
      ["out", "Deliverable", "output", ["step2"]],
    ],
    now,
  );
}
