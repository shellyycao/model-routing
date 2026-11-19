def rolling_mean(xs, window, min_periods=1):
    if window <= 0:
        raise ValueError('window')
    if not 1 <= min_periods <= window:
        raise ValueError('min_periods')

    values = list(xs)
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        current = values[start:i + 1]
        if len(current) < min_periods:
            result.append(None)
        else:
            result.append(sum(current) / len(current))
    return result
