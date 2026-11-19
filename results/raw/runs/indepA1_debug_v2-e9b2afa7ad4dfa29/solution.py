def overlap_minutes(a, b):
    """Return the length of overlap (in minutes) between two half‑open intervals.

    Each interval is a tuple (start, end) where ``start`` is inclusive and ``end``
    is exclusive. The function validates that ``end`` is not less than ``start``
    for either interval and raises ``ValueError`` if this condition is violated.
    Touching intervals (where the end of one equals the start of the other) are
    considered to have zero overlap.
    """
    # Validate interval ordering
    if a[1] < a[0] or b[1] < b[0]:
        raise ValueError("Interval end must be greater than or equal to start")

    # Compute the overlap using half‑open interval semantics
    overlap_start = max(a[0], b[0])
    overlap_end = min(a[1], b[1])
    overlap = overlap_end - overlap_start

    # If intervals do not intersect, overlap will be negative; clamp to zero
    return max(overlap, 0)
