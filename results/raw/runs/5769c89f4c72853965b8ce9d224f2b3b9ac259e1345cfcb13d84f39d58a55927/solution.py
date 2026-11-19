from collections import deque

def shortest_path(graph, start, goal):
    """Return a shortest node list from start to goal in an unweighted
    directed graph, or None if goal is unreachable.

    Neighbours are explored in listed order (breadth-first search).
    """
    q = deque([(start, [start])])
    seen = {start}
    while q:
        node, path = q.popleft()
        if node == goal:
            return path
        for nxt in graph.get(node, []):
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, path + [nxt]))
    return None
