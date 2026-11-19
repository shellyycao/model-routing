def dependency_order(deps):
    nodes = set(deps)
    # Include nodes that are referenced but not keys
    for v in deps.values():
        nodes.update(v)
    out = []
    while nodes:
        # Find nodes with no dependencies within the remaining set
        ready = sorted(n for n in nodes if not set(deps.get(n, [])) & nodes)
        if not ready:
            # If no nodes are ready, but nodes remain, there is a cycle
            raise ValueError("Cycle detected")
        out += ready
        nodes -= set(ready)
    return out