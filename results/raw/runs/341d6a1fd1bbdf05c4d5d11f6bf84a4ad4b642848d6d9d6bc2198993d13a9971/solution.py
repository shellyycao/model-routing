from bisect import bisect_right, insort_right
from collections import defaultdict

def allowed(events, limit, window):
    allowed_times = defaultdict(list)
    out = []
    for user, t in events:
        times = allowed_times[user]
        start = t - window
        if start < t:
            count = bisect_right(times, t) - bisect_right(times, start)
        else:
            count = 0
        ok = count < limit
        out.append(ok)
        if ok:
            insort_right(times, t)
    return out
