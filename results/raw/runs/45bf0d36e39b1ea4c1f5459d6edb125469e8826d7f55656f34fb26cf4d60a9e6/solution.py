def rotate(xs, k):
    xs = list(xs)
    n = len(xs)
    if n == 0:
        return []
    k %= n
    return xs[-k:] + xs[:-k]
