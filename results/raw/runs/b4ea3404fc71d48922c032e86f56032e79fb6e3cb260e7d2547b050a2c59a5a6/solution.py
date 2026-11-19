def invoice_total(lines, discount_pct=0, tax_pct=0):
    subtotal = sum(row['qty'] * row['unit_price'] for row in lines)
    return round(subtotal * (1 - discount_pct / 100) * (1 + tax_pct / 100), 2)