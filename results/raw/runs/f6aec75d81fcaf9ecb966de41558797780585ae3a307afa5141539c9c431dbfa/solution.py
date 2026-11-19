import heapq

def dependency_order(deps):
    # Collect all nodes: keys and any nodes referenced in dependency lists
    nodes = set(deps)
    for neighbors in deps.values():
        nodes.update(neighbors)
    
    # Build incoming edge sets for every node
    incoming = {n: set() for n in nodes}
    for n, neighbors in deps.items():
        for m in neighbors:
            incoming[m].add(n)
    
    # Initialize ready queue with nodes that have no incoming edges
    ready = [n for n in nodes if not incoming[n]]
    heapq.heapify(ready)
    out = []
    
    while ready:
        n = heapq.heappop(ready)
        out.append(n)
        # Find nodes that depend on n (i.e., n is in their incoming set)
        # We iterate over a copy of incoming keys to avoid runtime errors if we modify incoming
        # though we only modify values here. Iterating over 'nodes' is also fine.
        for m in list(nodes):
            if n in incoming[m]:
                incoming[m].remove(n)
                if not incoming[m] and m not in out and m not in ready:
                    heapq.heappush(ready, m)
    
    # Check for cycle
    if len(out) != len(nodes):
        raise ValueError("Cycle detected")
        
    return out