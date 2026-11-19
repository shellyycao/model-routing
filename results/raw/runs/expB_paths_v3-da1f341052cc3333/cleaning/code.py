import os
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions for each cleaning rule
# ---------------------------------------------------------------------------

def strip_and_mark_missing(df):
    """R1 – strip whitespace and convert defined missing tokens to NaN."""
    missing_tokens = {"", "na", "n/a", "null", "none", "-"}
    def clean_cell(x):
        if isinstance(x, str):
            x = x.strip()
            if x.lower() in missing_tokens:
                return np.nan
            return x
        return x
    return df.applymap(clean_cell)

def parse_order_date(s):
    """R3 – try the allowed date formats, return ISO string or None."""
    if pd.isna(s):
        return None
    s = s.strip()
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return None

def map_region(val):
    """R4 – map region abbreviations / names to canonical values."""
    if pd.isna(val):
        return None
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
    return mapping.get(val)

def map_product_category(val):
    """R5 – map various spellings to the five allowed categories."""
    if pd.isna(val):
        return None
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
    return mapping.get(val)

def clean_unit_price(val):
    """R6 – strip currency symbols / commas and parse as float."""
    if pd.isna(val):
        return None
    # Remove $ , USD (case‑insensitive) and surrounding spaces
    s = re.sub(r"[\$,]", "", str(val), flags=re.IGNORECASE)
    s = re.sub(r"usd", "", s, flags=re.IGNORECASE)
    s = s.strip()
    try:
        price = float(s)
        return price
    except Exception:
        return None

def clean_quantity(val):
    """R7 – parse as number, ensure whole integer between 1 and 50."""
    if pd.isna(val):
        return None
    try:
        num = float(str(val).strip())
    except Exception:
        return None
    if abs(num - round(num)) > 1e-9:
        return None
    i = int(round(num))
    if 1 <= i <= 50:
        return i
    return None

def clean_discount_pct(val):
    """R8 – remove trailing % and parse; missing becomes 0."""
    if pd.isna(val):
        return 0.0
    s = str(val).strip()
    if s.endswith('%'):
        s = s[:-1]
    s = s.strip()
    try:
        pct = float(s)
        return pct
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.getenv("INPUT_DIR")
    output_dir = os.getenv("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("Both INPUT_DIR and OUTPUT_DIR environment variables must be set.")

    raw_path = os.path.join(input_dir, "raw.csv")
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)

    # R1 – strip whitespace and mark missing tokens
    df = strip_and_mark_missing(df)

    # R2 – drop duplicate order_id, keep first occurrence
    dup_mask = df.duplicated(subset="order_id", keep='first')
    duplicates_removed = dup_mask.sum()
    df = df[~dup_mask]

    # Prepare a dict to collect drop counts per rule
    drop_counts = {
        "order_date": 0,
        "region": 0,
        "product_category": 0,
        "unit_price": 0,
        "quantity": 0,
        "discount_pct": 0,
    }

    # R3 – parse order_date
    df["order_date_parsed"] = df["order_date"].apply(parse_order_date)
    mask_date = df["order_date_parsed"].notna()
    drop_counts["order_date"] = (~mask_date).sum()
    df = df[mask_date].copy()
    df["order_date"] = df["order_date_parsed"]
    df.drop(columns=["order_date_parsed"], inplace=True)

    # R4 – map region
    df["region_mapped"] = df["region"].apply(map_region)
    mask_region = df["region_mapped"].notna()
    drop_counts["region"] = (~mask_region).sum()
    df = df[mask_region].copy()
    df["region"] = df["region_mapped"]
    df.drop(columns=["region_mapped"], inplace=True)

    # R5 – map product_category
    df["product_category_mapped"] = df["product_category"].apply(map_product_category)
    mask_pc = df["product_category_mapped"].notna()
    drop_counts["product_category"] = (~mask_pc).sum()
    df = df[mask_pc].copy()
    df["product_category"] = df["product_category_mapped"]
    df.drop(columns=["product_category_mapped"], inplace=True)

    # R6 – clean unit_price
    df["unit_price_clean"] = df["unit_price"].apply(clean_unit_price)
    mask_price = df["unit_price_clean"].notna() & df["unit_price_clean"].gt(0) & df["unit_price_clean"].le(5000)
    drop_counts["unit_price"] = (~mask_price).sum()
    df = df[mask_price].copy()
    df["unit_price"] = df["unit_price_clean"]
    df.drop(columns=["unit_price_clean"], inplace=True)

    # R7 – clean quantity
    df["quantity_clean"] = df["quantity"].apply(clean_quantity)
    mask_qty = df["quantity_clean"].notna()
    drop_counts["quantity"] = (~mask_qty).sum()
    df = df[mask_qty].copy()
    df["quantity"] = df["quantity_clean"]
    df.drop(columns=["quantity_clean"], inplace=True)

    # R8 – clean discount_pct (missing -> 0)
    df["discount_pct_clean"] = df["discount_pct"].apply(clean_discount_pct)
    mask_disc = df["discount_pct_clean"].notna() & df["discount_pct_clean"].ge(0) & df["discount_pct_clean"].le(100)
    drop_counts["discount_pct"] = (~mask_disc).sum()
    df = df[mask_disc].copy()
    df["discount_pct"] = df["discount_pct_clean"]
    df.drop(columns=["discount_pct_clean"], inplace=True)

    # R9 – customer_id handling
    df["customer_id"] = df["customer_id"].fillna('UNKNOWN').apply(lambda x: str(x).upper())

    # Ensure correct dtypes for calculations
    df["unit_price"] = df["unit_price"].astype(float)
    df["quantity"] = df["quantity"].astype(int)
    df["discount_pct"] = df["discount_pct"].astype(float)

    # R10 – revenue calculation
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
    df.sort_values(by="order_id", inplace=True)

    cleaned_rows = len(df)

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(cleaned_path, index=False)

    # Write cleaning summary JSON
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows,
        "duplicates_removed": int(duplicates_removed),
        "drops_by_rule": {
            "order_date": int(drop_counts["order_date"]),
            "region": int(drop_counts["region"]),
            "product_category": int(drop_counts["product_category"]),
            "unit_price": int(drop_counts["unit_price"]),
            "quantity": int(drop_counts["quantity"]),
            "discount_pct": int(drop_counts["discount_pct"]),
        },
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
