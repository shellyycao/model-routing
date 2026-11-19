import os
import re
import json
import math
from datetime import datetime

import pandas as pd

# R1: tokens treated as missing (case-insensitive, after stripping)
MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

MONTHS_SHORT = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
MONTHS_FULL = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
    "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
}


def _make_date(y, m, d):
    try:
        return datetime(y, m, d).strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_order_date(value):
    """R3: accept exactly YYYY-MM-DD, MM/DD/YYYY, DD-Mon-YYYY, YYYY/MM/DD,
    'Month D, YYYY' (English month names, locale-independent)."""
    if value is None:
        return None
    s = value.strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return _make_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        # month first
        return _make_date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
    m = re.fullmatch(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", s)
    if m:
        month = MONTHS_SHORT.get(m.group(2).lower())
        return _make_date(int(m.group(3)), month, int(m.group(1))) if month else None
    m = re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", s)
    if m:
        return _make_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", s)
    if m:
        month = MONTHS_FULL.get(m.group(1).lower())
        return _make_date(int(m.group(3)), month, int(m.group(2))) if month else None
    return None


REGION_MAP = {
    "north": "North", "south": "South", "east": "East", "west": "West",
    "n": "North", "s": "South", "e": "East", "w": "West",
}


def parse_region(value):
    if value is None:
        return None
    return REGION_MAP.get(" ".join(value.lower().split()))


CATEGORY_MAP = {
    "electronics": "Electronics", "electronic": "Electronics",
    "clothing": "Clothing", "apparel": "Clothing",
    "home & garden": "Home & Garden", "home and garden": "Home & Garden",
    "home&garden": "Home & Garden",
    "sports": "Sports", "sport": "Sports",
    "books": "Books", "book": "Books",
}


def parse_category(value):
    if value is None:
        return None
    return CATEGORY_MAP.get(" ".join(value.lower().split()))


def parse_unit_price(value):
    """R6: strip '$', 'USD', ',' and surrounding spaces; must be 0 < v <= 5000."""
    if value is None:
        return None
    t = re.sub(r"usd", "", value, flags=re.IGNORECASE)
    t = t.replace("$", "").replace(",", "").strip()
    if not t:
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    if not math.isfinite(v) or v <= 0 or v > 5000:
        return None
    return v


def parse_quantity(value):
    """R7: numeric whole number in [1, 50], stored as int ('3.0' allowed)."""
    if value is None:
        return None
    try:
        v = float(value.strip())
    except ValueError:
        return None
    if not math.isfinite(v) or v != math.floor(v) or v < 1 or v > 50:
        return None
    return int(v)


def parse_discount(value):
    """R8: strip one trailing '%'; must be a number in [0, 100]."""
    if value is None:
        return None
    t = value.strip()
    if t.endswith("%"):
        t = t[:-1].strip()
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

    # R1: read every column as text; keep raw strings (disable pandas NA detection)
    df = pd.read_csv(os.path.join(input_dir, "raw.csv"), dtype=str, na_filter=False)
    df.columns = [str(c).strip() for c in df.columns]
    raw_rows = int(len(df))

    # strip whitespace from every value, then normalise missing tokens to None
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    df = df.apply(lambda col: col.map(lambda v: None if v.lower() in MISSING_TOKENS else v))

    summary = {"raw_rows": raw_rows}

    # R2: de-duplicate on order_id BEFORE any other row filter; keep first
    # occurrence in raw-file order. order_id is not nullable, so rows without
    # one cannot be kept.
    missing_oid = df["order_id"].isna()
    summary["dropped_missing_order_id"] = int(missing_oid.sum())
    df = df[~missing_oid]
    dup_mask = df["order_id"].duplicated(keep="first")
    summary["duplicate_order_id_removed"] = int(dup_mask.sum())
    df = df[~dup_mask].copy()

    # R3: order_date
    df["order_date"] = df["order_date"].map(parse_order_date)
    bad = df["order_date"].isna()
    summary["dropped_invalid_order_date"] = int(bad.sum())
    df = df[~bad].copy()

    # R4: region
    df["region"] = df["region"].map(parse_region)
    bad = df["region"].isna()
    summary["dropped_invalid_region"] = int(bad.sum())
    df = df[~bad].copy()

    # R5: product_category
    df["product_category"] = df["product_category"].map(parse_category)
    bad = df["product_category"].isna()
    summary["dropped_invalid_product_category"] = int(bad.sum())
    df = df[~bad].copy()

    # R6: unit_price
    df["unit_price"] = df["unit_price"].map(parse_unit_price)
    bad = df["unit_price"].isna()
    summary["dropped_invalid_unit_price"] = int(bad.sum())
    df = df[~bad].copy()
    df["unit_price"] = df["unit_price"].astype(float)

    # R7: quantity
    df["quantity"] = df["quantity"].map(parse_quantity)
    bad = df["quantity"].isna()
    summary["dropped_invalid_quantity"] = int(bad.sum())
    df = df[~bad].copy()
    df["quantity"] = df["quantity"].astype(int)

    # R8: discount_pct (missing -> 0, row kept; invalid -> drop)
    missing_disc = df["discount_pct"].isna()
    summary["discount_pct_missing_filled_zero"] = int(missing_disc.sum())
    df["discount_pct"] = df["discount_pct"].map(parse_discount)
    df.loc[missing_disc, "discount_pct"] = 0.0
    bad = df["discount_pct"].isna()
    summary["dropped_invalid_discount_pct"] = int(bad.sum())
    df = df[~bad].copy()
    df["discount_pct"] = df["discount_pct"].astype(float)

    # R9: customer_id (upper case; missing -> 'UNKNOWN', row kept)
    missing_cust = df["customer_id"].isna()
    summary["customer_id_missing_filled_unknown"] = int(missing_cust.sum())
    df["customer_id"] = df["customer_id"].map(lambda v: "UNKNOWN" if v is None else v.upper())

    # R10: revenue
    df["revenue"] = (df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)).round(2)

    # R11: final column selection/order, sort by order_id ascending, write CSV
    out_cols = ["order_id", "order_date", "customer_id", "region",
                "product_category", "quantity", "unit_price",
                "discount_pct", "revenue"]
    df = df[out_cols].sort_values("order_id", kind="stable").reset_index(drop=True)

    out_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(out_path, index=False)
    summary["cleaned_rows"] = int(len(df))

    with open(os.path.join(output_dir, "cleaning_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
