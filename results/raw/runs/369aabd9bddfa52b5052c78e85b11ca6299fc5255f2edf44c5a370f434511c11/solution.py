def rolling_mean(xs, window, min_periods=1):
    if window <= 0:
        raise ValueError('window must be positive')
    if not (1 <= min_periods <= window):
        raise ValueError('min_periods must satisfy 1 <= min_periods <= window')
    result = []
    for i in range(len(xs)):
        slice_ = xs[max(0, i - window + 1):i + 1]
        if len(slice_) < min_periods:
            result.append(None)
        else:
            result.append(sum(slice_) / len(slice_))
    return result
