import heapq


def dependency_order(deps):
    # Include every key and every referenced node.
    nodes = set(deps)
    for dependencies in deps.values():
        nodes.update(dependencies)

    # incoming[n] = prerequisites of n; dependents[d] = nodes that need d.
    incoming = {n: set(deps.get(n, ())) for n in nodes}
    dependents = {n: set() for n in nodes}
    for n, dependencies in incoming.items():
        for d in dependencies:
            dependents[d].add(n)

    ready = [n for n in nodes if not incoming[n]]
    heapq.heapify(ready)
    out = []

    while ready:
        n = heapq.heappop(ready)
        out.append(n)
        for m in dependents[n]:
            incoming[m].remove(n)
            if not incoming[m]:
                heapq.heappush(ready, m)

    if len(out) != len(nodes):
        raise ValueError("dependency graph contains a cycle")

    return out
