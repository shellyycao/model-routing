def allocate_stock(stock, requests):
    remaining = dict(stock)
    seen = set()
    fulfilled = []
    for rid, sku, qty in requests:
        if rid in seen:
            continue
        if qty > 0 and remaining.get(sku, 0) >= qty:
            remaining[sku] -= qty
            fulfilled.append(rid)
            seen.add(rid)
    return fulfilled, remaining