def sessionize(events, gap):
    out = {}
    last = {}
    for user, t in sorted(events, key=lambda x: (x[0], x[1])):
        if user not in out:
            out[user] = [[t]]
        elif t - last[user] > gap:
            out[user].append([t])
        else:
            out[user][-1].append(t)
        last[user] = t
    return out
