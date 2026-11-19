def clamp(x, low, high):
    if low > high: raise ValueError('bounds')
    return max(min(x, high), low)
