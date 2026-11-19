def overlap_minutes(a, b):
    """Return the length of overlap (in minutes) between two half‑open intervals.

    Each interval is a tuple (start, end) where start and end are integers
    representing minutes. The interval includes *start* and excludes *end*.
    Raises ValueError if an interval has ``end < start``. Touching intervals
    (where the end of one equals the start of the other) have zero overlap.
    """
    # Basic validation: intervals must be two‑element sequences
    if len(a) != 2 or len(b) != 2:
        raise TypeError("Intervals must be 2‑element sequences")
    # Reject intervals where end is less than start (half‑open intervals allow start == end)
    if a[1] < a[0] or b[1] < b[0]:
        raise ValueError("interval end must not be less than start")
    # Compute overlap for half‑open intervals: max(0, min(end1, end2) - max(start1, start2))
    overlap = min(a[1], b[1]) - max(a[0], b[0])
    return overlap if overlap > 0 else 0