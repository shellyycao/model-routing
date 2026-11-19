"""Cleaning stage for the retail_sales project.

Reads raw.csv from INPUT_DIR, applies cleaning rules R1-R11 and writes
cleaned.csv plus cleaning_summary.json to OUTPUT_DIR.
"""

import os
import re
import json
from datetime import datetime

import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

DATE_FORMATS = (
    "%Y-%m-%d",    # YYYY-MM-DD
    "%m/%d/%Y",    # MM/DD/YYYY (month first)
    "%d-%b-%Y",    # DD-Mon-YYYY (e.g. 05-Mar-2024)
    "%Y/%m/%d",    # YYYY/MM/DD
    "%B %d, %Y",   # Month D, YYYY (e.g. March 5, 2024)
)

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

FINAL_COLUMNS = [
    "order_id", "order_date", "customer_id", "region", "product_category",
    "quantity", "unit_price", "discount_pct", "revenue",
]


def normalize_ws(value):
    return " ".join(str(value).split())


def parse_order_date(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def map_region(value):
    if pd.isna(value):
        return None
    return REGION_MAP.get(normalize_ws(value).lower())


def map_category(value):
    if pd.isna(value):
        return None
    return CATEGORY_MAP.get(normalize_ws(value).lower())


def parse_unit_price(value):
    if pd.isna(value):
        return None
    text = str(value).replace("$", "").replace(",", "")
    text = re.sub(r"usd", "", text, flags=re.IGNORECASE).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_quantity(value):
    if pd.isna(value):
        return None
    try:
        number = float(str(value).strip())
    except ValueError:
        return None
    if not number.is_integer():
        return None
    return int(number)


def parse_discount(value):
    if pd.isna(value):
        return 0.0  # a missing discount_pct means no discount
    text = str(value).strip()
    if text.endswith("%"):
        text = text[:-1].strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    summary = {}

    # R1: read every column as text, strip whitespace, standardise missing values.
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False, na_filter=False)
    summary["raw_rows"] = int(len(df))
    for column in df.columns:
        stripped = df[column].astype(str).str.strip()
        df[column] = stripped.mask(stripped.str.lower().isin(MISSING_TOKENS), pd.NA)

    # R2: drop duplicate order_id rows (keep first in raw-file order) BEFORE any other row filter.
    has_order_id = df["order_id"].notna()
    duplicate_mask = has_order_id & df.duplicated(subset=["order_id"], keep="first")
    summary["duplicates_removed"] = int(duplicate_mask.sum())
    df = df.loc[~duplicate_mask].copy()

    # R3: order_date - parse with the five allowed formats; drop missing/unparseable.
    parsed_dates = df["order_date"].map(parse_order_date)
    bad = parsed_dates.isna()
    summary["dropped_invalid_order_date"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["order_date"] = parsed_dates.loc[df.index].map(lambda d: d.isoformat())

    # R4: region - normalise case/abbreviations; drop missing/unmapped.
    mapped = df["region"].map(map_region)
    bad = mapped.isna()
    summary["dropped_invalid_region"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["region"] = mapped.loc[df.index]

    # R5: product_category - normalise case/variants; drop missing/unmapped.
    mapped = df["product_category"].map(map_category)
    bad = mapped.isna()
    summary["dropped_invalid_product_category"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["product_category"] = mapped.loc[df.index]

    # R6: unit_price - strip $/USD/commas, parse number; drop missing/non-numeric/<=0/>5000.
    parsed = df["unit_price"].map(parse_unit_price)
    bad = parsed.isna() | (parsed <= 0) | (parsed > 5000)
    summary["dropped_invalid_unit_price"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["unit_price"] = parsed.loc[df.index].astype(float)

    # R7: quantity - numeric whole numbers in [1, 50]; store as integer.
    parsed = df["quantity"].map(parse_quantity)
    bad = parsed.isna() | (parsed < 1) | (parsed > 50)
    summary["dropped_invalid_quantity"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["quantity"] = parsed.loc[df.index].astype(int)

    # R8: discount_pct - strip trailing %, parse number; missing -> 0; drop non-numeric/<0/>100.
    parsed = df["discount_pct"].map(parse_discount)
    bad = parsed.isna() | (parsed < 0) | (parsed > 100)
    summary["dropped_invalid_discount_pct"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["discount_pct"] = parsed.loc[df.index].astype(float)

    # R9: customer_id - upper-case; missing -> 'UNKNOWN' (row kept).
    summary["customer_id_set_unknown"] = int(df["customer_id"].isna().sum())
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN").astype(str).str.upper()

    # R10: revenue = quantity * unit_price * (1 - discount_pct/100), rounded to 2 decimals.
    df["revenue"] = (
        df["quantity"] * df["unit_price"] * (1.0 - df["discount_pct"] / 100.0)
    ).round(2)

    # R11: final column order, sort by order_id ascending, write CSV (header, no index).
    df = df[FINAL_COLUMNS].sort_values("order_id", kind="mergesort").reset_index(drop=True)
    df.to_csv(cleaned_path, index=False)

    summary["cleaned_rows"] = int(len(df))
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
