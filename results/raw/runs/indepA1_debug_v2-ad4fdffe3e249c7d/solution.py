def dedupe(xs):
    """Return a list with duplicates removed, preserving the first occurrence order.

    This implementation works for any iterable, including those containing
    unhashable items (e.g., lists, dicts). It does not rely on ``set`` which
    would both lose ordering and raise ``TypeError`` for unhashable elements.
    """
    result = []
    for x in xs:
        if x not in result:
            result.append(x)
    return result
