from bisect import bisect_right, insort
from collections import defaultdict

def allowed(events, limit, window):
    accepted = defaultdict(list)
    out = []
    for user, t in events:
        times = accepted[user]
        start = t - window
        in_window = bisect_right(times, t) - bisect_right(times, start)
        ok = in_window < limit
        out.append(ok)
        if ok:
            insort(times, t)
    return out
