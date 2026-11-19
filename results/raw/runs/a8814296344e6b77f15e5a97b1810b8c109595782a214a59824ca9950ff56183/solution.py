def rotate(xs, k):
    if not xs:
        return []
    n = len(xs)
    k %= n
    return list(xs[n - k:] + xs[:n - k])
