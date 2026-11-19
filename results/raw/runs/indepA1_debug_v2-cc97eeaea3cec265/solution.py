def clamp(x, low, high):
    """Return *x* bounded inclusively between *low* and *high*.

    If *low* is greater than *high* a :class:`ValueError` is raised.
    """
    if low > high:
        raise ValueError('low must not be greater than high')
    # First limit *x* to the upper bound, then enforce the lower bound.
    return max(min(x, high), low)
