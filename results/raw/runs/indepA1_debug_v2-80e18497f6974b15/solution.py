from collections import deque

def shortest_path(graph, start, goal):
    q = deque([(start, [start])])  # Include the start node in the path
    seen = set()
    while q:
        node, path = q.popleft()
        if node == goal:
            return path  # Return the full path when goal is reached
        for nxt in graph.get(node, []):
            if nxt not in seen:
                q.append((nxt, path + [nxt]))  # Append the next node to the path
                seen.add(nxt)
    return None