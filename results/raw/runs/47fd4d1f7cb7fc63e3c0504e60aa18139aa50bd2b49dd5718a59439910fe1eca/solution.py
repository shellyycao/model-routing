import heapq


def dependency_order(deps):
    dependencies = {}
    nodes = set(deps)
    for node, node_deps in deps.items():
        node_deps = set(node_deps)
        dependencies[node] = node_deps
        nodes.update(node_deps)
    for node in nodes:
        dependencies.setdefault(node, set())

    dependents = {node: set() for node in nodes}
    indegree = {node: 0 for node in nodes}
    for node, node_deps in dependencies.items():
        indegree[node] = len(node_deps)
        for dependency in node_deps:
            dependents[dependency].add(node)

    available = [node for node in nodes if indegree[node] == 0]
    heapq.heapify(available)

    order = []
    while available:
        node = heapq.heappop(available)
        order.append(node)
        for dependent in dependents[node]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(available, dependent)

    if len(order) != len(nodes):
        raise ValueError('dependency graph contains a cycle')
    return order