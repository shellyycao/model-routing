def paginate(items, size, cursor=None):
    if size <= 0:
        raise ValueError("size must be positive")
    start = 0 if cursor is None else int(cursor)
    if start < 0 or start > len(items):
        raise ValueError("invalid cursor")
    end = start + size
    page = items[start:end]
    next_cursor = str(end) if end < len(items) else None
    return page, next_cursor