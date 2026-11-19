import heapq

def dependency_order(deps):
    # Collect all nodes: keys and all referenced nodes
    nodes = set(deps.keys())
    for deps_list in deps.values():
        nodes.update(deps_list)
    
    # Build incoming sets (dependencies that must come before each node)
    incoming = {n: set(deps.get(n, [])) for n in nodes}
    
    # Initialize heap with nodes that have no dependencies
    in_ready = set(n for n in nodes if not incoming[n])
    ready = list(in_ready)
    heapq.heapify(ready)
    out = []
    
    while ready:
        n = heapq.heappop(ready)
        in_ready.discard(n)
        out.append(n)
        for m in nodes:
            if n in incoming[m]:
                incoming[m].remove(n)
                if not incoming[m] and m not in out and m not in in_ready:
                    heapq.heappush(ready, m)
                    in_ready.add(m)
    
    if len(out) != len(nodes):
        raise ValueError('Cycle detected in dependencies')
    
    return out
