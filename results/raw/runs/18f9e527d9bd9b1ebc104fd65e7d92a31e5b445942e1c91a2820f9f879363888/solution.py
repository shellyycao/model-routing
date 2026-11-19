from collections import deque


def shortest_path(graph, start, goal):
    if start == goal:
        return [start]

    queue = deque([(start, [start])])
    seen = {start}

    while queue:
        node, path = queue.popleft()
        for neighbour in graph.get(node, []):
            if neighbour in seen:
                continue
            new_path = path + [neighbour]
            if neighbour == goal:
                return new_path
            seen.add(neighbour)
            queue.append((neighbour, new_path))

    return None
