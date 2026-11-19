def paginate(items, size, cursor=None):
    if size <= 0:
        raise ValueError('Size must be positive')
    if cursor is not None and not cursor.isdigit():
        raise ValueError('Invalid cursor')
    start = 0 if cursor is None else int(cursor)
    if start < 0 or start >= len(items):
        raise ValueError('Invalid cursor')
    end = start + size
    if end > len(items):
        end = None
    else:
        end = str(end)
    return list(items[start:end]), end