import heapq
from typing import Dict, Iterable, List

def dependency_order(deps: Dict[str, Iterable[str]]) -> List[str]:
    """Return a deterministic topological ordering of the dependency graph.

    * ``deps`` maps a node to an iterable of nodes it depends on.
    * All nodes that appear either as a key or only as a dependency are included
      in the result.
    * When several nodes are ready (no remaining unmet dependencies) the
      alphabetically smallest one is chosen, guaranteeing deterministic output.
    * If the graph contains a cycle a ``ValueError`` is raised.
    """
    # ---------------------------------------------------------------------
    # 1. Collect the complete set of nodes (keys + referenced nodes).
    # ---------------------------------------------------------------------
    nodes = set(deps)
    for v in deps.values():
        nodes.update(v)

    # ---------------------------------------------------------------------
    # 2. Build the incoming‑dependency map and the outgoing adjacency map.
    # ---------------------------------------------------------------------
    incoming: Dict[str, set] = {n: set() for n in nodes}
    outgoing: Dict[str, set] = {n: set() for n in nodes}
    for node, dep_list in deps.items():
        for dep in dep_list:
            incoming[node].add(dep)
            outgoing[dep].add(node)

    # ---------------------------------------------------------------------
    # 3. Initialise the heap with nodes that have no incoming edges.
    # ---------------------------------------------------------------------
    ready = [n for n in nodes if not incoming[n]]
    heapq.heapify(ready)
    result: List[str] = []

    # ---------------------------------------------------------------------
    # 4. Process nodes in alphabetical order, updating the graph.
    # ---------------------------------------------------------------------
    while ready:
        n = heapq.heappop(ready)
        result.append(n)
        for m in outgoing[n]:
            incoming[m].remove(n)
            if not incoming[m]:
                heapq.heappush(ready, m)
        # Optional: clear to free memory (not required for correctness).
        outgoing[n].clear()

    # ---------------------------------------------------------------------
    # 5. Detect cycles – if any node was never emitted, a cycle exists.
    # ---------------------------------------------------------------------
    if len(result) != len(nodes):
        raise ValueError("Cycle detected in dependencies")

    return result
