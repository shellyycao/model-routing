def rolling_mean(xs, window, min_periods=1):
    if window <= 0:
        raise ValueError('window must be positive')
    if not (1 <= min_periods <= window):
        raise ValueError('min_periods must satisfy 1 <= min_periods <= window')
    result = []
    for i in range(len(xs)):
        segment = xs[max(0, i - window + 1):i + 1]
        if len(segment) >= min_periods:
            result.append(sum(segment) / len(segment))
        else:
            result.append(None)
    return result
