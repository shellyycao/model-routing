def running_total(xs):
    out=[]; total=0
    for value in xs:
        total += value; out.append(total)
    return out
