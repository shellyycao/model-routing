import os
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def strip_and_mark_missing(val):
    """Strip whitespace and convert defined missing tokens to NaN."""
    if not isinstance(val, str):
        return val
    val = val.strip()
    if val.lower() in {"", "na", "n/a", "null", "none", "-"}:
        return np.nan
    return val

def parse_order_date(val):
    """Try the allowed date formats, return YYYY-MM-DD string or NaN."""
    if pd.isna(val):
        return np.nan
    val = val.strip()
    date_formats = [
        "%Y-%m-%d",          # 2023-01-04
        "%m/%d/%Y",          # 01/05/2023
        "%d-%b-%Y",          # 05-Mar-2024 (abbr month)
        "%Y/%m/%d",          # 2023/01/13
        "%B %d, %Y",         # March 5, 2024 (full month name)
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return np.nan

def map_region(val):
    if pd.isna(val):
        return np.nan
    val = val.strip().lower()
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
    return mapping.get(val, np.nan)

def map_product_category(val):
    if pd.isna(val):
        return np.nan
    val = val.strip().lower()
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
    return mapping.get(val, np.nan)

def clean_unit_price(val):
    if pd.isna(val):
        return np.nan
    # Remove $ , USD (case‑insensitive) and surrounding spaces
    val = re.sub(r"\$", "", val, flags=re.IGNORECASE)
    val = re.sub(r"USD", "", val, flags=re.IGNORECASE)
    val = val.replace(",", "")
    val = val.strip()
    if val == "":
        return np.nan
    try:
        price = float(val)
        return price
    except ValueError:
        return np.nan

def clean_quantity(val):
    if pd.isna(val):
        return np.nan
    val = str(val).strip()
    try:
        qty = float(val)
        if not qty.is_integer():
            return np.nan
        qty_int = int(qty)
        return qty_int
    except ValueError:
        return np.nan

def clean_discount_pct(val):
    if pd.isna(val):
        return 0.0  # missing means no discount
    val = str(val).strip()
    if val.endswith('%'):
        val = val[:-1]
    if val == "":
        return 0.0
    try:
        pct = float(val)
        return pct
    except ValueError:
        return np.nan

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # 1. Read raw CSV as text, no automatic NA handling
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)

    # 2. R1 – strip whitespace and mark missing values
    df = df.applymap(strip_and_mark_missing)

    # 3. R2 – drop duplicate order_id, keep first occurrence
    df = df.drop_duplicates(subset="order_id", keep="first")

    # Prepare summary dict
    summary = {
        "raw_rows": raw_rows,
        "rows_after_R2": len(df),
        "dropped_R3": 0,
        "dropped_R4": 0,
        "dropped_R5": 0,
        "dropped_R6": 0,
        "dropped_R7": 0,
        "dropped_R8": 0,
        "cleaned_rows": 0,
    }

    # ---------------------------------------------------------------------
    # R3 – order_date parsing
    # ---------------------------------------------------------------------
    before = len(df)
    df["order_date"] = df["order_date"].apply(parse_order_date)
    df = df.dropna(subset=["order_date"])
    summary["dropped_R3"] = before - len(df)

    # ---------------------------------------------------------------------
    # R4 – region mapping
    # ---------------------------------------------------------------------
    before = len(df)
    df["region"] = df["region"].apply(map_region)
    df = df.dropna(subset=["region"])
    summary["dropped_R4"] = before - len(df)

    # ---------------------------------------------------------------------
    # R5 – product_category mapping
    # ---------------------------------------------------------------------
    before = len(df)
    df["product_category"] = df["product_category"].apply(map_product_category)
    df = df.dropna(subset=["product_category"])
    summary["dropped_R5"] = before - len(df)

    # ---------------------------------------------------------------------
    # R6 – unit_price cleaning and validation
    # ---------------------------------------------------------------------
    before = len(df)
    df["unit_price"] = df["unit_price"].apply(clean_unit_price)
    df = df.dropna(subset=["unit_price"])
    # enforce range >0 and <=5000
    df = df[(df["unit_price"] > 0) & (df["unit_price"] <= 5000)]
    summary["dropped_R6"] = before - len(df)

    # ---------------------------------------------------------------------
    # R7 – quantity cleaning and validation
    # ---------------------------------------------------------------------
    before = len(df)
    df["quantity"] = df["quantity"].apply(clean_quantity)
    df = df.dropna(subset=["quantity"])
    df = df[(df["quantity"] >= 1) & (df["quantity"] <= 50)]
    summary["dropped_R7"] = before - len(df)

    # ---------------------------------------------------------------------
    # R8 – discount_pct cleaning and validation
    # ---------------------------------------------------------------------
    before = len(df)
    df["discount_pct"] = df["discount_pct"].apply(clean_discount_pct)
    # rows where parsing failed become NaN – drop them
    df = df.dropna(subset=["discount_pct"])
    df = df[(df["discount_pct"] >= 0) & (df["discount_pct"] <= 100)]
    summary["dropped_R8"] = before - len(df)

    # ---------------------------------------------------------------------
    # R9 – customer_id handling
    # ---------------------------------------------------------------------
    df["customer_id"] = df["customer_id"].apply(lambda x: "UNKNOWN" if pd.isna(x) else str(x).upper())

    # ---------------------------------------------------------------------
    # R10 – revenue calculation
    # ---------------------------------------------------------------------
    df["revenue"] = (
        df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)
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

    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False)

    # Summary
    summary["cleaned_rows"] = len(df)
    # Remove intermediate helper keys not required by spec
    summary.pop("rows_after_R2", None)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
