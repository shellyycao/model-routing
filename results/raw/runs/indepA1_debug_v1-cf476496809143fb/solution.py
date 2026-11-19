def merge_intervals(intervals):
    # Work on a sorted copy so the original list is not modified
    sorted_intervals = sorted((list(iv) for iv in intervals), key=lambda x: x[0])
    out = []
    for s, e in sorted_intervals:
        # Merge when intervals overlap or touch (s <= previous end)
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out