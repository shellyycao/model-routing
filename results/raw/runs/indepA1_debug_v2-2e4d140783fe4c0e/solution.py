def clamp(x, low, high):
    """Clamp *x* to the inclusive range [low, high].

    Raises:
        ValueError: If *low* is greater than *high*.
    """
    if low > high:
        raise ValueError("low must not be greater than high")
    return min(max(x, low), high)
