def paginate(items, size, cursor=None):
    """Return (page, next_cursor) for a page of `items`.

    `cursor` is a zero-based start index encoded as a string; None starts
    at the beginning. `next_cursor` is the cursor for the following page,
    or None once the end of `items` has been reached. Nonpositive sizes
    and invalid cursors raise ValueError.
    """
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise ValueError("size must be a positive integer")

    if cursor is None:
        start = 0
    else:
        if not isinstance(cursor, str):
            raise ValueError(f"invalid cursor: {cursor!r}")
        try:
            start = int(cursor)
        except ValueError:
            raise ValueError(f"invalid cursor: {cursor!r}") from None
        if start < 0:
            raise ValueError(f"invalid cursor: {cursor!r}")

    data = list(items)
    end = start + size
    page = data[start:end]
    next_cursor = str(end) if end < len(data) else None
    return page, next_cursor
