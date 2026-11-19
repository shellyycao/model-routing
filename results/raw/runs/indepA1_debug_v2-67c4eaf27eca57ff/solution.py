def chunks(xs, size):
    """Return consecutive chunks of *xs* with length *size*.

    The final chunk may be shorter than *size* if the length of ``xs``
    is not a multiple of ``size``. ``xs`` is not mutated.

    Args:
        xs (list): The list to split.
        size (int): Desired chunk size; must be a positive integer.

    Returns:
        list[list]: A list containing the chunked sub‑lists.

    Raises:
        ValueError: If ``size`` is less than or equal to zero.
    """
    if size <= 0:
        raise ValueError("size must be a positive integer")
    return [xs[i:i + size] for i in range(0, len(xs), size)]
