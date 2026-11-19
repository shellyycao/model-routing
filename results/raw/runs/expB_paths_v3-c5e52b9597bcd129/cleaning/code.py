import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def clean_missing(val):
    """Strip whitespace and convert defined missing tokens to NaN."""
    if isinstance(val, str):
        val = val.strip()
        if val == "" or val.lower() in {"na", "n/a", "null", "none", "-"}:
            return np.nan
        return val
    return val

def parse_order_date(val):
    """Try the allowed date formats, return YYYY-MM-DD string or None."""
    if pd.isna(val):
        return None
    formats = [
        "%Y-%m-%d",          # 2023-01-04
        "%m/%d/%Y",          # 01/05/2023
        "%d-%b-%Y",          # 05-Mar-2024 (abbr month)
        "%Y/%m/%d",          # 2023/01/13
        "%B %d, %Y",         # March 5, 2024
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return None

def map_region(val):
    if pd.isna(val):
        return None
    v = val.strip().lower()
    mapping = {
        "north": "North",
        "n": "North",
        "south": "South",
        "s": "South",
        "east": "East",
        "e": "East",
        "west": "West",
        "w": "West",
    }
    return mapping.get(v)

def map_product_category(val):
    if pd.isna(val):
        return None
    v = val.strip().lower()
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
    return mapping.get(v)

def clean_unit_price(val):
    if pd.isna(val):
        return None
    # Remove $, USD, commas and surrounding spaces
    cleaned = val.replace('$', '').replace('USD', '').replace(',', '').strip()
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

def clean_discount_pct(val):
    if pd.isna(val):
        return 0.0  # missing means no discount
    s = str(val).strip()
    if s.endswith('%'):
        s = s[:-1]
    try:
        return float(s)
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.getenv('INPUT_DIR')
    output_dir = os.getenv('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('INPUT_DIR and OUTPUT_DIR environment variables must be set')

    raw_path = os.path.join(input_dir, 'raw.csv')
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)

    # R1: strip whitespace and normalise missing values
    df = df.applymap(clean_missing)

    # R2: remove duplicate order_id, keep first
    dup_mask = df.duplicated(subset='order_id', keep='first')
    duplicates_removed = dup_mask.sum()
    df = df[~dup_mask].copy()

    # Prepare summary counters
    summary = {
        "raw_rows": raw_rows,
        "duplicates_removed": int(duplicates_removed),
        "order_date_invalid": 0,
        "region_invalid": 0,
        "product_category_invalid": 0,
        "unit_price_invalid": 0,
        "quantity_invalid": 0,
        "discount_pct_invalid": 0,
        "cleaned_rows": 0
    }

    # R3: order_date parsing
    df['order_date_parsed'] = df['order_date'].apply(parse_order_date)
    before = len(df)
    df = df[~df['order_date_parsed'].isna()].copy()
    summary['order_date_invalid'] = before - len(df)
    df = df.drop(columns=['order_date'])
    df = df.rename(columns={'order_date_parsed': 'order_date'})

    # R4: region mapping
    df['region_mapped'] = df['region'].apply(map_region)
    before = len(df)
    df = df[~df['region_mapped'].isna()].copy()
    summary['region_invalid'] = before - len(df)
    df = df.drop(columns=['region'])
    df = df.rename(columns={'region_mapped': 'region'})

    # R5: product_category mapping
    df['product_category_mapped'] = df['product_category'].apply(map_product_category)
    before = len(df)
    df = df[~df['product_category_mapped'].isna()].copy()
    summary['product_category_invalid'] = before - len(df)
    df = df.drop(columns=['product_category'])
    df = df.rename(columns={'product_category_mapped': 'product_category'})

    # R6: unit_price cleaning
    df['unit_price_clean'] = df['unit_price'].apply(clean_unit_price)
    before = len(df)
    df = df[~df['unit_price_clean'].isna()].copy()
    summary['unit_price_invalid'] = before - len(df)
    # Apply numeric constraints
    df = df[(df['unit_price_clean'] > 0) & (df['unit_price_clean'] <= 5000)]
    # Count rows removed by constraints
    summary['unit_price_invalid'] += before - len(df)
    df = df.drop(columns=['unit_price'])
    df = df.rename(columns={'unit_price_clean': 'unit_price'})

    # R7: quantity cleaning
    df['quantity_clean'] = df['quantity'].apply(clean_quantity)
    before = len(df)
    df = df[~df['quantity_clean'].isna()].copy()
    summary['quantity_invalid'] = before - len(df)
    df = df[(df['quantity_clean'] >= 1) & (df['quantity_clean'] <= 50)]
    summary['quantity_invalid'] += before - len(df)
    df = df.drop(columns=['quantity'])
    df = df.rename(columns={'quantity_clean': 'quantity'})

    # R8: discount_pct cleaning
    df['discount_pct_clean'] = df['discount_pct'].apply(clean_discount_pct)
    before = len(df)
    df = df[~df['discount_pct_clean'].isna()].copy()
    summary['discount_pct_invalid'] = before - len(df)
    df = df[(df['discount_pct_clean'] >= 0) & (df['discount_pct_clean'] <= 100)]
    summary['discount_pct_invalid'] += before - len(df)
    df = df.drop(columns=['discount_pct'])
    df = df.rename(columns={'discount_pct_clean': 'discount_pct'})

    # R9: customer_id handling
    df['customer_id'] = df['customer_id'].apply(lambda x: 'UNKNOWN' if pd.isna(x) else str(x).upper())

    # Ensure correct dtypes
    df['quantity'] = df['quantity'].astype(int)
    df['unit_price'] = df['unit_price'].astype(float)
    df['discount_pct'] = df['discount_pct'].astype(float)

    # R10: revenue calculation
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

    # R11: final column order and sorting
    final_cols = [
        'order_id', 'order_date', 'customer_id', 'region',
        'product_category', 'quantity', 'unit_price', 'discount_pct', 'revenue'
    ]
    df = df[final_cols]
    df = df.sort_values(by='order_id')

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(cleaned_path, index=False)

    # Summary JSON
    summary['cleaned_rows'] = len(df)
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
