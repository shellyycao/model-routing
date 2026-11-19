def rotate(xs, k):
    """Return a new list rotated right by *k* positions.
    A negative *k* rotates left. An empty input returns an empty list.
    """
    # Return early for empty input to avoid ZeroDivisionError on modulo.
    if not xs:
        return []
    n = len(xs)
    # Convert any k (positive, negative, or larger than n) to an equivalent
    # right‑rotation amount in the range [0, n).
    r = k % n
    # Perform the right rotation using slicing. When r == 0 the slices produce
    # the original list, satisfying the "no change" case.
    return list(xs[-r:] + xs[:-r])
