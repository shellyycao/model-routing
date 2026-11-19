from collections import deque


def shortest_path(graph, start, goal):
    queue = deque([(start, [start])])
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
