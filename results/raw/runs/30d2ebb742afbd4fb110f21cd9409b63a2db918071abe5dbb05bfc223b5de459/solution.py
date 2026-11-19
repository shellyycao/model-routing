def paginate(items, size, cursor=None):
    """Return (page, next_cursor) for the requested window of items.

    cursor is a zero-based start index encoded as a string; next_cursor is
    None once the end of items has been reached. Invalid cursors and
    nonpositive sizes raise ValueError.
    """
    if size <= 0:
        raise ValueError("size must be a positive integer")

    items = list(items)

    if cursor is None:
        start = 0
    else:
        try:
            start = int(cursor)
        except (TypeError, ValueError):
            raise ValueError("invalid cursor: %r" % (cursor,))
        if start < 0 or start > len(items):
            raise ValueError("invalid cursor: %r" % (cursor,))

    end = start + size
    page = items[start:end]
    next_cursor = str(end) if end < len(items) else None
    return page, next_cursor
