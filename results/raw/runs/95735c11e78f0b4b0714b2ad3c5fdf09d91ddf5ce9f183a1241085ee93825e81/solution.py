def allocate_stock(stock, requests):
    remaining = dict(stock)
    seen = set()
    fulfilled = []
    for request_id, sku, qty in requests:
        if request_id in seen:
            continue
        seen.add(request_id)
        if qty <= 0:
            continue
        available = remaining.get(sku, 0)
        if available >= qty:
            remaining[sku] = available - qty
            fulfilled.append(request_id)
    return fulfilled, remaining
