def shortest_path(graph, start, goal):
    queue = [(start, [start])]
    seen = set()
    while queue:
        node, path = queue.pop(0)
        if node in seen:
            continue
        seen.add(node)
        if node == goal:
            return path
        queue += [(n, path + [n]) for n in graph.get(node, []) if n not in seen]
    return None
