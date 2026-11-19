def sessionize(events, gap):
    # Sort events by user, then timestamp to ensure correct session grouping
    sorted_events = sorted(events, key=lambda x: (x[0], x[1]))
    out = {}
    for user, t in sorted_events:
        sessions = out.setdefault(user, [])
        # Start new session if no sessions exist or gap is strictly greater than `gap`
        if not sessions or t - sessions[-1][-1] > gap:
            sessions.append([t])
        else:
            sessions[-1].append(t)
    return out