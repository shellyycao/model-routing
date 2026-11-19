from collections import deque

def shortest_path(graph, start, goal):
    """Return a list of nodes representing a shortest path from start to goal
    in an unweighted directed graph, or None if no such path exists.
    Neighbours are explored in the order they appear in the adjacency list.
    """
    # BFS queue holds tuples (current_node, path_to_current_node)
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