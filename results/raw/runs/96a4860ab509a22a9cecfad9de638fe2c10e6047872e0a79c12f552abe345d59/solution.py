def sessionize(events, gap):
    sessions = {}
    last_by_user = {}
    for user, t in sorted(events, key=lambda e: (e[0], e[1])):
        if user not in sessions:
            sessions[user] = [[]]
        elif t - last_by_user[user] > gap:
            sessions[user].append([])
        sessions[user][-1].append(t)
        last_by_user[user] = t
    return sessions
