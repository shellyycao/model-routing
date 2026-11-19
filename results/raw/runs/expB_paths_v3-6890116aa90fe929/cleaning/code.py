import os
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

# ---------- Helper functions ----------

def is_missing(val):
    if pd.isna(val):
        return True
    if isinstance(val, str):
        return val.strip().lower() in {"", "na", "n/a", "null", "none", "-"}
    return False

def clean_str(val):
    return val.strip() if isinstance(val, str) else val

def parse_order_date(val):
    if pd.isna(val):
        return np.nan
    val = val.strip()
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            # For %d-%b-%Y ensure month abbreviation capitalised (e.g., Mar)
            if fmt == "%d-%b-%Y":
                # Title‑case the month part
                parts = val.split('-')
                if len(parts) == 3:
                    parts[1] = parts[1].title()
                    val_try = '-'.join(parts)
                else:
                    val_try = val
                dt = datetime.strptime(val_try, fmt)
            else:
                dt = datetime.strptime(val, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return np.nan

def map_region(val):
    if pd.isna(val):
        return np.nan
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
    key = val.strip().lower()
    return mapping.get(key, np.nan)

def map_product_category(val):
    if pd.isna(val):
        return np.nan
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
    key = val.strip().lower()
    return mapping.get(key, np.nan)

def clean_unit_price(val):
    if pd.isna(val):
        return np.nan
    # Remove $ , USD (case‑insensitive) and surrounding spaces
    s = re.sub(r"[\$,]", "", str(val), flags=re.IGNORECASE)
    s = re.sub(r"usd", "", s, flags=re.IGNORECASE)
    s = s.strip()
    if s == "":
        return np.nan
    try:
        price = float(s)
        if price <= 0 or price > 5000:
            return np.nan
        return price
    except Exception:
        return np.nan

def clean_quantity(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    try:
        qty = float(s)
        if not qty.is_integer():
            return np.nan
        qty_int = int(qty)
        if qty_int < 1 or qty_int > 50:
            return np.nan
        return qty_int
    except Exception:
        return np.nan

def clean_discount(val):
    if pd.isna(val):
        return 0.0
    s = str(val).strip()
    if s.endswith('%'):
        s = s[:-1]
    if s == "":
        return 0.0
    try:
        disc = float(s)
        if disc < 0 or disc > 100:
            return np.nan
        return disc
    except Exception:
        return np.nan

# ---------- Main cleaning workflow ----------

def main():
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("INPUT_DIR and OUTPUT_DIR environment variables must be set")

    raw_path = os.path.join(input_dir, "raw.csv")
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)

    # R1: strip whitespace and normalise missing values
    df = df.applymap(clean_str)
    missing_mask = df.applymap(is_missing)
    df = df.mask(missing_mask, np.nan)

    # R2: remove duplicate order_id (keep first)
    dup_mask = df.duplicated(subset=["order_id"], keep='first')
    duplicates_removed = dup_mask.sum()
    df = df[~dup_mask]

    # R3: parse order_date
    df['order_date_parsed'] = df['order_date'].apply(parse_order_date)
    drop_order_date = df['order_date_parsed'].isna().sum()
    df = df.dropna(subset=['order_date_parsed'])
    df = df.drop(columns=['order_date'])
    df = df.rename(columns={'order_date_parsed': 'order_date'})

    # R4: map region
    df['region_mapped'] = df['region'].apply(map_region)
    drop_region = df['region_mapped'].isna().sum()
    df = df.dropna(subset=['region_mapped'])
    df = df.drop(columns=['region']).rename(columns={'region_mapped': 'region'})

    # R5: map product_category
    df['product_category_mapped'] = df['product_category'].apply(map_product_category)
    drop_category = df['product_category_mapped'].isna().sum()
    df = df.dropna(subset=['product_category_mapped'])
    df = df.drop(columns=['product_category']).rename(columns={'product_category_mapped': 'product_category'})

    # R6: clean unit_price
    df['unit_price_clean'] = df['unit_price'].apply(clean_unit_price)
    drop_price = df['unit_price_clean'].isna().sum()
    df = df.dropna(subset=['unit_price_clean'])
    df = df.drop(columns=['unit_price']).rename(columns={'unit_price_clean': 'unit_price'})

    # R7: clean quantity
    df['quantity_clean'] = df['quantity'].apply(clean_quantity)
    drop_quantity = df['quantity_clean'].isna().sum()
    df = df.dropna(subset=['quantity_clean'])
    df = df.drop(columns=['quantity']).rename(columns={'quantity_clean': 'quantity'})

    # R8: clean discount_pct (missing -> 0)
    df['discount_pct_clean'] = df['discount_pct'].apply(clean_discount)
    drop_discount = df['discount_pct_clean'].isna().sum()
    df = df.dropna(subset=['discount_pct_clean'])
    df = df.drop(columns=['discount_pct']).rename(columns={'discount_pct_clean': 'discount_pct'})

    # R9: clean customer_id
    df['customer_id'] = df['customer_id'].apply(lambda x: 'UNKNOWN' if pd.isna(x) else str(x).upper())

    # R10: compute revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

    # R11: final column order and sort
    final_cols = [
        'order_id', 'order_date', 'customer_id', 'region', 'product_category',
        'quantity', 'unit_price', 'discount_pct', 'revenue'
    ]
    df = df[final_cols]
    df = df.sort_values(by='order_id')

    cleaned_rows = len(df)

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(cleaned_path, index=False)

    # Write cleaning summary JSON
    summary = {
        "raw_rows": int(raw_rows),
        "cleaned_rows": int(cleaned_rows),
        "duplicates_removed": int(duplicates_removed),
        "rows_dropped_order_date": int(drop_order_date),
        "rows_dropped_region": int(drop_region),
        "rows_dropped_product_category": int(drop_category),
        "rows_dropped_unit_price": int(drop_price),
        "rows_dropped_quantity": int(drop_quantity),
        "rows_dropped_discount_pct": int(drop_discount)
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
