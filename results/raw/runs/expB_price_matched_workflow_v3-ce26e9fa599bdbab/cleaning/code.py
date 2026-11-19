import json
import math
import os
import re
from datetime import datetime

import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

DATE_FORMATS = (
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY, English 3-letter month (e.g. 05-Mar-2024)
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY, full English month name (e.g. March 5, 2024)
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


def norm_key(value):
    """Lowercase and collapse internal whitespace for case-insensitive lookups."""
    return " ".join(str(value).lower().split())


def is_missing(value):
    return value is None or str(value).strip().lower() in MISSING_TOKENS


def parse_date(value):
    if value is None:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_unit_price(value):
    if value is None:
        return None
    text = value.replace("$", "").replace(",", "")
    text = re.sub(r"usd", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", "", text)
    try:
        number = float(text)
    except ValueError:
        return None
    if not math.isfinite(number) or number <= 0 or number > 5000:
        return None
    return number


def parse_quantity(value):
    if value is None:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    if not math.isfinite(number) or not number.is_integer():
        return None
    if number < 1 or number > 50:
        return None
    return int(number)


def parse_discount(value):
    if value is None:
        return 0.0  # missing discount means no discount
    text = value.strip()
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        number = float(text)
    except ValueError:
        return None
    if not math.isfinite(number) or number < 0 or number > 100:
        return None
    return number


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)

    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # R1: read every column as text, strip whitespace, normalize missing tokens.
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_filter=False)
    raw_rows = int(len(df))
    for col in df.columns:
        df[col] = df[col].map(lambda v: None if is_missing(v) else str(v).strip())

    # R2: remove duplicate order_id rows BEFORE any other row filter; keep first in raw-file order.
    dup_mask = df["order_id"].notna() & df.duplicated(subset=["order_id"], keep="first")
    duplicates_removed = int(dup_mask.sum())
    df = df.loc[~dup_mask].copy()

    # R3: order_date - parse with exactly the five allowed formats; drop missing/unparseable.
    df["order_date"] = df["order_date"].map(parse_date)
    dropped_order_date = int(df["order_date"].isna().sum())
    df = df.loc[df["order_date"].notna()].copy()

    # R4: region - case-insensitive mapping incl. single-letter abbreviations.
    df["region"] = df["region"].map(lambda v: REGION_MAP.get(norm_key(v)) if v is not None else None)
    dropped_region = int(df["region"].isna().sum())
    df = df.loc[df["region"].notna()].copy()

    # R5: product_category - case-insensitive mapping incl. known variants.
    df["product_category"] = df["product_category"].map(lambda v: CATEGORY_MAP.get(norm_key(v)) if v is not None else None)
    dropped_product_category = int(df["product_category"].isna().sum())
    df = df.loc[df["product_category"].notna()].copy()

    # R6: unit_price - strip '$', 'USD', ',' and spaces; numeric; 0 < price <= 5000.
    df["unit_price"] = df["unit_price"].map(parse_unit_price)
    dropped_unit_price = int(df["unit_price"].isna().sum())
    df = df.loc[df["unit_price"].notna()].copy()

    # R7: quantity - numeric whole number in [1, 50], stored as integer.
    df["quantity"] = df["quantity"].map(parse_quantity)
    dropped_quantity = int(df["quantity"].isna().sum())
    df = df.loc[df["quantity"].notna()].copy()

    # R8: discount_pct - drop trailing '%', numeric in [0, 100]; missing -> 0.
    discount_missing = int(df["discount_pct"].isna().sum())
    df["discount_pct"] = df["discount_pct"].map(parse_discount)
    dropped_discount_pct = int(df["discount_pct"].isna().sum())
    df = df.loc[df["discount_pct"].notna()].copy()

    # R9: customer_id - upper case; missing -> 'UNKNOWN' (row kept).
    customer_missing = int(df["customer_id"].isna().sum())
    df["customer_id"] = df["customer_id"].map(lambda v: "UNKNOWN" if v is None else v.upper())

    # R10: revenue = quantity * unit_price * (1 - discount_pct / 100), rounded to 2 decimals.
    df["revenue"] = (
        df["quantity"].astype(float)
        * df["unit_price"].astype(float)
        * (1 - df["discount_pct"].astype(float) / 100)
    ).round(2)

    # R11: exact column set/order, sort by order_id ascending, write CSV with header, no index.
    df = df[OUTPUT_COLUMNS].sort_values("order_id", ascending=True, kind="mergesort")
    df.to_csv(cleaned_path, index=False)

    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": int(len(df)),
        "duplicates_removed": duplicates_removed,
        "dropped_invalid_order_date": dropped_order_date,
        "dropped_invalid_region": dropped_region,
        "dropped_invalid_product_category": dropped_product_category,
        "dropped_invalid_unit_price": dropped_unit_price,
        "dropped_invalid_quantity": dropped_quantity,
        "dropped_invalid_discount_pct": dropped_discount_pct,
        "discount_pct_missing_set_to_zero": discount_missing,
        "customer_id_missing_set_to_unknown": customer_missing,
    }
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
