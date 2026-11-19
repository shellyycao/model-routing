def invoice_total(lines, discount_pct=0, tax_pct=0):
    """Calculate the total invoice amount.

    * `lines` is an iterable of mappings with keys ``'qty'`` and ``'unit_price'``.
    * `discount_pct` is the discount percentage (e.g., ``10`` for 10%).
    * `tax_pct` is the tax percentage (e.g., ``5`` for 5%).

    The function sums ``qty * unit_price`` for all lines, applies the discount,
    then applies tax, and finally rounds the *final* result to two decimal places.
    """
    # 1. Compute raw subtotal without any intermediate rounding.
    subtotal = sum(row['qty'] * row['unit_price'] for row in lines)

    # 2. Apply discount (percentage expressed as a fraction).
    discounted = subtotal * (1 - discount_pct / 100)

    # 3. Apply tax on the discounted amount.
    total = discounted * (1 + tax_pct / 100)

    # 4. Round only the final total to two decimal places.
    return round(total, 2)
