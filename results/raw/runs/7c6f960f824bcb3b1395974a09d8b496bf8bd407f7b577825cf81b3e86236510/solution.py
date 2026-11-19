def rolling_mean(xs, window, min_periods=1):
    '''Return trailing means, using None when a position has too few values.'''
    if not 1 <= min_periods <= window:
        raise ValueError('min_periods must satisfy 1 <= min_periods <= window')

    means = []
    for i in range(len(xs)):
        start = max(0, i - window + 1)
        values = xs[start:i + 1]
        if len(values) >= min_periods:
            means.append(sum(values) / len(values))
        else:
            means.append(None)
    return means
