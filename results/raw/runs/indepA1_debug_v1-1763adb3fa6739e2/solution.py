def median(xs):
    if not xs:
        raise ValueError("empty")
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2:
        return s[mid]
    else:
        return (s[mid - 1] + s[mid]) / 2