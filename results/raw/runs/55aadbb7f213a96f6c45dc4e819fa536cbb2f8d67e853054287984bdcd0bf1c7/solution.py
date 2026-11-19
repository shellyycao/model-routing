import heapq


def dependency_order(deps):
    # Include every key and every referenced dependency node.
    nodes = set(deps)
    for refs in deps.values():
        nodes.update(refs)

    # remaining[n] = dependencies of n that have not been emitted yet.
    remaining = {n: set(deps.get(n, [])) for n in nodes}
    dependents = {n: [] for n in nodes}
    for n in nodes:
        for d in remaining[n]:
            dependents[d].append(n)

    # Nodes with no outstanding dependencies, smallest first.
    ready = [n for n in nodes if not remaining[n]]
    heapq.heapify(ready)

    out = []
    while ready:
        n = heapq.heappop(ready)
        out.append(n)
        for m in dependents[n]:
            remaining[m].discard(n)
            if not remaining[m]:
                heapq.heappush(ready, m)

    if len(out) != len(nodes):
        raise ValueError("dependency cycle detected")
    return out
