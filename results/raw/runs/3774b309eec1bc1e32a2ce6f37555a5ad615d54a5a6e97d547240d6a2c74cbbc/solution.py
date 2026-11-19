def shortest_path(graph, start, goal):
    from collections import deque
    queue = deque([(start, [start])])
    seen = {start}
    while queue:
        node, path = queue.popleft()
        if node == goal:
            return path
        for n in graph.get(node, []):
            if n not in seen:
                seen.add(n)
                queue.append((n, path + [n]))
    return None