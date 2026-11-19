def paginate(items, size, cursor=None):
    if size <= 0: raise ValueError('size')
    try:
        start = 0 if cursor is None else int(cursor)
    except (ValueError, TypeError):
        raise ValueError('cursor')
    if cursor is not None and (int(cursor) < 0 or str(int(cursor)) != str(cursor).strip()):
        raise ValueError('cursor')
    end = min(start + size, len(items))
    next_cursor = str(end) if end < len(items) else None
    return list(items[start:end]), next_cursor
