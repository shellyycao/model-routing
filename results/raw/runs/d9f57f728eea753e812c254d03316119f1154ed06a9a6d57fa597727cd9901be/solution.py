def overlap_minutes(a, b):
    a_start, a_end = a
    b_start, b_end = b

    if a_end < a_start:
        raise ValueError("interval end must not be before start")
    if b_end < b_start:
        raise ValueError("interval end must not be before start")

    overlap_start = max(a_start, b_start)
    overlap_end = min(a_end, b_end)
    return max(0, overlap_end - overlap_start)
