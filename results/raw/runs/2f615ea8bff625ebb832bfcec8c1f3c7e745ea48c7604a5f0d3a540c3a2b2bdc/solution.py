def allocate_stock(stock, requests):
    remaining = stock.copy()
    fulfilled = []
    seen_ids = set()
    for rid, sku, qty in requests:
        if rid in seen_ids:
            continue
        if qty > 0 and remaining.get(sku, 0) >= qty:
            remaining[sku] -= qty
            fulfilled.append(rid)
            seen_ids.add(rid)
    return fulfilled, remaining