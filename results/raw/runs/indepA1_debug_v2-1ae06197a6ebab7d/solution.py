def paginate(items, size, cursor=None):
    if size <= 0: raise ValueError('size must be positive')
    if cursor is not None and (int(cursor) < 0 or int(cursor) >= len(items)):
        raise ValueError('invalid cursor')
    start = 0 if cursor is None else int(cursor)
    end = min(start + size, len(items))
    return list(items[start:end]), (str(end) if end < len(items) else None)