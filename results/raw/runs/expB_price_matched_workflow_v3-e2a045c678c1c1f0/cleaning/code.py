import os
import re
import json
from datetime import date

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

MONTH_ABBR = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
              "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
MONTH_FULL = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
              "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
              "november": 11, "december": 12}

REGION_MAP = {"north": "North", "n": "North",
              "south": "South", "s": "South",
              "east": "East", "e": "East",
              "west": "West", "w": "West"}

CATEGORY_MAP = {"electronics": "Electronics", "electronic": "Electronics",
                "clothing": "Clothing", "apparel": "Clothing",
                "home & garden": "Home & Garden",
                "home and garden": "Home & Garden",
                "home&garden": "Home & Garden",
                "sports": "Sports", "sport": "Sports",
                "books": "Books", "book": "Books"}


def make_date(y, m, d):
    try:
        return date(int(y), int(m), int(d)).isoformat()
    except ValueError:
        return None


def parse_order_date(s):
    """Parse exactly the five allowed formats; return ISO 'YYYY-MM-DD' or None."""
    if s is None or pd.isna(s):
        return None
    s = s.strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)          # YYYY-MM-DD
    if m:
        return make_date(m.group(1), m.group(2), m.group(3))
    m = re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", s)          # YYYY/MM/DD
    if m:
        return make_date(m.group(1), m.group(2), m.group(3))
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)          # MM/DD/YYYY (month first)
    if m:
        return make_date(m.group(3), m.group(1), m.group(2))
    m = re.fullmatch(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", s)      # DD-Mon-YYYY
    if m:
        mon = MONTH_ABBR.get(m.group(2).lower())
        return None if mon is None else make_date(m.group(3), mon, m.group(1))
    m = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", s)   # Month D, YYYY
    if m:
        mon = MONTH_FULL.get(m.group(1).lower())
        return None if mon is None else make_date(m.group(3), mon, m.group(2))
    return None


def clean_region(s):
    if s is None or pd.isna(s):
        return None
    return REGION_MAP.get(s.lower())


def clean_category(s):
    if s is None or pd.isna(s):
        return None
    return CATEGORY_MAP.get(s.lower())


def clean_unit_price(s):
    if s is None or pd.isna(s):
        return None
    t = re.sub(r"(?i)usd", "", s)
    t = t.replace("$", "").replace(",", "").strip()
    if t == "":
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    if not np.isfinite(v) or v <= 0 or v > 5000:
        return None
    return float(v)


def clean_quantity(s):
    if s is None or pd.isna(s):
        return None
    try:
        v = float(str(s))
    except ValueError:
        return None
    if not np.isfinite(v) or not v.is_integer() or v < 1 or v > 50:
        return None
    return int(v)


def clean_discount(s):
    if s is None or pd.isna(s):
        return 0.0  # missing discount means no discount; row is kept
    t = s.strip()
    if t.endswith("%"):
        t = t[:-1].strip()
    if t == "":
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    if not np.isfinite(v) or v < 0 or v > 100:
        return None
    return float(v)


def apply_rule(df, col, func):
    """Apply a per-value cleaning function; None means drop the row."""
    results = [func(x) for x in df[col]]
    keep = [r is not None for r in results]
    dropped = int(len(results) - sum(keep))
    out = df.loc[keep].copy()
    out[col] = [r for r, k in zip(results, keep) if k]
    return out, dropped


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # R1: read every column as text, strip whitespace, normalise missing tokens.
    raw_path = os.path.join(INPUT_DIR, "raw.csv")
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False,
                     na_filter=False, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)
        df[col] = df[col].map(
            lambda x: pd.NA if (isinstance(x, str) and x.lower() in MISSING_TOKENS) else x
        )

    summary = {"raw_rows": int(len(df))}

    # R2: remove duplicate order_id rows FIRST (keep first occurrence in raw order).
    dup_mask = df["order_id"].notna() & df["order_id"].duplicated(keep="first")
    summary["duplicates_removed"] = int(dup_mask.sum())
    df = df.loc[~dup_mask].copy()

    # order_id must not be null in the output schema.
    miss_oid = df["order_id"].isna()
    summary["dropped_missing_order_id"] = int(miss_oid.sum())
    df = df.loc[~miss_oid].copy()

    # R3-R7, R8: sequential per-column rules.
    df, summary["dropped_invalid_order_date"] = apply_rule(df, "order_date", parse_order_date)
    df, summary["dropped_invalid_region"] = apply_rule(df, "region", clean_region)
    df, summary["dropped_invalid_product_category"] = apply_rule(df, "product_category", clean_category)
    df, summary["dropped_invalid_unit_price"] = apply_rule(df, "unit_price", clean_unit_price)
    df, summary["dropped_invalid_quantity"] = apply_rule(df, "quantity", clean_quantity)

    summary["missing_discount_pct_set_to_zero"] = int(df["discount_pct"].isna().sum())
    df, summary["dropped_invalid_discount_pct"] = apply_rule(df, "discount_pct", clean_discount)

    # R9: customer_id upper case; missing -> 'UNKNOWN'.
    summary["missing_customer_id_set_to_UNKNOWN"] = int(df["customer_id"].isna().sum())
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN").astype(str).str.upper()

    # Enforce numeric dtypes.
    df["quantity"] = df["quantity"].astype(int)
    df["unit_price"] = df["unit_price"].astype(float)
    df["discount_pct"] = df["discount_pct"].astype(float)

    # R10: revenue = quantity * unit_price * (1 - discount_pct/100), rounded to 2 dp.
    df["revenue"] = (df["quantity"] * df["unit_price"]
                     * (1.0 - df["discount_pct"] / 100.0)).round(2)

    # R11: exact columns, sorted by order_id ascending, header row, no index.
    df = df.sort_values("order_id", kind="mergesort")
    out = df[["order_id", "order_date", "customer_id", "region",
              "product_category", "quantity", "unit_price",
              "discount_pct", "revenue"]]
    out.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)

    summary["cleaned_rows"] = int(len(out))
    with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
