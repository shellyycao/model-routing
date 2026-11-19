def rolling_mean(xs, window, min_periods=1):
    """
    Compute a rolling (trailing) mean of the sequence ``xs``.

    Parameters
    ----------
    xs : sequence of numbers
        Input data.
    window : int
        Size of the trailing window (must be >= 1).
    min_periods : int, optional
        Minimum number of observations in the window required to produce a
        result. If the window contains fewer than ``min_periods`` values,
        ``None`` is returned for that position. Must satisfy 1 <= min_periods <= window.

    Returns
    -------
    list
        List of rolling means (float) or ``None`` where the requirement is not met.
    """
    # Validate arguments
    if not isinstance(window, int) or window < 1:
        raise ValueError("window must be a positive integer")
    if not isinstance(min_periods, int) or min_periods < 1:
        raise ValueError("min_periods must be a positive integer")
    if min_periods > window:
        raise ValueError("min_periods must be less than or equal to window")

    result = []
    for i in range(len(xs)):
        # inclusive start index of the trailing window
        start = max(0, i - window + 1)
        count = i - start + 1  # actual number of elements in the window
        if count < min_periods:
            result.append(None)
        else:
            window_sum = sum(xs[start:i + 1])
            result.append(window_sum / count)
    return result
