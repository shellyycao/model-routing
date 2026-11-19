def rotate(xs, k):
    if not xs:
        return []
    n = len(xs)
    k %= n
    return xs[-k:] + xs[:-k]