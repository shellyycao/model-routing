def clamp(x, low, high):
    if low > high:
        raise ValueError("low must be less than or equal to high")
    return min(max(x, low), high)
