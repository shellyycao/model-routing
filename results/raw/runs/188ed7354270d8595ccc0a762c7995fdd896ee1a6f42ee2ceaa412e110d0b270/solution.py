def dedupe(xs):
    seen = []
    result = []
    for x in xs:
        if x not in seen:
            seen.append(x)
            result.append(x)
    return result
