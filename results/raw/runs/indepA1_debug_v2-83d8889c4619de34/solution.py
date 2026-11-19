def allocate_stock(stock, requests):
    remaining = stock.copy()
    fulfilled = []
    seen_requests = set()
    for rid, sku, qty in requests:
        if rid in seen_requests or qty <= 0 or remaining.get(sku, 0) < qty:
            continue
        seen_requests.add(rid)
        remaining[sku] -= qty
        fulfilled.append(rid)
    return fulfilled, remaining