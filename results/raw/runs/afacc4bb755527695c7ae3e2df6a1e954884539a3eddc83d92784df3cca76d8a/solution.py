def dedupe(xs):
    """Remove later duplicates while preserving first-occurrence order.

    Uses equality comparisons instead of hashing, so unhashable values are supported.
    """
    kept = []
    for x in xs:
        if x not in kept:
            kept.append(x)
    return kept
