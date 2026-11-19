def dependency_order(deps):
    # Collect all nodes: keys plus any referenced nodes not in keys
    all_nodes = set(deps.keys())
    for v in deps.values():
        all_nodes.update(v)
    # Build a working deps that includes referenced-only nodes with empty deps
    full_deps = {n: list(deps.get(n, [])) for n in all_nodes}
    nodes = set(all_nodes)
    out = []
    while nodes:
        ready = sorted(n for n in nodes if not set(full_deps.get(n, [])) & nodes)
        if not ready:
            raise ValueError("Cycle detected in dependencies")
        out += ready
        nodes -= set(ready)
    return out
