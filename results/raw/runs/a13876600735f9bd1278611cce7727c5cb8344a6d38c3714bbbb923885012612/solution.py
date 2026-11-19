from collections import defaultdict, deque

def allowed(events, limit, window):
    qs = defaultdict(deque)
    out = []
    for user, t in events:
        q = qs[user]
        while q and q[0] <= t - window:
            q.popleft()
        ok = len(q) < limit
        out.append(ok)
        if ok:
            q.append(t)
    return out
