import heapq

def dependency_order(deps):
    # Collect all nodes: keys and any nodes referenced in dependency lists
    nodes = set(deps)
    for neighbors in deps.values():
        nodes.update(neighbors)
    
    # Build incoming edge sets for each node
    incoming = {n: set() for n in nodes}
    for n, neighbors in deps.items():
        for m in neighbors:
            incoming[m].add(n)
    
    # Initialize ready queue with nodes having no incoming edges
    ready = [n for n in nodes if not incoming[n]]
    heapq.heapify(ready)
    
    out = []
    while ready:
        n = heapq.heappop(ready)
        out.append(n)
        # Find nodes that depend on n (i.e., n is in their incoming set)
        # We can iterate over nodes, but a more efficient way is to track outgoing edges.
        # For simplicity and correctness, we iterate over all nodes.
        for m in nodes:
            if n in incoming[m]:
                incoming[m].remove(n)
                if not incoming[m] and m not in out and m not in ready:
                    heapq.heappush(ready, m)
    
    # Check for cycles
    if len(out) != len(nodes):
        raise ValueError("Cycle detected")
    
    return out
