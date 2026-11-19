import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def strip_and_normalise(val):
    """Strip whitespace and convert known missing markers to NaN."""
    if not isinstance(val, str):
        return val
    val = val.strip()
    if val.lower() in {"", "na", "n/a", "null", "none", "-"}:
        return np.nan
    return val

def parse_order_date(date_str):
    """Try the allowed date formats, return ISO string or None."""
    if pd.isna(date_str):
        return None
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return None

def clean_unit_price(val):
    if pd.isna(val):
        return None
    # remove $ , USD (case‑insensitive) and surrounding spaces
    cleaned = val.replace('$', '').replace(',', '')
    cleaned = cleaned.replace('USD', '').strip()
    if cleaned == "":
        return None
    try:
        price = float(cleaned)
        return price
    except Exception:
        return None

def clean_quantity(val):
    if pd.isna(val):
        return None
    try:
        num = float(val)
        if not num.is_integer():
            return None
        return int(num)
    except Exception:
        return None

def clean_discount(val):
    if pd.isna(val):
        return 0.0
    s = str(val).strip()
    if s.endswith('%'):
        s = s[:-1]
    if s == "":
        return 0.0
    try:
        return float(s)
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("INPUT_DIR and OUTPUT_DIR environment variables must be set")

    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # 1. Read everything as text, no NA conversion
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_filter=False)
    raw_rows = len(df)

    # 2. Strip whitespace and normalise missing markers for every cell
    df = df.applymap(strip_and_normalise)

    # Prepare summary counters
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": None,
        "duplicates_removed": 0,
        "rows_dropped_R3_order_date": 0,
        "rows_dropped_R4_region": 0,
        "rows_dropped_R5_product_category": 0,
        "rows_dropped_R6_unit_price": 0,
        "rows_dropped_R7_quantity": 0,
        "rows_dropped_R8_discount_pct": 0
    }

    # ---------------------------------------------------------------------
    # R2 – Remove duplicate order_id (keep first)
    # ---------------------------------------------------------------------
    before = len(df)
    df = df.drop_duplicates(subset="order_id", keep="first")
    summary["duplicates_removed"] = before - len(df)

    # ---------------------------------------------------------------------
    # R3 – order_date parsing
    # ---------------------------------------------------------------------
    df["order_date_parsed"] = df["order_date"].apply(parse_order_date)
    keep_mask = df["order_date_parsed"].notna()
    summary["rows_dropped_R3_order_date"] = len(df) - keep_mask.sum()
    df = df[keep_mask].copy()
    df = df.drop(columns=["order_date"]).rename(columns={"order_date_parsed": "order_date"})

    # ---------------------------------------------------------------------
    # R4 – region mapping
    # ---------------------------------------------------------------------
    region_map = {
        "n": "North",
        "north": "North",
        "s": "South",
        "south": "South",
        "e": "East",
        "east": "East",
        "w": "West",
        "west": "West"
    }
    df["region_mapped"] = df["region"].astype(str).str.lower().map(region_map)
    keep_mask = df["region_mapped"].notna()
    summary["rows_dropped_R4_region"] = len(df) - keep_mask.sum()
    df = df[keep_mask].copy()
    df = df.drop(columns=["region"]).rename(columns={"region_mapped": "region"})

    # ---------------------------------------------------------------------
    # R5 – product_category mapping
    # ---------------------------------------------------------------------
    cat_map = {
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
        "book": "Books"
    }
    df["product_category_mapped"] = df["product_category"].astype(str).str.lower().map(cat_map)
    keep_mask = df["product_category_mapped"].notna()
    summary["rows_dropped_R5_product_category"] = len(df) - keep_mask.sum()
    df = df[keep_mask].copy()
    df = df.drop(columns=["product_category"]).rename(columns={"product_category_mapped": "product_category"})

    # ---------------------------------------------------------------------
    # R6 – unit_price cleaning and validation
    # ---------------------------------------------------------------------
    df["unit_price_clean"] = df["unit_price"].apply(clean_unit_price)
    keep_mask = df["unit_price_clean"].notna() & (df["unit_price_clean"] > 0) & (df["unit_price_clean"] <= 5000)
    summary["rows_dropped_R6_unit_price"] = len(df) - keep_mask.sum()
    df = df[keep_mask].copy()
    df = df.drop(columns=["unit_price"]).rename(columns={"unit_price_clean": "unit_price"})

    # ---------------------------------------------------------------------
    # R7 – quantity validation
    # ---------------------------------------------------------------------
    df["quantity_clean"] = df["quantity"].apply(clean_quantity)
    keep_mask = df["quantity_clean"].notna() & (df["quantity_clean"] >= 1) & (df["quantity_clean"] <= 50)
    summary["rows_dropped_R7_quantity"] = len(df) - keep_mask.sum()
    df = df[keep_mask].copy()
    df = df.drop(columns=["quantity"]).rename(columns={"quantity_clean": "quantity"})

    # ---------------------------------------------------------------------
    # R8 – discount_pct cleaning and validation (missing -> 0)
    # ---------------------------------------------------------------------
    df["discount_pct_clean"] = df["discount_pct"].apply(clean_discount)
    keep_mask = df["discount_pct_clean"].notna() & (df["discount_pct_clean"] >= 0) & (df["discount_pct_clean"] <= 100)
    summary["rows_dropped_R8_discount_pct"] = len(df) - keep_mask.sum()
    df = df[keep_mask].copy()
    df = df.drop(columns=["discount_pct"]).rename(columns={"discount_pct_clean": "discount_pct"})

    # ---------------------------------------------------------------------
    # R9 – customer_id handling
    # ---------------------------------------------------------------------
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN").astype(str).str.upper()

    # ---------------------------------------------------------------------
    # R10 – revenue calculation
    # ---------------------------------------------------------------------
    df["revenue"] = (
        df["quantity"].astype(int) *
        df["unit_price"].astype(float) *
        (1 - df["discount_pct"].astype(float) / 100)
    ).round(2)

    # ---------------------------------------------------------------------
    # R11 – final column order, sorting and output
    # ---------------------------------------------------------------------
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
    df = df.sort_values(by="order_id", ascending=True)

    # Ensure correct dtypes for output (pandas will write them as needed)
    df["quantity"] = df["quantity"].astype(int)
    df["unit_price"] = df["unit_price"].astype(float)
    df["discount_pct"] = df["discount_pct"].astype(float)
    df["revenue"] = df["revenue"].astype(float)

    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False)

    # Summary JSON
    summary["cleaned_rows"] = len(df)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
