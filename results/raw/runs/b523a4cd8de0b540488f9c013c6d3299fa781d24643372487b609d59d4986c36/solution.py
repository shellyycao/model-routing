def sessionize(events, gap):
    out = {}
    last = {}
    for user, t in sorted(events, key=lambda x: (x[0], x[1])):
        if user not in out:
            out[user] = [[]]
            last[user] = None
        if last[user] is not None and t - last[user] > gap:
            out[user].append([])
        out[user][-1].append(t)
        last[user] = t
    return out