import heapq


def dependency_order(deps):
    '''Return a deterministic topological order for a dependency mapping.

    deps maps a node to an iterable of prerequisite nodes. Every key and
    every referenced node is emitted. Among nodes whose prerequisites have
    all been emitted, the alphabetically smallest node is chosen next.
    Raises ValueError if a cycle prevents a complete order.
    '''
    raw_deps = {node: set(node_deps) for node, node_deps in deps.items()}
    nodes = set(raw_deps)
    for node_deps in raw_deps.values():
        nodes.update(node_deps)

    dependencies = {node: raw_deps.get(node, set()) for node in nodes}
    dependents = {node: [] for node in nodes}
    indegree = {node: 0 for node in nodes}

    for node, node_deps in dependencies.items():
        for dep in node_deps:
            dependents[dep].append(node)
            indegree[node] += 1

    ready = [node for node, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    out = []

    while ready:
        node = heapq.heappop(ready)
        out.append(node)
        for dependent in dependents[node]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)

    if len(out) != len(nodes):
        raise ValueError('dependency graph contains a cycle')
    return out
