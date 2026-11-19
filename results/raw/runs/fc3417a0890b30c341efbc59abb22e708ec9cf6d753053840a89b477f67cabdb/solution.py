import heapq

def dependency_order(deps):
    # Collect all nodes: keys and all referenced dependencies
    nodes = set(deps)
    for vals in deps.values():
        nodes.update(vals)
    
    # Build incoming sets (dependencies that must come before each node)
    incoming = {n: set(deps.get(n, [])) for n in nodes}
    
    # Start with nodes that have no dependencies
    ready = [n for n in nodes if not incoming[n]]
    heapq.heapify(ready)
    
    out = []
    in_ready = set(ready)  # track what's in the heap to avoid duplicates
    
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
