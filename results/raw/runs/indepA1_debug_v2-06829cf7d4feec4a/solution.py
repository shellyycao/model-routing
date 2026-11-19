def rolling_mean(xs, window, min_periods=1):
    if not (1 <= min_periods <= window):
        raise ValueError('min_periods must be between 1 and window')
    result = []
    for i in range(len(xs)):
        start = max(0, i - window + 1)
        subset = xs[start:i + 1]
        if len(subset) >= min_periods:
            result.append(sum(subset) / len(subset))
        else:
            result.append(None)
    return result