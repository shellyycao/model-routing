#!/usr/bin/env python3
"""Cleaning stage (retail_sales): cleans raw.csv into cleaned.csv per rules R1-R11."""

import json
import os
import re
from datetime import datetime

import numpy as np
import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

DATE_FORMATS = [
    (re.compile(r"^\d{4}-\d{1,2}-\d{1,2}$"), "%Y-%m-%d"),          # YYYY-MM-DD
    (re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$"), "%m/%d/%Y"),          # MM/DD/YYYY (month first)
    (re.compile(r"^\d{1,2}-[A-Za-z]{3}-\d{4}$"), "%d-%b-%Y"),       # DD-Mon-YYYY
    (re.compile(r"^\d{4}/\d{1,2}/\d{1,2}$"), "%Y/%m/%d"),          # YYYY/MM/DD
    (re.compile(r"^[A-Za-z]+ \d{1,2}, \d{4}$"), "%B %d, %Y"),       # Month D, YYYY
]

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

OUTPUT_COLUMNS = ["order_id", "order_date", "customer_id", "region",
                  "product_category", "quantity", "unit_price",
                  "discount_pct", "revenue"]


def normalize_cell(value):
    s = "" if value is None else str(value)
    s = s.strip()
    return np.nan if s.lower() in MISSING_TOKENS else s


def parse_date(value):
    if pd.isna(value):
        return None
    s = re.sub(r"\s+", " ", str(value).strip())
    for pattern, fmt in DATE_FORMATS:
        if pattern.match(s):
            try:
                return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
            except ValueError:
                return None
    return None


def parse_region(value):
    if pd.isna(value):
        return None
    key = re.sub(r"\s+", " ", str(value).strip().lower())
    return REGION_MAP.get(key)


def parse_category(value):
    if pd.isna(value):
        return None
    key = re.sub(r"\s+", " ", str(value).strip().lower())
    return CATEGORY_MAP.get(key)


def parse_unit_price(value):
    if pd.isna(value):
        return None
    s = str(value).replace("$", "").replace(",", "")
    s = re.sub(r"usd", "", s, flags=re.IGNORECASE).strip()
    if not s:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    if not np.isfinite(v) or v <= 0 or v > 5000:
        return None
    return v


def parse_quantity(value):
    if pd.isna(value):
        return None
    try:
        v = float(str(value).strip())
    except ValueError:
        return None
    if not np.isfinite(v) or not v.is_integer() or v < 1 or v > 50:
        return None
    return int(v)


def parse_discount(value):
    """Return (parsed_value_or_None_if_invalid, was_missing)."""
    if pd.isna(value):
        return 0.0, True
    s = str(value).strip()
    if s.endswith("%"):
        s = s[:-1].strip()
    try:
        v = float(s)
    except ValueError:
        return None, False
    if not np.isfinite(v) or v < 0 or v > 100:
        return None, False
    return v, False


def apply_rule(df, column, parser, summary, count_name):
    parsed = df[column].map(parser)
    summary[count_name] = int(parsed.isna().sum())
    return df.assign(**{column: parsed}).dropna(subset=[column]).copy()


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)

    # R1: read everything as text (no NA coercion), strip, normalize missing tokens.
    df = pd.read_csv(os.path.join(input_dir, "raw.csv"),
                     dtype=str, keep_default_na=False, na_filter=False,
                     encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    summary = {"raw_rows": int(len(df))}
    for col in df.columns:
        df[col] = df[col].map(normalize_cell)

    # R2: deduplicate on order_id BEFORE any other row filter (keep first occurrence).
    summary["dropped_missing_order_id"] = int(df["order_id"].isna().sum())
    df = df[df["order_id"].notna()].copy()
    summary["duplicates_removed"] = int(df.duplicated(subset=["order_id"]).sum())
    df = df.drop_duplicates(subset=["order_id"], keep="first").copy()

    # R3-R7: parse/validate fields, dropping rows that fail.
    df = apply_rule(df, "order_date", parse_date, summary,
                    "dropped_missing_or_unparseable_order_date")
    df = apply_rule(df, "region", parse_region, summary,
                    "dropped_missing_or_invalid_region")
    df = apply_rule(df, "product_category", parse_category, summary,
                    "dropped_missing_or_invalid_product_category")
    df = apply_rule(df, "unit_price", parse_unit_price, summary,
                    "dropped_missing_or_invalid_unit_price")
    df = apply_rule(df, "quantity", parse_quantity, summary,
                    "dropped_missing_or_invalid_quantity")
    df["quantity"] = df["quantity"].astype(int)

    # R8: discount_pct -- missing means 0; non-numeric/out-of-range rows are dropped.
    disc = [parse_discount(v) for v in df["discount_pct"]]
    df["discount_pct"] = [d[0] for d in disc]
    summary["discount_pct_missing_set_to_zero"] = int(sum(1 for d in disc if d[1]))
    summary["dropped_invalid_discount_pct"] = int(df["discount_pct"].isna().sum())
    df = df.dropna(subset=["discount_pct"]).copy()
    df["discount_pct"] = df["discount_pct"].astype(float)

    # R9: customer_id upper-cased; missing -> 'UNKNOWN' (row kept).
    summary["customer_id_missing_set_to_UNKNOWN"] = int(df["customer_id"].isna().sum())
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN").astype(str).str.upper()

    # R10: revenue = quantity * unit_price * (1 - discount_pct/100), 2 decimals.
    df["unit_price"] = df["unit_price"].astype(float)
    df["revenue"] = (df["quantity"].astype(float)
                     * df["unit_price"]
                     * (1.0 - df["discount_pct"] / 100.0)).round(2)

    # R11: exact column order, sort by order_id ascending, plain CSV with header, no index.
    out = (df[OUTPUT_COLUMNS]
           .sort_values("order_id", ascending=True, kind="mergesort")
           .reset_index(drop=True))
    out.to_csv(os.path.join(output_dir, "cleaned.csv"), index=False)

    summary["cleaned_rows"] = int(len(out))
    with open(os.path.join(output_dir, "cleaning_summary.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print("cleaned_rows:", summary["cleaned_rows"])


if __name__ == "__main__":
    main()
