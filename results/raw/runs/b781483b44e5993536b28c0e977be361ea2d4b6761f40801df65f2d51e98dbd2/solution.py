def invoice_total(lines, discount_pct=0, tax_pct=0):
    subtotal = sum(row['qty'] * row['unit_price'] for row in lines)
    after_discount = subtotal * (1 - discount_pct / 100)
    total = after_discount * (1 + tax_pct / 100)
    return round(total, 2)
