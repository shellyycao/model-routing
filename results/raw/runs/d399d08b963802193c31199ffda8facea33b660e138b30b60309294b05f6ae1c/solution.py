import heapq


def dependency_order(deps):
    deps = {node: list(dependencies) for node, dependencies in deps.items()}

    nodes = set(deps)
    for dependencies in deps.values():
        nodes.update(dependencies)

    incoming = {node: set(deps.get(node, ())) for node in nodes}
    dependents = {node: set() for node in nodes}
    for node, dependencies in deps.items():
        for dependency in dependencies:
            dependents[dependency].add(node)

    ready = [node for node in nodes if not incoming[node]]
    heapq.heapify(ready)
    out = []

    while ready:
        node = heapq.heappop(ready)
        out.append(node)
        for dependent in dependents[node]:
            incoming[dependent].discard(node)
            if not incoming[dependent]:
                heapq.heappush(ready, dependent)

    if len(out) != len(nodes):
        remaining = sorted(node for node in nodes if incoming[node])
        raise ValueError('cycle detected involving: ' + ', '.join(map(str, remaining)))

    return out
