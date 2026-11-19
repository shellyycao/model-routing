def dependency_order(deps):
    nodes = set(deps)
    out = []
    visited = set()
    while nodes:
        ready = sorted(n for n in nodes if not set(deps.get(n, [])) & nodes)
        if not ready:
            cycle_node = next(n for n in nodes if n not in visited)
            raise ValueError(f'Cycle detected involving node {cycle_node}')
        for node in ready:
            visited.add(node)
        out += ready
        nodes -= set(ready)
    return out
