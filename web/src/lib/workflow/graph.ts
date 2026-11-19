/** Pure graph helpers over (nodeIds, edges). No framework imports. */

export interface EdgeLike {
  source: string;
  target: string;
}

export function adjacency(nodeIds: Iterable<string>, edges: readonly EdgeLike[]): Map<string, string[]> {
  const adj = new Map<string, string[]>();
  for (const id of nodeIds) adj.set(id, []);
  for (const e of edges) {
    if (adj.has(e.source) && adj.has(e.target)) adj.get(e.source)!.push(e.target);
  }
  return adj;
}

/** True when `to` is reachable from `from` following edge direction. */
export function isReachable(from: string, to: string, edges: readonly EdgeLike[]): boolean {
  if (from === to) return true;
  const out = new Map<string, string[]>();
  for (const e of edges) {
    if (!out.has(e.source)) out.set(e.source, []);
    out.get(e.source)!.push(e.target);
  }
  const seen = new Set<string>([from]);
  const stack = [from];
  while (stack.length) {
    const cur = stack.pop()!;
    for (const nxt of out.get(cur) ?? []) {
      if (nxt === to) return true;
      if (!seen.has(nxt)) {
        seen.add(nxt);
        stack.push(nxt);
      }
    }
  }
  return false;
}

/** Adding source→target creates a cycle iff source is reachable from target (or it is a self-loop). */
export function wouldCreateCycle(edges: readonly EdgeLike[], source: string, target: string): boolean {
  return source === target || isReachable(target, source, edges);
}

/**
 * Kahn topological sort. Returns the order and the set of nodes that could not
 * be ordered (they are on, or downstream of, a cycle).
 */
export function topoSort(nodeIds: readonly string[], edges: readonly EdgeLike[]): { order: string[]; blocked: string[] } {
  const ids = new Set(nodeIds);
  const indeg = new Map<string, number>();
  const out = new Map<string, string[]>();
  for (const id of nodeIds) {
    indeg.set(id, 0);
    out.set(id, []);
  }
  for (const e of edges) {
    if (!ids.has(e.source) || !ids.has(e.target)) continue;
    out.get(e.source)!.push(e.target);
    indeg.set(e.target, indeg.get(e.target)! + 1);
  }
  const queue = nodeIds.filter((id) => indeg.get(id) === 0);
  const order: string[] = [];
  while (queue.length) {
    const cur = queue.shift()!;
    order.push(cur);
    for (const nxt of out.get(cur)!) {
      indeg.set(nxt, indeg.get(nxt)! - 1);
      if (indeg.get(nxt) === 0) queue.push(nxt);
    }
  }
  const done = new Set(order);
  return { order, blocked: nodeIds.filter((id) => !done.has(id)) };
}

/** Node ids that lie on at least one directed cycle (Tarjan SCC, size>1 or self-loop). */
export function nodesOnCycles(nodeIds: readonly string[], edges: readonly EdgeLike[]): string[] {
  const adj = adjacency(nodeIds, edges);
  let index = 0;
  const idx = new Map<string, number>();
  const low = new Map<string, number>();
  const onStack = new Set<string>();
  const stack: string[] = [];
  const result = new Set<string>();

  const strong = (v: string) => {
    idx.set(v, index);
    low.set(v, index);
    index++;
    stack.push(v);
    onStack.add(v);
    for (const w of adj.get(v)!) {
      if (!idx.has(w)) {
        strong(w);
        low.set(v, Math.min(low.get(v)!, low.get(w)!));
      } else if (onStack.has(w)) {
        low.set(v, Math.min(low.get(v)!, idx.get(w)!));
      }
    }
    if (low.get(v) === idx.get(v)) {
      const comp: string[] = [];
      let w: string;
      do {
        w = stack.pop()!;
        onStack.delete(w);
        comp.push(w);
      } while (w !== v);
      if (comp.length > 1 || adj.get(v)!.includes(v)) comp.forEach((c) => result.add(c));
    }
  };
  for (const id of nodeIds) if (!idx.has(id)) strong(id);
  return nodeIds.filter((id) => result.has(id));
}

/** Weakly connected components, each listed in input order. */
export function weakComponents(nodeIds: readonly string[], edges: readonly EdgeLike[]): string[][] {
  const parent = new Map<string, string>();
  for (const id of nodeIds) parent.set(id, id);
  const find = (x: string): string => {
    let r = x;
    while (parent.get(r) !== r) r = parent.get(r)!;
    let c = x;
    while (parent.get(c) !== r) {
      const n = parent.get(c)!;
      parent.set(c, r);
      c = n;
    }
    return r;
  };
  for (const e of edges) {
    if (!parent.has(e.source) || !parent.has(e.target)) continue;
    const a = find(e.source);
    const b = find(e.target);
    if (a !== b) parent.set(a, b);
  }
  const groups = new Map<string, string[]>();
  for (const id of nodeIds) {
    const r = find(id);
    if (!groups.has(r)) groups.set(r, []);
    groups.get(r)!.push(id);
  }
  return [...groups.values()];
}

export function incoming(id: string, edges: readonly EdgeLike[]): string[] {
  return edges.filter((e) => e.target === id).map((e) => e.source);
}

export function outgoing(id: string, edges: readonly EdgeLike[]): string[] {
  return edges.filter((e) => e.source === id).map((e) => e.target);
}

/** All transitive ancestors of `id`. */
export function ancestors(id: string, edges: readonly EdgeLike[]): Set<string> {
  const seen = new Set<string>();
  const stack = [id];
  while (stack.length) {
    const cur = stack.pop()!;
    for (const p of incoming(cur, edges)) {
      if (!seen.has(p)) {
        seen.add(p);
        stack.push(p);
      }
    }
  }
  return seen;
}
