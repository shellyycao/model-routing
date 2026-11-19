def moving_average(xs, k):
    if k <= 0 or k > len(xs):
        return []
    return [sum(xs[i:i + k]) / k for i in range(len(xs) - k + 1)]
