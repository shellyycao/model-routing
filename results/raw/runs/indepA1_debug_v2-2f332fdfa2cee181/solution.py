def dedupe(xs):
    seen = []
    result = []
    for x in xs:
        try:
            if x not in seen:
                seen.append(x)
                result.append(x)
        except TypeError:
            if x not in seen:
                seen.append(x)
                result.append(x)
    return result
