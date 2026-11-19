import os
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def strip_and_normalize(df):
    """Strip whitespace from all string cells and convert defined missing tokens to NaN."""
    missing_tokens = {'', 'na', 'n/a', 'null', 'none', '-'}
    def clean_cell(x):
        if isinstance(x, str):
            x = x.strip()
            if x.lower() in missing_tokens:
                return np.nan
            return x
        return x
    return df.applymap(clean_cell)

def parse_date(value):
    if pd.isna(value):
        return None
    value = value.strip()
    # possible formats
    fmts = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in fmts:
        try:
            # For %d-%b-%Y the month abbreviation may be lower‑case; title‑case it
            if fmt == "%d-%b-%Y":
                value_to_try = value.title()
            else:
                value_to_try = value
            dt = datetime.strptime(value_to_try, fmt)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            continue
    return None

def clean_unit_price(val):
    if pd.isna(val):
        return None
    # remove $ , USD (case‑insensitive) and surrounding spaces
    val = re.sub(r"[\$,]", "", str(val), flags=re.IGNORECASE)
    val = re.sub(r"usd", "", val, flags=re.IGNORECASE)
    val = val.strip()
    if val == "":
        return None
    try:
        num = float(val)
        return num
    except Exception:
        return None

def clean_quantity(val):
    if pd.isna(val):
        return None
    try:
        num = float(str(val).strip())
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
    input_dir = os.environ.get('INPUT_DIR')
    output_dir = os.environ.get('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('INPUT_DIR and OUTPUT_DIR environment variables must be set')

    raw_path = os.path.join(input_dir, 'raw.csv')
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')

    # 1. Read raw CSV – all columns as text, no NA parsing
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_filter=False)
    raw_rows = len(df)
    summary = {'raw_rows': raw_rows}

    # 2. Strip whitespace and normalise missing tokens (R1)
    df = strip_and_normalize(df)

    # 3. Remove duplicate order_id rows, keep first (R2)
    before_dup = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    dup_removed = before_dup - len(df)
    summary['duplicates_removed'] = dup_removed

    # ---------------------------------------------------------------------
    # R3 – order_date parsing
    # ---------------------------------------------------------------------
    df['order_date_parsed'] = df['order_date'].apply(parse_date)
    before = len(df)
    df = df[~df['order_date_parsed'].isna()]
    summary['rows_dropped_order_date'] = before - len(df)
    df = df.drop(columns=['order_date'])
    df = df.rename(columns={'order_date_parsed': 'order_date'})

    # ---------------------------------------------------------------------
    # R4 – region mapping
    # ---------------------------------------------------------------------
    region_map = {
        'n': 'North', 'north': 'North',
        's': 'South', 'south': 'South',
        'e': 'East',  'east': 'East',
        'w': 'West',  'west': 'West'
    }
    def map_region(val):
        if pd.isna(val):
            return None
        return region_map.get(val.strip().lower())
    df['region_mapped'] = df['region'].apply(map_region)
    before = len(df)
    df = df[~df['region_mapped'].isna()]
    summary['rows_dropped_region'] = before - len(df)
    df = df.drop(columns=['region']).rename(columns={'region_mapped': 'region'})

    # ---------------------------------------------------------------------
    # R5 – product_category mapping
    # ---------------------------------------------------------------------
    cat_map = {
        'electronics': 'Electronics',
        'electronic': 'Electronics',
        'clothing': 'Clothing',
        'apparel': 'Clothing',
        'home & garden': 'Home & Garden',
        'home and garden': 'Home & Garden',
        'home&garden': 'Home & Garden',
        'sports': 'Sports',
        'sport': 'Sports',
        'books': 'Books',
        'book': 'Books'
    }
    def map_category(val):
        if pd.isna(val):
            return None
        return cat_map.get(val.strip().lower())
    df['category_mapped'] = df['product_category'].apply(map_category)
    before = len(df)
    df = df[~df['category_mapped'].isna()]
    summary['rows_dropped_product_category'] = before - len(df)
    df = df.drop(columns=['product_category']).rename(columns={'category_mapped': 'product_category'})

    # ---------------------------------------------------------------------
    # R6 – unit_price cleaning
    # ---------------------------------------------------------------------
    df['unit_price_clean'] = df['unit_price'].apply(clean_unit_price)
    before = len(df)
    df = df[~df['unit_price_clean'].isna()]
    df = df[(df['unit_price_clean'] > 0) & (df['unit_price_clean'] <= 5000)]
    summary['rows_dropped_unit_price'] = before - len(df)
    df = df.drop(columns=['unit_price']).rename(columns={'unit_price_clean': 'unit_price'})

    # ---------------------------------------------------------------------
    # R7 – quantity cleaning
    # ---------------------------------------------------------------------
    df['quantity_clean'] = df['quantity'].apply(clean_quantity)
    before = len(df)
    df = df[~df['quantity_clean'].isna()]
    df = df[(df['quantity_clean'] >= 1) & (df['quantity_clean'] <= 50)]
    summary['rows_dropped_quantity'] = before - len(df)
    df = df.drop(columns=['quantity']).rename(columns={'quantity_clean': 'quantity'})

    # ---------------------------------------------------------------------
    # R8 – discount_pct cleaning
    # ---------------------------------------------------------------------
    df['discount_pct_clean'] = df['discount_pct'].apply(clean_discount)
    before = len(df)
    # rows where discount could not be parsed become NaN -> drop
    df = df[~df['discount_pct_clean'].isna()]
    df = df[(df['discount_pct_clean'] >= 0) & (df['discount_pct_clean'] <= 100)]
    summary['rows_dropped_discount_pct'] = before - len(df)
    df = df.drop(columns=['discount_pct']).rename(columns={'discount_pct_clean': 'discount_pct'})

    # ---------------------------------------------------------------------
    # R9 – customer_id handling
    # ---------------------------------------------------------------------
    df['customer_id'] = df['customer_id'].apply(lambda x: 'UNKNOWN' if pd.isna(x) else str(x).upper())

    # ---------------------------------------------------------------------
    # R10 – revenue calculation
    # ---------------------------------------------------------------------
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

    # ---------------------------------------------------------------------
    # R11 – final column order, sorting and output
    # ---------------------------------------------------------------------
    final_cols = [
        'order_id', 'order_date', 'customer_id', 'region',
        'product_category', 'quantity', 'unit_price', 'discount_pct', 'revenue'
    ]
    df = df[final_cols]
    df = df.sort_values(by='order_id')

    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False)
    summary['cleaned_rows'] = len(df)

    # Write cleaning summary JSON
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
