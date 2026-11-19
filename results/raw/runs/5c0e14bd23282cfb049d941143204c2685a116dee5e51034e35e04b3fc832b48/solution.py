from collections import defaultdict, deque


def allowed(events, limit, window):
    q = defaultdict(deque)
    out = []
    for user, t in events:
        # The counting window is (t - window, t]: the left endpoint is
        # exclusive, so evict prior allowed events at or before t - window.
        while q[user] and q[user][0] <= t - window:
            q[user].popleft()
        ok = len(q[user]) < limit
        out.append(ok)
        # Rejected events do not consume capacity; only record allowed ones.
        if ok:
            q[user].append(t)
    return out
