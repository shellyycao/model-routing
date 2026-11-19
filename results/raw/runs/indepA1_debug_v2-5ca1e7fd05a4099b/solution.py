def shortest_path(graph, start, goal):
    """Return a shortest path from *start* to *goal* in an unweighted directed graph.

    The graph is a mapping from node to an iterable of neighbour nodes.  Neighbours are
    explored in the order they appear in the adjacency list.  If *goal* is unreachable,
    ``None`` is returned.
    """
    from collections import deque

    # BFS queue holds tuples of (current_node, path_to_current_node)
    queue = deque()
    queue.append((start, [start]))
    # Mark nodes as seen when they are enqueued to avoid duplicate work.
    seen = {start}

    while queue:
        node, path = queue.popleft()
        if node == goal:
            return path
        for neighbour in graph.get(node, []):
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append((neighbour, path + [neighbour]))
    return None