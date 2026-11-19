def rolling_mean(xs, window, min_periods=1):
    if window <= 0:
        raise ValueError('window')
    if min_periods < 1 or min_periods > window:
        raise ValueError('min_periods')
    result = []
    for i in range(len(xs)):
        vals = xs[max(0, i - window + 1):i + 1]
        if len(vals) < min_periods:
            result.append(None)
        else:
            result.append(sum(vals) / len(vals))
    return result
