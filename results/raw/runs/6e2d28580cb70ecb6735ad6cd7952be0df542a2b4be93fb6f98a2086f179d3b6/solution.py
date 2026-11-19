def allocate_stock(stock, requests):
    remaining = dict(stock)
    fulfilled = []
    seen_request_ids = set()

    for request_id, sku, qty in requests:
        if request_id in seen_request_ids:
            continue
        seen_request_ids.add(request_id)

        if qty <= 0:
            continue
        if remaining.get(sku, 0) >= qty:
            remaining[sku] = remaining.get(sku, 0) - qty
            fulfilled.append(request_id)

    return fulfilled, remaining
