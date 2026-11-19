def paginate(items, size, cursor=None):
    if size <= 0:
        raise ValueError("size must be positive")
    start = 0 if cursor is None else int(cursor)
    if start < 0:
        raise ValueError("cursor must be non-negative")
    end = start + size
    page = items[start:end]
    next_cursor = None if end >= len(items) else str(end)
    return page, next_cursor