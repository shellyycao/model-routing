def rotate(xs, k):
    if not xs:
        return []
    k %= len(xs)
    return list(xs[-k:] + xs[:-k]) if k != 0 else list(xs)
