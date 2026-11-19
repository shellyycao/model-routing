def dependency_order(deps):
    # Collect all nodes: keys and any nodes referenced in dependency lists
    nodes = set(deps)
    for dependencies in deps.values():
        nodes.update(dependencies)
    
    out = []
    while nodes:
        # Find nodes with no dependencies remaining in the 'nodes' set
        # Use get() to handle nodes that are referenced but not keys in the dict
        ready = sorted(n for n in nodes if not set(deps.get(n, [])) & nodes)
        
        if not ready:
            # If no nodes are ready, but nodes remain, there is a cycle
            raise ValueError("Cycle detected")
        
        out += ready
        nodes -= set(ready)
        
    return out