def dedupe(xs):
    """Return a list with duplicates removed, keeping the first occurrence of each element.

    The function works with any iterable and supports unhashable items because it
    uses linear ``in`` checks rather than a set or dict.
    """
    out = []
    for item in xs:
        if item not in out:
            out.append(item)
    return out
