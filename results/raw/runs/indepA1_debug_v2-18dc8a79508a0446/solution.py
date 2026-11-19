from collections import defaultdict, deque

def allowed(events, limit, window):
    """Return a list of booleans indicating whether each event is allowed.

    An event (user, time) is allowed if the number of *prior allowed* events for the
    same ``user`` that fall in the half‑open interval ``(time‑window, time]`` is
    strictly less than ``limit``. Rejected events do not consume capacity.
    """
    # Separate queues per user to track timestamps of allowed events only.
    user_queues = defaultdict(deque)
    out = []
    for user, t in events:
        q = user_queues[user]
        # Remove timestamps that are not in the window: those <= t - window.
        while q and q[0] <= t - window:
            q.popleft()
        if len(q) < limit:
            out.append(True)
            q.append(t)  # record this allowed event
        else:
            out.append(False)  # rejected, do not record
    return out
