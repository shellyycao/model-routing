def running_total(xs):
    total = 0
    out = []
    for value in xs:
        total += value
        out.append(total)
    return out
