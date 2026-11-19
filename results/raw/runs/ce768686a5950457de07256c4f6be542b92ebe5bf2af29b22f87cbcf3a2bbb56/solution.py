def paginate(items, size, cursor=None):
    if size <= 0:
        raise ValueError("size must be positive")
    if cursor is None:
        start = 0
    else:
        try:
            start = int(cursor)
        except (ValueError, TypeError):
            raise ValueError("invalid cursor")
        if start < 0 or start > len(items):
            raise ValueError("invalid cursor")
    end = start + size
    page = list(items[start:end])
    next_cursor = None if end >= len(items) else str(end)
    return page, next_cursor
