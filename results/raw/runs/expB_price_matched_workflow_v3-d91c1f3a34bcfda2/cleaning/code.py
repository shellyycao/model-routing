import json
import math
import os
import re
from datetime import datetime

import numpy as np
import pandas as pd

# R1: values treated as missing (compared case-insensitively, after stripping)
MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

# R3: exactly these date formats are accepted
DATE_FORMATS = (
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY, e.g. 05-Mar-2024
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY, e.g. March 5, 2024
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
    s = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_unit_price(value):
    s = str(value).strip()
    s = re.sub(r"(?i)usd", "", s)  # remove the substring 'USD' (any case)
    s = s.replace("$", "").replace(",", "").strip()
    if not s:
        return None
    try:
        price = float(s)
    except ValueError:
        return None
    if not math.isfinite(price) or price <= 0 or price > 5000:
        return None
    return price


def parse_quantity(value):
    s = str(value).strip()
    try:
        number = float(s)
    except ValueError:
        return None
    if not math.isfinite(number) or not number.is_integer():
        return None
    qty = int(number)
    if qty < 1 or qty > 50:
        return None
    return qty


def parse_discount(value):
    """Return (discount_pct, is_valid); a missing value means no discount (0)."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0.0, True
    s = str(value).strip()
    if s.endswith("%"):
        s = s[:-1].strip()
    if not s:
        return None, False
    try:
        disc = float(s)
    except ValueError:
        return None, False
    if not math.isfinite(disc) or disc < 0 or disc > 100:
        return None, False
    return disc, True


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # R1: read every column as text, strip whitespace, normalise missing tokens to NaN.
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False, na_filter=False)
    raw_rows = int(len(df))
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        df[col] = df[col].map(
            lambda v: np.nan if str(v).strip().lower() in MISSING_TOKENS else str(v).strip()
        )

    summary = {"raw_rows": raw_rows}

    # R2: deduplicate on order_id (keep first occurrence in raw-file order) BEFORE any
    # other row filter. Rows with no order_id cannot satisfy the schema and are dropped.
    missing_order_id = int(df["order_id"].isna().sum())
    df = df[df["order_id"].notna()]
    rows_before = len(df)
    df = df.drop_duplicates(subset="order_id", keep="first")
    summary["r2_missing_order_id_dropped"] = missing_order_id
    summary["r2_duplicate_order_id_dropped"] = int(rows_before - len(df))

    # R3: order_date - parse with the five allowed formats, drop unparseable/missing.
    parsed = df["order_date"].map(parse_order_date)
    keep = parsed.notna()
    summary["r3_invalid_order_date_dropped"] = int((~keep).sum())
    df = df.loc[keep].copy()
    df["order_date"] = parsed.loc[keep]

    # R4: region - case-insensitive mapping incl. single-letter abbreviations.
    mapped = df["region"].map(lambda v: REGION_MAP.get(str(v).strip().lower()))
    keep = mapped.notna()
    summary["r4_invalid_region_dropped"] = int((~keep).sum())
    df = df.loc[keep].copy()
    df["region"] = mapped.loc[keep]

    # R5: product_category - case-insensitive mapping incl. listed variants.
    mapped = df["product_category"].map(lambda v: CATEGORY_MAP.get(str(v).strip().lower()))
    keep = mapped.notna()
    summary["r5_invalid_product_category_dropped"] = int((~keep).sum())
    df = df.loc[keep].copy()
    df["product_category"] = mapped.loc[keep]

    # R6: unit_price - strip '$', 'USD', ',' then parse; drop missing/non-numeric/<=0/>5000.
    mapped = df["unit_price"].map(parse_unit_price)
    keep = mapped.notna()
    summary["r6_invalid_unit_price_dropped"] = int((~keep).sum())
    df = df.loc[keep].copy()
    df["unit_price"] = mapped.loc[keep].astype(float)

    # R7: quantity - numeric whole number in [1, 50], stored as integer.
    mapped = df["quantity"].map(parse_quantity)
    keep = mapped.notna()
    summary["r7_invalid_quantity_dropped"] = int((~keep).sum())
    df = df.loc[keep].copy()
    df["quantity"] = mapped.loc[keep].astype(int)

    # R8: discount_pct - strip trailing '%'; missing means 0; must be in [0, 100].
    mapped = df["discount_pct"].map(parse_discount)
    keep = mapped.map(lambda t: t[1])
    summary["r8_invalid_discount_pct_dropped"] = int((~keep).sum())
    df = df.loc[keep].copy()
    df["discount_pct"] = mapped.loc[keep].map(lambda t: t[0]).astype(float)

    # R9: customer_id - upper case; missing becomes 'UNKNOWN' (row kept).
    missing_customer = int(df["customer_id"].isna().sum())
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN").map(lambda v: str(v).strip().upper())
    summary["r9_missing_customer_id_set_to_unknown"] = missing_customer

    # R10: revenue = quantity * unit_price * (1 - discount_pct/100), rounded to 2 decimals.
    df["revenue"] = (
        df["quantity"].astype(float) * df["unit_price"] * (1.0 - df["discount_pct"] / 100.0)
    ).round(2)

    # R11: exact column order, sorted by order_id ascending, header row, no index.
    df = df[OUTPUT_COLUMNS].sort_values("order_id", ascending=True, kind="mergesort")
    df = df.reset_index(drop=True)
    df.to_csv(cleaned_path, index=False)

    summary["cleaned_rows"] = int(len(df))
    summary["rows_dropped_total"] = raw_rows - int(len(df))

    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print(f"cleaning done: {raw_rows} raw rows -> {len(df)} cleaned rows")


if __name__ == "__main__":
    main()
