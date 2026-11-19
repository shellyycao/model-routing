def sessionize(events, gap):
    out = {}
    for user, t in sorted(events):
        sessions = out.setdefault(user, [])
        if not sessions or t - sessions[-1][-1] > gap:
            sessions.append([t])
        else:
            sessions[-1].append(t)
    return out
