def sessionize(events, gap):
    """
    Group events into user sessions.

    Parameters
    ----------
    events : iterable of (user, timestamp)
        Unordered collection of events.
    gap : number
        Maximum allowed time difference within a session. A new session
        starts when the difference between consecutive timestamps for the same
        user is strictly greater than ``gap``.

    Returns
    -------
    dict
        Mapping from user to a list of sessions, where each session is a list
        of timestamps in chronological order. The input ``events`` is not
        mutated.
    """
    # Work on a sorted copy to avoid mutating the original iterable.
    sorted_events = sorted(events, key=lambda e: (e[0], e[1]))

    out = {}
    for user, t in sorted_events:
        sessions = out.setdefault(user, [])
        # Start a new session if there is no previous session or the gap
        # between this timestamp and the last timestamp of the current session
        # is strictly greater than the allowed gap.
        if not sessions or t - sessions[-1][-1] > gap:
            sessions.append([t])
        else:
            sessions[-1].append(t)
    return out