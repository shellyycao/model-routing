def dedupe(xs):
    """Remove later duplicates while preserving first-occurrence order.

    Membership is tested with ``==`` against the output list (not a set),
    so unhashable values (e.g., lists, dicts) are supported.
    """
    out = []
    for item in xs:
        if item not in out:
            out.append(item)
    return out
