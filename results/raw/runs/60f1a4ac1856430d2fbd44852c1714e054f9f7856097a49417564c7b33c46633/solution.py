from collections import deque

def shortest_path(graph, start, goal):
    q = deque([(start, [start])])
    seen = set([start])
    while q:
        node, path = q.popleft()
        if node == goal:
            return path
        for nxt in graph.get(node, []):
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, path + [nxt]))
    return None