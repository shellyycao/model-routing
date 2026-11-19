def dependency_order(deps):
    nodes = set(deps)
    # Include all nodes referenced in dependency lists but not present as keys
    for node_list in deps.values():
        nodes.update(node_list)
    out = []
    while nodes:
        # Find nodes with no dependencies within the remaining set
        ready = sorted(n for n in nodes if not set(deps.get(n, [])) & nodes)
        if not ready:
            # If no nodes are ready, a cycle exists
            raise ValueError("Cycle detected")
        out += ready
        nodes -= set(ready)
    return out