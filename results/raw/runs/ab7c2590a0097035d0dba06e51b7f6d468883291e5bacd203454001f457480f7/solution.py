from collections import deque
def allowed(events, limit, window):
    queues = {}
    out = []
    for user, t in events:
        if user not in queues:
            queues[user] = deque()
        q = queues[user]
        while q and q[0] <= t - window:
            q.popleft()
        ok = len(q) < limit
        out.append(ok)
        if ok:
            q.append(t)
    return out
