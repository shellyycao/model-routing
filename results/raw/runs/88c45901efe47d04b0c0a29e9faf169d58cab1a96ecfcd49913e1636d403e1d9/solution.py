def paginate(items, size, cursor=None):
    if size <= 0: raise ValueError('size')
    try:
        start = 0 if cursor is None else int(cursor)
    except ValueError:
        raise ValueError('cursor')
    if start < 0 or start > len(items): raise ValueError('cursor')
    end = min(start + size, len(items))
    return list(items[start:end]), (str(end) if end < len(items) else None)