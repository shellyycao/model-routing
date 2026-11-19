import json
import math
import os
import re
from datetime import datetime

import pandas as pd

# R1: tokens treated as missing (compared case-insensitively after stripping).
MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

# R3: the only accepted order_date formats, tried in this order.
DATE_FORMATS = [
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY, e.g. 05-Mar-2024
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY, e.g. March 5, 2024
]

# R4: region mapping (case-insensitive), incl. single-letter abbreviations.
REGION_MAP = {
    "north": "North", "n": "North",
    "south": "South", "s": "South",
    "east": "East", "e": "East",
    "west": "West", "w": "West",
}

# R5: product_category mapping (case-insensitive), incl. allowed variants.
CATEGORY_MAP = {
    "electronics": "Electronics",
    "electronic": "Electronics",
    "clothing": "Clothing",
    "apparel": "Clothing",
    "home & garden": "Home & Garden",
    "home and garden": "Home & Garden",
    "home&garden": "Home & Garden",
    "sports": "Sports",
    "sport": "Sports",
    "books": "Books",
    "book": "Books",
}

OUTPUT_COLUMNS = [
    "order_id", "order_date", "customer_id", "region", "product_category",
    "quantity", "unit_price", "discount_pct", "revenue",
]


def normalise(value):
    """R1: strip whitespace; map missing tokens to None."""
    if value is None:
        return None
    v = str(value).strip()
    return None if v.lower() in MISSING_TOKENS else v


def parse_date(value):
    """R3: parse with exactly the allowed formats; return YYYY-MM-DD or None."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_number(text):
    """Parse a finite float; return None if not a valid number."""
    try:
        num = float(text)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(num):
        return None
    return num


def clean_unit_price(value):
    """R6: strip 'USD', '$', ',' and surrounding spaces, then parse."""
    s = re.sub(r"usd", "", value, flags=re.IGNORECASE)
    s = s.replace("$", "").replace(",", "").strip()
    if s == "":
        return None
    return parse_number(s)


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    raw_path = os.path.join(input_dir, "raw.csv")

    # R1: read every column as text; disable pandas' own NA detection so that
    # missing-value handling follows R1 exactly.
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_filter=False)
    summary = {"raw_rows": int(len(df))}

    records = [
        {col: normalise(val) for col, val in row.items()}
        for row in df.to_dict("records")
    ]

    # R2: drop duplicate order_id rows FIRST, keeping the first raw-file occurrence.
    seen_ids = set()
    deduped = []
    duplicates_removed = 0
    for rec in records:
        oid = rec.get("order_id")
        key = oid if oid is not None else "<MISSING_ORDER_ID>"
        if key in seen_ids:
            duplicates_removed += 1
            continue
        seen_ids.add(key)
        deduped.append(rec)
    summary["duplicates_removed"] = duplicates_removed

    counts = {
        "dropped_bad_order_date": 0,
        "dropped_bad_region": 0,
        "dropped_bad_product_category": 0,
        "dropped_bad_unit_price": 0,
        "dropped_bad_quantity": 0,
        "dropped_bad_discount_pct": 0,
        "discount_pct_missing_set_to_zero": 0,
        "customer_id_missing_set_to_unknown": 0,
    }

    cleaned = []
    for rec in deduped:
        # R3: order_date
        raw_date = rec.get("order_date")
        parsed_date = parse_date(raw_date) if raw_date is not None else None
        if parsed_date is None:
            counts["dropped_bad_order_date"] += 1
            continue

        # R4: region
        raw_region = rec.get("region")
        region = REGION_MAP.get(raw_region.lower()) if raw_region is not None else None
        if region is None:
            counts["dropped_bad_region"] += 1
            continue

        # R5: product_category
        raw_cat = rec.get("product_category")
        category = CATEGORY_MAP.get(raw_cat.lower()) if raw_cat is not None else None
        if category is None:
            counts["dropped_bad_product_category"] += 1
            continue

        # R6: unit_price
        raw_price = rec.get("unit_price")
        price = clean_unit_price(raw_price) if raw_price is not None else None
        if price is None or price <= 0 or price > 5000:
            counts["dropped_bad_unit_price"] += 1
            continue

        # R7: quantity
        raw_qty = rec.get("quantity")
        qty_num = parse_number(raw_qty) if raw_qty is not None else None
        if qty_num is None or not qty_num.is_integer() or qty_num < 1 or qty_num > 50:
            counts["dropped_bad_quantity"] += 1
            continue
        quantity = int(qty_num)

        # R8: discount_pct
        raw_disc = rec.get("discount_pct")
        if raw_disc is None:
            discount = 0.0
            counts["discount_pct_missing_set_to_zero"] += 1
        else:
            s = raw_disc.strip()
            if s.endswith("%"):
                s = s[:-1].strip()
            disc = parse_number(s) if s != "" else None
            if disc is None or disc < 0 or disc > 100:
                counts["dropped_bad_discount_pct"] += 1
                continue
            discount = float(disc)

        # R9: customer_id
        raw_cust = rec.get("customer_id")
        if raw_cust is None:
            customer_id = "UNKNOWN"
            counts["customer_id_missing_set_to_unknown"] += 1
        else:
            customer_id = raw_cust.upper()

        # R10: revenue
        revenue = round(quantity * price * (1 - discount / 100), 2)

        cleaned.append({
            "order_id": rec.get("order_id"),
            "order_date": parsed_date,
            "customer_id": customer_id,
            "region": region,
            "product_category": category,
            "quantity": quantity,
            "unit_price": price,
            "discount_pct": discount,
            "revenue": revenue,
        })

    summary.update(counts)

    # R11: exact column order, sorted by order_id ascending, header, no index.
    out_df = pd.DataFrame(cleaned, columns=OUTPUT_COLUMNS)
    out_df = out_df.sort_values("order_id", ascending=True, kind="stable").reset_index(drop=True)
    summary["cleaned_rows"] = int(len(out_df))

    os.makedirs(output_dir, exist_ok=True)
    out_df.to_csv(os.path.join(output_dir, "cleaned.csv"), index=False)

    with open(os.path.join(output_dir, "cleaning_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("raw_rows={raw} cleaned_rows={clean}".format(
        raw=summary["raw_rows"], clean=summary["cleaned_rows"]))


if __name__ == "__main__":
    main()
