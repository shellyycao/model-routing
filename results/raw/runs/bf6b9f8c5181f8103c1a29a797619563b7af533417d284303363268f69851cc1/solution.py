def rolling_mean(xs, window, min_periods=1):
    if window <= 0:
        raise ValueError('window')
    if min_periods < 1:
        raise ValueError('min_periods')
    if min_periods > window:
        raise ValueError('min_periods')
    result = []
    for i in range(len(xs)):
        window_vals = xs[max(0, i - window + 1):i + 1]
        if len(window_vals) < min_periods:
            result.append(None)
        else:
            result.append(sum(window_vals) / len(window_vals))
    return result
