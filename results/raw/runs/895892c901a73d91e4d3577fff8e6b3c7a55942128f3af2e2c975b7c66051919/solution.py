def paginate(items, size, cursor=None):
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise ValueError('size must be a positive integer')
    if cursor is None:
        start = 0
    else:
        if not isinstance(cursor, str):
            raise ValueError('cursor must be a zero-based start index string')
        try:
            start = int(cursor, 10)
        except ValueError:
            raise ValueError('cursor must be a zero-based start index string') from None
        if start < 0:
            raise ValueError('cursor out of range')
    try:
        item_count = len(items)
    except TypeError:
        items = list(items)
        item_count = len(items)
    if start > item_count:
        raise ValueError('cursor out of range')
    end = start + size
    page = list(items[start:end])
    next_cursor = None if end >= item_count else str(end)
    return page, next_cursor
