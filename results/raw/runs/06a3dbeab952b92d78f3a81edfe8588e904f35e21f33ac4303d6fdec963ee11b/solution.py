import heapq

def dependency_order(deps):
    # Every key and every referenced node is part of the graph.
    nodes = set(deps)
    for key in deps:
        nodes.update(deps[key])

    # dependencies[n]: nodes that must appear before n.
    dependencies = {n: set(deps.get(n, ())) for n in nodes}
    # dependents[n]: nodes that list n as a dependency.
    dependents = {n: set() for n in nodes}
    for n in nodes:
        for d in dependencies[n]:
            dependents[d].add(n)

    ready = [n for n in nodes if not dependencies[n]]
    heapq.heapify(ready)
    out = []
    while ready:
        n = heapq.heappop(ready)
        out.append(n)
        for m in dependents[n]:
            dependencies[m].discard(n)
            if not dependencies[m]:
                heapq.heappush(ready, m)

    if len(out) != len(nodes):
        raise ValueError("dependency cycle detected")
    return out
