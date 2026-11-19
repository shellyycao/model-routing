def invoice_total(lines, discount_pct=0, tax_pct=0):
    """
    Calculate the total invoice amount.

    Parameters
    ----------
    lines : iterable of dict
        Each dict must contain 'qty' and 'unit_price' keys.
    discount_pct : float, optional
        Discount percentage to apply to the subtotal (default 0).
    tax_pct : float, optional
        Tax percentage to apply after discount (default 0).

    Returns
    -------
    float
        Total amount rounded to two decimal places.
    """
    # 1. Compute the raw subtotal.
    subtotal = sum(row['qty'] * row['unit_price'] for row in lines)
    # 2. Apply discount first.
    discounted = subtotal * (1 - discount_pct / 100)
    # 3. Apply tax to the discounted amount.
    total = discounted * (1 + tax_pct / 100)
    # 4. Round only the final result.
    return round(total, 2)
