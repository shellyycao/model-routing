def clamp(x, low, high):
    if low > high:
        raise ValueError("low must not be greater than high")
    return min(max(x, low), high)
