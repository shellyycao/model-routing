def overlap_minutes(a, b):
    a_start, a_end = a
    b_start, b_end = b
    if a_end < a_start or b_end < b_start:
        raise ValueError("interval end must not be before start")
    return max(0, min(a_end, b_end) - max(a_start, b_start))