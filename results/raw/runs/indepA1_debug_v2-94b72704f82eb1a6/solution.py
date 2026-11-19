def paginate(items, size, cursor=None):
    """
    Return a page of items and a cursor for the next page.

    Parameters
    ----------
    items : iterable
        Collection of items to paginate.
    size : int
        Number of items per page. Must be a positive integer.
    cursor : str or None, optional
        Zero‑based start index encoded as a string. If None, pagination starts
        from the beginning.

    Returns
    -------
    tuple (list, str|None)
        The slice of items for the requested page and the cursor for the next
        page, or None when there are no more items.

    Raises
    ------
    ValueError
        If ``size`` is not positive, or if ``cursor`` is not a valid zero‑based
        index string.
    """
    # Validate size – must be a positive integer
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size")

    # Ensure we have a sequence that supports slicing
    seq = list(items)

    # Resolve start index from cursor
    if cursor is None:
        start = 0
    else:
        if not isinstance(cursor, str):
            raise ValueError("cursor")
        try:
            start = int(cursor)
        except Exception:
            raise ValueError("cursor")
        # Cursor must be within the bounds of the sequence
        if start < 0 or start > len(seq):
            raise ValueError("cursor")

    # Compute slice boundaries
    end = min(start + size, len(seq))

    # Extract the page
    page = seq[start:end]

    # Determine the next cursor (None when at the end)
    next_cursor = str(end) if end < len(seq) else None

    return page, next_cursor
