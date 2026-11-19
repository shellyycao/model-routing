from collections import defaultdict, deque


def allowed(events, limit, window):
    q = defaultdict(deque)
    out = []
    for user, t in events:
        # Evict prior allowed events that are no longer in (t - window, t].
        # Events exactly at t - window are outside the half-open window.
        while q[user] and q[user][0] <= t - window:
            q[user].popleft()
        ok = len(q[user]) < limit
        out.append(ok)
        if ok:
            # Only allowed events consume capacity.
            q[user].append(t)
    return out
