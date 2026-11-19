def dedupe(xs):
    out = []
    seen = set()
    for item in reversed(xs):
        if item not in seen:
            seen.add(item)
            out.append(item)
    return list(reversed(out))