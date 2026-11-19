def overlap_minutes(a, b):
    if a[1] <= a[0] or b[1] <= b[0]:
        raise ValueError('interval')
    overlap_start = max(a[0], b[0])
    overlap_end = min(a[1], b[1])
    if overlap_start >= overlap_end:
        return 0
    return overlap_end - overlap_start