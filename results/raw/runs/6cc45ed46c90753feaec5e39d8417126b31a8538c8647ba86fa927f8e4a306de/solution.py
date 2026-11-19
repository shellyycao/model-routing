import heapq

def dependency_order(deps):
    # 1. Collect all nodes: keys and any nodes referenced in dependency lists.
    nodes = set(deps.keys())
    for dependencies in deps.values():
        nodes.update(dependencies)
    
    # 2. Build adjacency list and incoming degree count.
    # Initialize adjacency list for all nodes to ensure deterministic iteration.
    adj = {n: set() for n in nodes}
    incoming = {n: 0 for n in nodes}
    
    for u, dependencies in deps.items():
        for v in dependencies:
            if v not in adj:
                adj[v] = set() # Should be covered by node collection, but safe
            adj[v].add(u)
            incoming[u] += 1
            
    # 3. Initialize heap with nodes having 0 incoming edges.
    ready = [n for n in nodes if incoming[n] == 0]
    heapq.heapify(ready)
    
    out = []
    while ready:
        n = heapq.heappop(ready)
        out.append(n)
        
        # Iterate over neighbors (nodes that depend on n)
        for m in adj.get(n, []):
            incoming[m] -= 1
            if incoming[m] == 0:
                heapq.heappush(ready, m)
                
    # 4. Cycle detection.
    if len(out) != len(nodes):
        raise ValueError("Cycle detected")
        
    return out