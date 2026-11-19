def chunks(xs, size):
    if size <= 0: raise ValueError('size must be greater than 0')
    return [xs[i:i+size] for i in range(0, len(xs), size)]