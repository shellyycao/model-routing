import os
import re
import json
import math
from datetime import datetime

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

# R1: values treated as missing (case-insensitive, after stripping)
MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

# R3: exactly these five date formats are accepted
DATE_FORMATS = (
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY, English 3-letter month abbreviation
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY, full English month name
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

OUTPUT_COLUMNS = [
    "order_id", "order_date", "customer_id", "region", "product_category",
    "quantity", "unit_price", "discount_pct", "revenue",
]


def _is_nan(v):
    return isinstance(v, float) and math.isnan(v)


def _norm(v):
    """Lower-case and collapse internal whitespace for case-insensitive lookups."""
    return " ".join(str(v).strip().lower().split())


def parse_order_date(v):
    """Return the date as YYYY-MM-DD, or None if missing/unparseable."""
    if v is None or _is_nan(v):
        return None
    s = str(v).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def map_region(v):
    if v is None or _is_nan(v):
        return None
    return REGION_MAP.get(_norm(v))


def map_category(v):
    if v is None or _is_nan(v):
        return None
    return CATEGORY_MAP.get(_norm(v))


def parse_unit_price(v):
    if v is None or _is_nan(v):
        return None
    s = str(v).replace("$", "").replace(",", "")
    s = re.sub(r"(?i)usd", "", s).strip()
    if not s:
        return None
    try:
        x = float(s)
    except ValueError:
        return None
    if math.isnan(x) or math.isinf(x) or x <= 0 or x > 5000:
        return None
    return x


def parse_quantity(v):
    if v is None or _is_nan(v):
        return None
    try:
        x = float(str(v).strip())
    except ValueError:
        return None
    if math.isnan(x) or math.isinf(x) or not x.is_integer():
        return None
    q = int(x)
    if q < 1 or q > 50:
        return None
    return q


def parse_discount(v):
    """Missing means no discount -> 0.0. Return None only for invalid values (row dropped)."""
    if v is None or _is_nan(v):
        return 0.0
    s = str(v).strip()
    if s.endswith("%"):
        s = s[:-1].strip()
    if not s:
        return None
    try:
        x = float(s)
    except ValueError:
        return None
    if math.isnan(x) or math.isinf(x) or x < 0 or x > 100:
        return None
    return x


def apply_rule(df, column, func, summary, key):
    """Map a column through func; drop rows where func returns None; count drops."""
    mapped = df[column].map(func)
    keep = mapped.notna()
    summary[key] = int((~keep).sum())
    out = df.loc[keep].copy()
    out[column] = mapped[keep]
    return out


def main():
    summary = {}

    # R1: read every column as text, strip whitespace, normalize missing tokens
    raw_path = os.path.join(INPUT_DIR, "raw.csv")
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_filter=False)
    summary["raw_rows"] = int(len(df))
    df = df.apply(lambda col: col.astype(str).str.strip())
    for col in df.columns:
        df[col] = df[col].map(lambda v: np.nan if v.lower() in MISSING_TOKENS else v)

    # R2: remove duplicate order_id rows FIRST, keeping the first raw-file occurrence
    before = len(df)
    df = df.drop_duplicates(subset="order_id", keep="first")
    summary["r2_duplicate_order_id_rows_removed"] = int(before - len(df))

    # order_id is not nullable in the output schema
    before = len(df)
    df = df[df["order_id"].notna()]
    summary["missing_order_id_rows_dropped"] = int(before - len(df))

    # R3-R8: parse / canonicalize / validate, dropping invalid rows, in order
    df = apply_rule(df, "order_date", parse_order_date, summary, "r3_invalid_order_date_rows_dropped")
    df = apply_rule(df, "region", map_region, summary, "r4_invalid_region_rows_dropped")
    df = apply_rule(df, "product_category", map_category, summary, "r5_invalid_product_category_rows_dropped")
    df = apply_rule(df, "unit_price", parse_unit_price, summary, "r6_invalid_unit_price_rows_dropped")
    df = apply_rule(df, "quantity", parse_quantity, summary, "r7_invalid_quantity_rows_dropped")
    df = apply_rule(df, "discount_pct", parse_discount, summary, "r8_invalid_discount_pct_rows_dropped")

    # R9: upper-case customer_id; missing -> 'UNKNOWN' (row kept)
    summary["r9_missing_customer_id_filled_unknown"] = int(df["customer_id"].isna().sum())
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN").astype(str).str.strip().str.upper()

    # R10: revenue = quantity * unit_price * (1 - discount_pct/100), rounded to 2 decimals
    df["quantity"] = df["quantity"].astype(int)
    df["unit_price"] = df["unit_price"].astype(float)
    df["discount_pct"] = df["discount_pct"].astype(float)
    df["revenue"] = (df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)).round(2)

    # R11: exact column set/order, sorted by order_id ascending, header row, no index
    out = df[OUTPUT_COLUMNS].copy()
    out = out.sort_values("order_id", kind="mergesort").reset_index(drop=True)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cleaned_path = os.path.join(OUTPUT_DIR, "cleaned.csv")
    out.to_csv(cleaned_path, index=False)
    summary["cleaned_rows"] = int(len(out))

    summary_path = os.path.join(OUTPUT_DIR, "cleaning_summary.json")
    with open(summary_path, "w") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
