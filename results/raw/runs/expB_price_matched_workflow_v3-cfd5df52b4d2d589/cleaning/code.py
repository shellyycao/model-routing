import os
import re
import json
import math
from datetime import datetime

import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

REGION_MAP = {
    "north": "North", "south": "South", "east": "East", "west": "West",
    "n": "North", "s": "South", "e": "East", "w": "West",
}

CATEGORY_MAP = {
    "electronics": "Electronics", "electronic": "Electronics",
    "clothing": "Clothing", "apparel": "Clothing",
    "home & garden": "Home & Garden", "home and garden": "Home & Garden",
    "home&garden": "Home & Garden",
    "sports": "Sports", "sport": "Sports",
    "books": "Books", "book": "Books",
}

# Exactly the five allowed order_date formats (R3).
DATE_PATTERNS = [
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "%Y-%m-%d"),
    (re.compile(r"^\d{2}/\d{2}/\d{4}$"), "%m/%d/%Y"),
    (re.compile(r"^\d{2}-[A-Za-z]{3}-\d{4}$"), "%d-%b-%Y"),
    (re.compile(r"^\d{4}/\d{2}/\d{2}$"), "%Y/%m/%d"),
    (re.compile(r"^[A-Za-z]+ \d{1,2}, \d{4}$"), "%B %d, %Y"),
]

OUTPUT_COLUMNS = [
    "order_id", "order_date", "customer_id", "region", "product_category",
    "quantity", "unit_price", "discount_pct", "revenue",
]


def clean_text(value):
    """R1: strip whitespace; map missing tokens (case-insensitive) to None."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    s = str(value).strip()
    if s.lower() in MISSING_TOKENS:
        return None
    return s


def parse_order_date(s):
    """R3: parse with exactly one allowed format; return YYYY-MM-DD or None."""
    for pattern, fmt in DATE_PATTERNS:
        if pattern.match(s):
            try:
                return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
            except ValueError:
                return None
    return None


def parse_unit_price(s):
    """R6: remove $ / USD / thousands separators; require 0 < price <= 5000."""
    t = s.replace("$", "").replace("USD", "").replace(",", "").strip()
    if not t:
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    if not math.isfinite(v) or v <= 0 or v > 5000:
        return None
    return v


def parse_quantity(s):
    """R7: numeric whole-number quantity in [1, 50]; values like '3.0' allowed."""
    try:
        v = float(s)
    except ValueError:
        return None
    if not math.isfinite(v) or not v.is_integer():
        return None
    q = int(v)
    if q < 1 or q > 50:
        return None
    return q


def parse_discount(s):
    """R8: missing -> 0; strip a trailing %; require 0 <= value <= 100."""
    if s is None:
        return 0.0
    t = s[:-1].strip() if s.endswith("%") else s
    try:
        v = float(t)
    except ValueError:
        return None
    if not math.isfinite(v) or v < 0 or v > 100:
        return None
    return v


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)

    raw_path = os.path.join(input_dir, "raw.csv")
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_filter=False)

    counts = {
        "duplicate_order_id_removed": 0,
        "dropped_missing_order_id": 0,
        "dropped_invalid_order_date": 0,
        "dropped_invalid_region": 0,
        "dropped_invalid_product_category": 0,
        "dropped_invalid_unit_price": 0,
        "dropped_invalid_quantity": 0,
        "dropped_invalid_discount_pct": 0,
        "discount_pct_missing_filled_with_0": 0,
        "customer_id_missing_filled_with_UNKNOWN": 0,
    }

    cleaned = []
    seen_order_ids = set()

    for record in df.to_dict("records"):
        # R1: strip whitespace and normalize missing tokens on every value.
        row = {k: clean_text(v) for k, v in record.items()}

        order_id = row.get("order_id")
        if order_id is None:
            counts["dropped_missing_order_id"] += 1
            continue
        # R2: remove duplicate order_ids BEFORE any other row filter;
        # keep the first occurrence in raw-file order.
        if order_id in seen_order_ids:
            counts["duplicate_order_id_removed"] += 1
            continue
        seen_order_ids.add(order_id)

        # R3: order_date
        od_raw = row.get("order_date")
        order_date = parse_order_date(od_raw) if od_raw is not None else None
        if order_date is None:
            counts["dropped_invalid_order_date"] += 1
            continue

        # R4: region
        rg_raw = row.get("region")
        region = REGION_MAP.get(rg_raw.lower()) if rg_raw is not None else None
        if region is None:
            counts["dropped_invalid_region"] += 1
            continue

        # R5: product_category
        pc_raw = row.get("product_category")
        category = CATEGORY_MAP.get(pc_raw.lower()) if pc_raw is not None else None
        if category is None:
            counts["dropped_invalid_product_category"] += 1
            continue

        # R6: unit_price
        up_raw = row.get("unit_price")
        unit_price = parse_unit_price(up_raw) if up_raw is not None else None
        if unit_price is None:
            counts["dropped_invalid_unit_price"] += 1
            continue

        # R7: quantity
        qt_raw = row.get("quantity")
        quantity = parse_quantity(qt_raw) if qt_raw is not None else None
        if quantity is None:
            counts["dropped_invalid_quantity"] += 1
            continue

        # R8: discount_pct
        dc_raw = row.get("discount_pct")
        if dc_raw is None:
            counts["discount_pct_missing_filled_with_0"] += 1
        discount = parse_discount(dc_raw)
        if discount is None:
            counts["dropped_invalid_discount_pct"] += 1
            continue

        # R9: customer_id
        cid_raw = row.get("customer_id")
        if cid_raw is None:
            counts["customer_id_missing_filled_with_UNKNOWN"] += 1
            customer_id = "UNKNOWN"
        else:
            customer_id = cid_raw.upper()

        # R10: revenue
        revenue = round(quantity * unit_price * (1 - discount / 100), 2)

        cleaned.append({
            "order_id": order_id,
            "order_date": order_date,
            "customer_id": customer_id,
            "region": region,
            "product_category": category,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount_pct": discount,
            "revenue": revenue,
        })

    out_df = pd.DataFrame(cleaned, columns=OUTPUT_COLUMNS)
    # R11: sort by order_id ascending; header row, no index column.
    out_df = out_df.sort_values("order_id", ascending=True).reset_index(drop=True)

    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    out_df.to_csv(cleaned_path, index=False)

    summary = {"raw_rows": int(len(df))}
    summary.update(counts)
    summary["cleaned_rows"] = int(len(out_df))

    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
