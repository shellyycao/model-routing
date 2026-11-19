def sessionize(events, gap):
    out = {}
    for user, t in sorted(events, key=lambda x: (x[0], x[1])):
        if user not in out:
            out[user] = [[]]
        if out[user] and t - out[user][-1][-1] > gap:
            out[user].append([])
        out[user][-1].append(t)
    return out