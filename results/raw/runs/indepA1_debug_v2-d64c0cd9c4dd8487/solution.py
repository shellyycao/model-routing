from collections import defaultdict, deque

def allowed(events, limit, window):
    q = defaultdict(deque)
    out = []
    for user, t in events:
        while q[user] and q[user][0] <= t - window:
            q[user].popleft()
        ok = len(q[user]) < limit
        out.append(ok)
        if ok:
            q[user].append(t)
    return out
