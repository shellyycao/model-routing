import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

# ---------------------------------------------------------------------------
# Helper functions for cleaning steps
# ---------------------------------------------------------------------------

def strip_and_mark_missing(df, missing_set):
    """Strip whitespace from all string cells and replace defined missing values with NaN."""
    def clean_cell(x):
        if isinstance(x, str):
            x = x.strip()
            if x.lower() in missing_set:
                return np.nan
            return x
        return x
    return df.applymap(clean_cell)

def parse_order_date(val):
    """Try the allowed date formats, return YYYY-MM-DD string or NaN."""
    if pd.isna(val):
        return np.nan
    val = val.strip()
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d-%b-%Y",   # e.g. 05-Mar-2024
        "%Y/%m/%d",
        "%B %d, %Y",  # full month name
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return np.nan

def map_region(val):
    if pd.isna(val):
        return np.nan
    key = val.strip().lower()
    mapping = {
        "n": "North",
        "north": "North",
        "s": "South",
        "south": "South",
        "e": "East",
        "east": "East",
        "w": "West",
        "west": "West",
    }
    return mapping.get(key, np.nan)

def map_product_category(val):
    if pd.isna(val):
        return np.nan
    key = val.strip().lower()
    mapping = {
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
    return mapping.get(key, np.nan)

def clean_unit_price(val):
    if pd.isna(val):
        return np.nan
    # Remove $ , USD (case‑insensitive) and surrounding spaces
    cleaned = val.replace('$', '').replace(',', '')
    cleaned = cleaned.replace('USD', '').replace('usd', '')
    cleaned = cleaned.strip()
    if cleaned == "":
        return np.nan
    try:
        price = float(cleaned)
        return price
    except Exception:
        return np.nan

def clean_quantity(val):
    if pd.isna(val):
        return np.nan
    try:
        qty = float(val)
        if not qty.is_integer():
            return np.nan
        qty_int = int(qty)
        return qty_int
    except Exception:
        return np.nan

def clean_discount_pct(val):
    if pd.isna(val):
        return 0.0  # missing means no discount
    s = str(val).strip()
    if s.endswith('%'):
        s = s[:-1].strip()
    if s == "":
        return 0.0
    try:
        pct = float(s)
        return pct
    except Exception:
        return np.nan

def clean_customer_id(val):
    if pd.isna(val):
        return "UNKNOWN"
    return str(val).strip().upper()

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("Both INPUT_DIR and OUTPUT_DIR environment variables must be set.")

    raw_path = os.path.join(input_dir, "raw.csv")
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    summary = {
        "raw_rows": len(df),
        "duplicates_removed": 0,
        "rows_after_duplicates": 0,
        "rows_after_order_date": 0,
        "rows_after_region": 0,
        "rows_after_product_category": 0,
        "rows_after_unit_price": 0,
        "rows_after_quantity": 0,
        "rows_after_discount_pct": 0,
        "cleaned_rows": 0,
    }

    # R1 – strip whitespace and mark generic missing values
    missing_vals = {"", "na", "n/a", "null", "none", "-"}
    df = strip_and_mark_missing(df, missing_vals)

    # R2 – remove duplicate order_id, keep first
    dup_mask = df.duplicated(subset=["order_id"], keep='first')
    summary["duplicates_removed"] = dup_mask.sum()
    df = df[~dup_mask].copy()
    summary["rows_after_duplicates"] = len(df)

    # R3 – parse order_date
    df["order_date_parsed"] = df["order_date"].apply(parse_order_date)
    df = df.dropna(subset=["order_date_parsed"]).copy()
    summary["rows_after_order_date"] = len(df)
    df["order_date"] = df["order_date_parsed"]
    df = df.drop(columns=["order_date_parsed"])

    # R4 – map region
    df["region_mapped"] = df["region"].apply(map_region)
    df = df.dropna(subset=["region_mapped"]).copy()
    summary["rows_after_region"] = len(df)
    df["region"] = df["region_mapped"]
    df = df.drop(columns=["region_mapped"])

    # R5 – map product_category
    df["product_category_mapped"] = df["product_category"].apply(map_product_category)
    df = df.dropna(subset=["product_category_mapped"]).copy()
    summary["rows_after_product_category"] = len(df)
    df["product_category"] = df["product_category_mapped"]
    df = df.drop(columns=["product_category_mapped"])

    # R6 – clean unit_price
    df["unit_price_clean"] = df["unit_price"].apply(clean_unit_price)
    df = df.dropna(subset=["unit_price_clean"]).copy()
    # enforce bounds
    df = df[(df["unit_price_clean"] > 0) & (df["unit_price_clean"] <= 5000)].copy()
    summary["rows_after_unit_price"] = len(df)
    df["unit_price"] = df["unit_price_clean"]
    df = df.drop(columns=["unit_price_clean"])

    # R7 – clean quantity
    df["quantity_clean"] = df["quantity"].apply(clean_quantity)
    df = df.dropna(subset=["quantity_clean"]).copy()
    df = df[(df["quantity_clean"] >= 1) & (df["quantity_clean"] <= 50)].copy()
    summary["rows_after_quantity"] = len(df)
    df["quantity"] = df["quantity_clean"]
    df = df.drop(columns=["quantity_clean"])

    # R8 – clean discount_pct
    df["discount_pct_clean"] = df["discount_pct"].apply(clean_discount_pct)
    df = df.dropna(subset=["discount_pct_clean"]).copy()
    df = df[(df["discount_pct_clean"] >= 0) & (df["discount_pct_clean"] <= 100)].copy()
    summary["rows_after_discount_pct"] = len(df)
    df["discount_pct"] = df["discount_pct_clean"]
    df = df.drop(columns=["discount_pct_clean"])

    # R9 – clean customer_id
    df["customer_id"] = df["customer_id"].apply(clean_customer_id)

    # Ensure correct dtypes for numeric columns
    df["unit_price"] = df["unit_price"].astype(float)
    df["quantity"] = df["quantity"].astype(int)
    df["discount_pct"] = df["discount_pct"].astype(float)

    # R10 – compute revenue
    df["revenue"] = (df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)).round(2)

    # R11 – final column order and sorting
    final_cols = [
        "order_id",
        "order_date",
        "customer_id",
        "region",
        "product_category",
        "quantity",
        "unit_price",
        "discount_pct",
        "revenue",
    ]
    df = df[final_cols]
    df = df.sort_values(by="order_id", ascending=True).reset_index(drop=True)
    summary["cleaned_rows"] = len(df)

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(cleaned_path, index=False)

    # Write cleaning summary JSON
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
