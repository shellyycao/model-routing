from bisect import bisect_right, insort
from collections import defaultdict

def allowed(events, limit, window):
    # user -> sorted list of times of prior ALLOWED events (input order preserved
    # by only inserting events as they are processed; sorted for interval counting).
    prior = defaultdict(list)
    out = []
    for user, t in events:
        times = prior[user]
        lo = t - window
        # Count prior allowed events for THIS user with lo < s <= t, i.e. in
        # (t - window, t]. Left endpoint exclusive, right endpoint inclusive.
        count = bisect_right(times, t) - bisect_right(times, lo)
        ok = count < limit
        out.append(ok)
        if ok:
            insort(times, t)  # rejected events are never inserted, so they consume no capacity
    return out
