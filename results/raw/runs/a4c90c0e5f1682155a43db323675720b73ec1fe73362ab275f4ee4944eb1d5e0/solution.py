def invoice_total(lines, discount_pct=0, tax_pct=0):
    subtotal = sum(row['qty'] * row['unit_price'] for row in lines)
    discounted_total = subtotal * (1 - discount_pct / 100)
    taxed_total = discounted_total * (1 + tax_pct / 100)
    return round(taxed_total, 2)
