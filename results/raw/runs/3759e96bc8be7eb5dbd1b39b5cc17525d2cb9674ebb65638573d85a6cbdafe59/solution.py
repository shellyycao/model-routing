def dedupe(xs):
    result = []
    for x in xs:
        if not any(x is seen or x == seen for seen in result):
            result.append(x)
    return result
