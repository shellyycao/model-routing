def chunks(xs, size):
    if size <= 0:
        raise ValueError('size')
    # iterate over the list in steps of `size`, including a possible short final chunk
    return [xs[i:i+size] for i in range(0, len(xs), size)]
