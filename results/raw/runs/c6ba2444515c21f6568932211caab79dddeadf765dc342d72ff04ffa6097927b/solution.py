def overlap_minutes(a, b):
    if a[1] < a[0] or b[1] < b[0]:
        raise ValueError('interval')
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))
