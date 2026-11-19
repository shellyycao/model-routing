from collections import defaultdict, deque

def allowed(events, limit, window):
    """Return a list of booleans indicating whether each event is allowed.

    An event (user, time) is allowed if the number of *previously allowed*
    events for the same user that fall in the half‑open interval
    (time‑window, time] is strictly less than ``limit``.  Rejected events do
    not consume capacity.
    """
    q = defaultdict(deque)  # stores timestamps of allowed events per user
    out = []
    for user, t in events:
        # Discard events that are not in the (t‑window, t] interval.
        # Events with timestamp <= t‑window are outside the interval because
        # the left side is open.
        while q[user] and q[user][0] <= t - window:
            q[user].popleft()
        ok = len(q[user]) < limit
        out.append(ok)
        # Only record the timestamp if the event is allowed; rejected events
        # must not affect future capacity checks.
        if ok:
            q[user].append(t)
    return out
