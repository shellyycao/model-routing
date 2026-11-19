def shortest_path(graph, start, goal):
    queue = [(start, [start])]
    seen = set()
    while queue:
        node, path = queue.pop(0)
        seen.add(node)
        if node == goal:
            return path
        for n in graph.get(node, []):
            if n not in seen:
                queue.append((n, path + [n]))
    return None