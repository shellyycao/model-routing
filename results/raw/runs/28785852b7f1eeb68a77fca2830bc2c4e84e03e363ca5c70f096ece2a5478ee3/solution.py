def rolling_mean(xs, window, min_periods=1):
    if not (1 <= min_periods <= window):
        raise ValueError("require 1 <= min_periods <= window")
    result = []
    for i in range(len(xs)):
        start = max(0, i - window + 1)
        vals = xs[start:i + 1]
        if len(vals) < min_periods:
            result.append(None)
        else:
            result.append(sum(vals) / len(vals))
    return result
