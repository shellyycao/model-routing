def paginate(items, size, cursor=None):
    if size <= 0:
        raise ValueError('size')
    if cursor is None:
        start = 0
    else:
        try:
            start = int(cursor)
        except (TypeError, ValueError):
            raise ValueError('cursor')
        if start < 0 or start > len(items):
            raise ValueError('cursor')
    end = min(start + size, len(items))
    next_cursor = str(end) if end < len(items) else None
    return list(items[start:end]), next_cursor
