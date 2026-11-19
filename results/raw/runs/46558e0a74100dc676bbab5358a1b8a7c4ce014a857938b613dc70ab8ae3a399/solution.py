from collections import deque

def shortest_path(graph, start, goal):
    if start == goal:
        return [start]
    q = deque([(start, [start])])
    seen = set([start])
    while q:
        node, path = q.popleft()
        for nxt in graph.get(node, []):
            if nxt not in seen:
                if nxt == goal:
                    return path + [nxt]
                q.append((nxt, path + [nxt]))
                seen.add(nxt)
    return None