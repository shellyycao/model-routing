import heapq

def dependency_order(deps):
    nodes = set(deps)
    incoming = {n: set(deps.get(n, [])) for n in nodes}
    ready = [n for n in nodes if not incoming[n]]
    heapq.heapify(ready)
    out = []
    visited = set()
    while ready:
        n = heapq.heappop(ready)
        if n in visited:
            raise ValueError('Cycle detected')
        visited.add(n)
        out.append(n)
        for m in nodes:
            if n in incoming[m]:
                incoming[m].remove(n)
            if not incoming[m] and m not in out and m not in ready:
                heapq.heappush(ready, m)
    return out