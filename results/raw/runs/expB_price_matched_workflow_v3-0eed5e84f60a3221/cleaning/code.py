import json
import os
import re
from datetime import datetime

import numpy as np
import pandas as pd

MISSING_MARKERS = {"", "na", "n/a", "null", "none", "-"}

DATE_FORMATS = (
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY (English 3-letter month)
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY (full English month name)
)

REGION_MAP = {
    "north": "North", "south": "South", "east": "East", "west": "West",
    "n": "North", "s": "South", "e": "East", "w": "West",
}

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


def parse_order_date(value):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def parse_region(value):
    return REGION_MAP.get(value.strip().lower())


def parse_category(value):
    key = re.sub(r"\s+", " ", value.strip().lower())
    return CATEGORY_MAP.get(key)


def parse_unit_price(value):
    text = re.sub(r"(?i)usd", "", value)
    text = text.replace("$", "").replace(",", "").strip()
    try:
        number = float(text)
    except ValueError:
        return None
    if not np.isfinite(number) or number <= 0 or number > 5000:
        return None
    return number


def parse_quantity(value):
    try:
        number = float(value)
    except ValueError:
        return None
    if not np.isfinite(number) or not number.is_integer():
        return None
    number = int(number)
    if number < 1 or number > 50:
        return None
    return number


def parse_discount(value):
    text = value.strip()
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        number = float(text)
    except ValueError:
        return None
    if not np.isfinite(number) or number < 0 or number > 100:
        return None
    return number


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)

    raw_path = os.path.join(input_dir, "raw.csv")

    # R1: read every column as text; no automatic NA conversion
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_filter=False)
    summary = {"raw_rows": int(len(df))}

    # R1: strip whitespace from every value; normalize missing markers (case-insensitive)
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].map(lambda v: np.nan if v.lower() in MISSING_MARKERS else v)

    # R2: drop duplicate order_id BEFORE any other row filter, keep first in raw-file order
    before = len(df)
    df = df.drop_duplicates(subset="order_id", keep="first")
    summary["duplicates_removed"] = int(before - len(df))

    # order_id is not nullable in the output schema
    before = len(df)
    df = df[df["order_id"].notna()]
    summary["dropped_missing_order_id"] = int(before - len(df))

    # R3: order_date -> one of the five allowed formats, written as YYYY-MM-DD
    parsed = df["order_date"].map(lambda v: parse_order_date(v) if pd.notna(v) else None)
    valid = parsed.notna()
    summary["dropped_invalid_order_date"] = int((~valid).sum())
    df = df[valid].copy()
    df["order_date"] = parsed[valid]

    # R4: region -> North/South/East/West (single-letter abbreviations allowed)
    parsed = df["region"].map(lambda v: parse_region(v) if pd.notna(v) else None)
    valid = parsed.notna()
    summary["dropped_invalid_region"] = int((~valid).sum())
    df = df[valid].copy()
    df["region"] = parsed[valid]

    # R5: product_category -> one of the five canonical categories (variants mapped)
    parsed = df["product_category"].map(lambda v: parse_category(v) if pd.notna(v) else None)
    valid = parsed.notna()
    summary["dropped_invalid_product_category"] = int((~valid).sum())
    df = df[valid].copy()
    df["product_category"] = parsed[valid]

    # R6: unit_price -> strip '$', 'USD', ','; must be a number in (0, 5000]
    parsed = df["unit_price"].map(lambda v: parse_unit_price(v) if pd.notna(v) else None)
    valid = parsed.notna()
    summary["dropped_invalid_unit_price"] = int((~valid).sum())
    df = df[valid].copy()
    df["unit_price"] = parsed[valid].astype(float)

    # R7: quantity -> numeric, whole number, 1..50, stored as int
    parsed = df["quantity"].map(lambda v: parse_quantity(v) if pd.notna(v) else None)
    valid = parsed.notna()
    summary["dropped_invalid_quantity"] = int((~valid).sum())
    df = df[valid].copy()
    df["quantity"] = parsed[valid].astype(int)

    # R8: discount_pct -> strip trailing '%'; missing means 0; must be 0..100
    summary["discount_missing_set_to_zero"] = int(df["discount_pct"].isna().sum())
    parsed = df["discount_pct"].map(lambda v: 0.0 if pd.isna(v) else parse_discount(v))
    valid = parsed.notna()
    summary["dropped_invalid_discount_pct"] = int((~valid).sum())
    df = df[valid].copy()
    df["discount_pct"] = parsed[valid].astype(float)

    # R9: customer_id -> upper case; missing becomes 'UNKNOWN' (row kept)
    summary["customer_id_missing_set_unknown"] = int(df["customer_id"].isna().sum())
    df["customer_id"] = df["customer_id"].map(
        lambda v: "UNKNOWN" if pd.isna(v) else v.upper()
    )

    # R10: revenue = quantity * unit_price * (1 - discount_pct / 100), rounded to 2 decimals
    df["revenue"] = (
        df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)
    ).round(2)

    # R11: exact column order, sorted by order_id ascending, header row, no index
    df = df[OUTPUT_COLUMNS].sort_values("order_id", kind="mergesort").reset_index(drop=True)

    out_csv = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(out_csv, index=False)
    summary["cleaned_rows"] = int(len(df))

    out_json = os.path.join(output_dir, "cleaning_summary.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print(f"Cleaned {summary['cleaned_rows']} of {summary['raw_rows']} rows -> {out_csv}")


if __name__ == "__main__":
    main()
