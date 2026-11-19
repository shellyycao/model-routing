def rotate(xs, k):
    """Return a new list rotated right by *k* positions.
    Negative *k* rotates left. Empty input returns an empty list.
    """
    if not xs:
        return []
    k %= len(xs)
    return xs[-k:] + xs[:-k]
