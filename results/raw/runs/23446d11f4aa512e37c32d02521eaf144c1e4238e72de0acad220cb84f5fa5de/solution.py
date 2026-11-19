def dedupe(xs):
    out = []
    for item in xs:
        if item not in out:
            out.append(item)
    return out
