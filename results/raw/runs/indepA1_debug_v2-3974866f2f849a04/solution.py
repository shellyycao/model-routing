def allocate_stock(stock, requests):
    """Allocate stock to a sequence of requests.

    Args:
        stock (dict): Mapping of SKU to available quantity.
        requests (iterable): Iterable of (request_id, sku, qty) tuples.

    Returns:
        tuple: (fulfilled_ids, remaining_stock)
            fulfilled_ids – list of request IDs that were fully satisfied, in the
            order they were processed.
            remaining_stock – a new dict reflecting stock after allocations.
    """
    # Work on a copy so the original ``stock`` dict is never mutated.
    remaining = stock.copy()
    fulfilled = []
    seen_ids = set()

    for request_id, sku, qty in requests:
        # Ignore duplicate request IDs.
        if request_id in seen_ids:
            continue
        seen_ids.add(request_id)

        # Only consider positive quantities.
        if qty <= 0:
            continue

        # Allocate only if enough stock is available for the SKU.
        if remaining.get(sku, 0) >= qty:
            remaining[sku] -= qty
            fulfilled.append(request_id)

    return fulfilled, remaining
