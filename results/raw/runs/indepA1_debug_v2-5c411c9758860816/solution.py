def running_total(xs):
    """Return a list of cumulative sums of *xs*.

    Each element in the returned list is the sum of all elements up to and
    including the corresponding element in *xs*.  The function works for
    integers, floats, or a mixture of both, and returns an empty list when
    *xs* is empty.
    """
    out = []
    total = 0
    for value in xs:
        total += value
        out.append(total)
    return out
