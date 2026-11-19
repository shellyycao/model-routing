def sessionize(events, gap):
    out = {}
    last = None
    last_user = None
    for user, t in sorted(events, key=lambda x: (x[0], x[1])):
        if user not in out:
            out[user] = [[]]
        if last is not None and user == last_user and t - last > gap:
            out[user].append([])
        out[user][-1].append(t)
        last = t
        last_user = user
    return out