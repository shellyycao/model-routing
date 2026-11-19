def sessionize(events, gap):
    out = {}
    last = {}
    for user, t in sorted(events):
        if user not in out:
            out[user] = [[]]
        if user in last and t - last[user] > gap:
            out[user].append([])
        out[user][-1].append(t)
        last[user] = t
    return out
