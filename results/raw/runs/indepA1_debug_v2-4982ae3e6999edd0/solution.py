def sessionize(events, gap):
    sorted_events = sorted(events, key=lambda x: (x[0], x[1]))
    out = {}
    for user, t in sorted_events:
        sessions = out.setdefault(user, [])
        if not sessions or t - sessions[-1][-1] > gap:
            sessions.append([t])
        else:
            sessions[-1].append(t)
    return out
