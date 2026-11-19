def rolling_mean(xs, window, min_periods=1):
    """Return one trailing-window mean per input position.

    The window for position i includes xs[i] and up to window - 1 prior
    values. If fewer than min_periods values are available, return None
    for that position.
    """
    if not 1 <= min_periods <= window:
        raise ValueError("min_periods must satisfy 1 <= min_periods <= window")

    values = list(xs)
    means = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        trailing = values[start:i + 1]
        if len(trailing) >= min_periods:
            means.append(sum(trailing) / len(trailing))
        else:
            means.append(None)
    return means
