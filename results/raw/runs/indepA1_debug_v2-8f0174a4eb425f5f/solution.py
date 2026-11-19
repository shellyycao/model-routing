def rolling_mean(xs, window, min_periods=1):
    """Return a list of rolling means for *xs* using a trailing window.

    For each position *i* in *xs*, the window consists of the elements
    ``xs[max(0, i - window + 1) : i + 1]``.  If the number of elements in the
    window is at least *min_periods*, the mean of those elements is returned;
    otherwise ``None`` is placed in the output list.

    Parameters
    ----------
    xs : sequence of numbers
        Input data.
    window : int
        Size of the trailing window; must be positive.
    min_periods : int, optional
        Minimum number of observations required to compute a mean.  Must satisfy
        ``1 <= min_periods <= window``.  Defaults to ``1``.
    """
    if window <= 0:
        raise ValueError('window must be positive')
    if not (1 <= min_periods <= window):
        raise ValueError('min_periods must satisfy 1 <= min_periods <= window')

    result = []
    for i in range(len(xs)):
        start = max(0, i - window + 1)
        count = i - start + 1
        if count < min_periods:
            result.append(None)
        else:
            window_slice = xs[start:i + 1]
            result.append(sum(window_slice) / count)
    return result