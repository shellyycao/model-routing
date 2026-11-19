def rotate(xs, k):
    if not xs: return []
    k %= len(xs)
    if k < 0:
        k += len(xs)
    return list(xs[-k:] + xs[:-k])