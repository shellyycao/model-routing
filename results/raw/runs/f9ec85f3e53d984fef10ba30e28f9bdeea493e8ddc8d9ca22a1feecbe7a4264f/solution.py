from collections import defaultdict, deque

def allowed(events, limit, window):
    q = defaultdict(deque)
    out = []
    for user, t in events:
        # Remove events older than or equal to t - window (outside the window)
        while q[user] and q[user][0] <= t - window:
            q[user].popleft()
        # Check if the number of prior allowed events is within the limit
        ok = len(q[user]) < limit
        out.append(ok)
        # Only add the event to the queue if it was allowed
        if ok:
            q[user].append(t)
    return out
