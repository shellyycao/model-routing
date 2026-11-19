import type { Workflow, WorkflowNode } from "./schema";

/** Simple layered layout: column = longest path depth, rows spread evenly. */
export function layoutLayered(nodes: WorkflowNode[], edges: Workflow["edges"], opts = { dx: 290, dy: 150, x0: 60, y0: 80 }): WorkflowNode[] {
  const depth = new Map<string, number>(nodes.map((n) => [n.id, 0]));
  // Relax edges |V| times (fine for small DAGs; terminates on cycles too).
  for (let i = 0; i < nodes.length; i++) {
    let changed = false;
    for (const e of edges) {
      if (!depth.has(e.source) || !depth.has(e.target)) continue;
      const d = depth.get(e.source)! + 1;
      if (d > depth.get(e.target)! && d < nodes.length) {
        depth.set(e.target, d);
        changed = true;
      }
    }
    if (!changed) break;
  }
  const cols = new Map<number, string[]>();
  for (const n of nodes) {
    const d = depth.get(n.id)!;
    if (!cols.has(d)) cols.set(d, []);
    cols.get(d)!.push(n.id);
  }
  const maxRows = Math.max(1, ...[...cols.values()].map((c) => c.length));
  const pos = new Map<string, { x: number; y: number }>();
  for (const [d, ids] of cols) {
    const offset = ((maxRows - ids.length) * opts.dy) / 2;
    ids.forEach((id, r) => pos.set(id, { x: opts.x0 + d * opts.dx, y: opts.y0 + offset + r * opts.dy }));
  }
  return nodes.map((n) => ({ ...n, position: pos.get(n.id)! }));
}
