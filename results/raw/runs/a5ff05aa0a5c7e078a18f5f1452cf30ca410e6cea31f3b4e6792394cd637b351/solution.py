def rolling_mean(xs, window, min_periods=1):
    if not (1 <= min_periods <= window):
        raise ValueError("min_periods must satisfy 1 <= min_periods <= window")
    result = []
    for i in range(len(xs)):
        start = max(0, i - window + 1)
        window_slice = xs[start:i+1]
        if len(window_slice) >= min_periods:
            result.append(sum(window_slice) / len(window_slice))
        else:
            result.append(None)
    return result