def paginate(items, size, cursor=None):
    """Return a page of items and a cursor for the next page.

    Args:
        items (Iterable): The collection to paginate.
        size (int): Positive number of items per page.
        cursor (str, optional): Zero‑based start index as a string. If ``None`` pagination starts at 0.

    Returns:
        tuple: (page, next_cursor) where ``page`` is a list of up to ``size`` items and
        ``next_cursor`` is a string representing the start index for the next page, or ``None``
        when the end of the collection has been reached.

    Raises:
        ValueError: If ``size`` is not a positive integer, if ``cursor`` is not a string
        representing a non‑negative integer, or if the cursor is out of range.
    """
    # Validate size
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")

    # Materialise items as a list for slicing
    seq = list(items)
    n = len(seq)

    # Determine start index from cursor
    if cursor is None:
        start = 0
    else:
        if not isinstance(cursor, str):
            raise ValueError("cursor must be a string")
        try:
            start = int(cursor)
        except Exception:
            raise ValueError("cursor must be a string representing an integer")
        if start < 0 or start > n:
            raise ValueError("cursor out of range")

    end = start + size
    page = seq[start:end]
    next_cursor = str(end) if end < n else None
    return page, next_cursor
