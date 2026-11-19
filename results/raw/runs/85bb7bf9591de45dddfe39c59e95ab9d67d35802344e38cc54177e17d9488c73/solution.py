def paginate(items, size, cursor=None):
    if size <= 0: raise ValueError('size')
    try:
        start = 0 if cursor is None else int(cursor)
    except (ValueError, TypeError):
        raise ValueError('cursor')
    if cursor is not None and (int(cursor) < 0 or str(int(cursor)) != cursor):
        raise ValueError('cursor')
    end = min(start + size, len(items))
    return list(items[start:end]), (str(end) if end < len(items) else None)
