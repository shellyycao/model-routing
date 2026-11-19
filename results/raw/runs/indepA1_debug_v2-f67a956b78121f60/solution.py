def allocate_stock(stock, requests):
    remaining = dict(stock)
    fulfilled = []
    seen_ids = set()
    for rid, sku, qty in requests:
        if rid in seen_ids:
            continue
        seen_ids.add(rid)
        if qty > 0 and remaining.get(sku, 0) >= qty:
            remaining[sku] -= qty
            fulfilled.append(rid)
    return fulfilled, remaining
