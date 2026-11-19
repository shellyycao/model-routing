def allocate_stock(stock, requests):
    """Allocate stock to requests.

    Args:
        stock (dict): Mapping of SKU to available quantity.
        requests (iterable): Iterable of (request_id, sku, qty) tuples.

    Returns:
        tuple: (list of fulfilled request_ids in order, remaining stock dict).
    """
    # Work on a copy so the original stock is not mutated
    remaining = dict(stock)
    seen = set()
    fulfilled = []

    for request_id, sku, qty in requests:
        # Ignore duplicate request IDs
        if request_id in seen:
            continue
        seen.add(request_id)

        # Only consider positive quantities
        if qty <= 0:
            continue

        # Fulfil the request only if enough stock is available
        if remaining.get(sku, 0) >= qty:
            remaining[sku] = remaining.get(sku, 0) - qty
            fulfilled.append(request_id)

    return fulfilled, remaining