import heapq

def dependency_order(deps):
    # Collect all nodes: keys and all referenced dependencies
    nodes = set(deps.keys())
    for vals in deps.values():
        nodes.update(vals)
    
    # Build incoming sets for all nodes
    incoming = {n: set() for n in nodes}
    for n, deps_list in deps.items():
        for d in deps_list:
            incoming[n].add(d)
    
    # Initialize heap with nodes that have no dependencies
    ready = [n for n in nodes if not incoming[n]]
    heapq.heapify(ready)
    
    in_ready = set(ready)
    out = []
    out_set = set()
    
    while ready:
        n = heapq.heappop(ready)
        in_ready.discard(n)
        out.append(n)
        out_set.add(n)
        
        for m in nodes:
            if n in incoming[m]:
                incoming[m].remove(n)
                if not incoming[m] and m not in out_set and m not in in_ready:
                    heapq.heappush(ready, m)
                    in_ready.add(m)
    
    if len(out) != len(nodes):
        raise ValueError('Cycle detected in dependencies')
    
    return out
