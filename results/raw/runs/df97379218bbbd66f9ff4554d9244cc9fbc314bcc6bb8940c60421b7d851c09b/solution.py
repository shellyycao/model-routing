def rotate(xs, k):
    if not xs:
        return []
    n = len(xs)
    k %= n
    # Rotate right by k: take last k elements, then the rest
    return xs[-k:] + xs[:-k] if k != 0 else list(xs)
