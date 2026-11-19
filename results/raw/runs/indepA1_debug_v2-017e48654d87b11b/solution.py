def rolling_mean(xs, window, min_periods=1):
    if not (1 <= min_periods <= window):
        raise ValueError('min_periods must be between 1 and window')
    if window <= 0:
        raise ValueError('window must be greater than 0')
    return [sum(xs[max(0, i-window+1):i+1])/max(len(xs[max(0, i-window+1):i+1]), 1) if len(xs[max(0, i-window+1):i+1]) >= min_periods else None for i in range(len(xs))]