import os
import pandas as pd
import numpy as np
import json
import re
import datetime

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def strip_and_normalise(df):
    """Strip whitespace from all string cells and replace defined missing tokens with NA."""
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    missing_tokens = {'', 'na', 'n/a', 'null', 'none', '-'}
    df = df.replace(list(missing_tokens), pd.NA, regex=False)
    return df

def parse_order_date(val):
    if pd.isna(val):
        return None
    val = val.strip()
    date_formats = [
        "%Y-%m-%d",          # 2023-01-04
        "%m/%d/%Y",          # 01/05/2023
        "%d-%b-%Y",          # 05-Mar-2024 (abbr month, case‑insensitive)
        "%Y/%m/%d",          # 2023/01/13
        "%B %d, %Y"          # March 5, 2024
    ]
    for fmt in date_formats:
        try:
            dt = datetime.datetime.strptime(val, fmt)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            continue
    return None

def clean_unit_price(val):
    if pd.isna(val):
        return None
    # remove $ , USD (case‑insensitive) and surrounding spaces
    val = re.sub(r"\$", "", val)
    val = re.sub(r",", "", val)
    val = re.sub(r"\bUSD\b", "", val, flags=re.I)
    val = val.strip()
    try:
        price = float(val)
        return price
    except Exception:
        return None

def clean_quantity(val):
    if pd.isna(val):
        return None
    try:
        num = float(val)
        if abs(num - round(num)) > 1e-9:
            return None
        return int(round(num))
    except Exception:
        return None

def clean_discount(val):
    if pd.isna(val):
        return 0.0
    val = str(val).strip()
    if val.endswith('%'):
        val = val[:-1]
    try:
        return float(val)
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get('INPUT_DIR')
    output_dir = os.environ.get('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('Both INPUT_DIR and OUTPUT_DIR environment variables must be set')

    raw_path = os.path.join(input_dir, 'raw.csv')
    df_raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df_raw)

    # R1 – strip whitespace and normalise missing tokens
    df = strip_and_normalise(df_raw.copy())

    summary = {
        'raw_rows': raw_rows,
        'duplicate_rows_removed': 0,
        'order_date_invalid': 0,
        'region_invalid': 0,
        'product_category_invalid': 0,
        'unit_price_invalid': 0,
        'quantity_invalid': 0,
        'discount_pct_invalid': 0,
        'cleaned_rows': 0
    }

    # R2 – drop duplicate order_id, keep first occurrence
    before_dup = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    summary['duplicate_rows_removed'] = before_dup - len(df)

    # ---------------------------------------------------------------------
    # R3 – order_date parsing
    # ---------------------------------------------------------------------
    df['order_date_parsed'] = df['order_date'].apply(parse_order_date)
    before = len(df)
    df = df.dropna(subset=['order_date_parsed'])
    summary['order_date_invalid'] = before - len(df)
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
        key = val.strip().lower()
        return region_map.get(key)
    df['region_mapped'] = df['region'].apply(map_region)
    before = len(df)
    df = df.dropna(subset=['region_mapped'])
    summary['region_invalid'] = before - len(df)
    df = df.drop(columns=['region'])
    df = df.rename(columns={'region_mapped': 'region'})

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
        key = val.strip().lower()
        return cat_map.get(key)
    df['product_category_mapped'] = df['product_category'].apply(map_category)
    before = len(df)
    df = df.dropna(subset=['product_category_mapped'])
    summary['product_category_invalid'] = before - len(df)
    df = df.drop(columns=['product_category'])
    df = df.rename(columns={'product_category_mapped': 'product_category'})

    # ---------------------------------------------------------------------
    # R6 – unit_price cleaning
    # ---------------------------------------------------------------------
    df['unit_price_clean'] = df['unit_price'].apply(clean_unit_price)
    before = len(df)
    df = df.dropna(subset=['unit_price_clean'])
    # filter range
    df = df[(df['unit_price_clean'] > 0) & (df['unit_price_clean'] <= 5000)]
    summary['unit_price_invalid'] = before - len(df)
    df = df.drop(columns=['unit_price'])
    df = df.rename(columns={'unit_price_clean': 'unit_price'})

    # ---------------------------------------------------------------------
    # R7 – quantity cleaning
    # ---------------------------------------------------------------------
    df['quantity_clean'] = df['quantity'].apply(clean_quantity)
    before = len(df)
    df = df.dropna(subset=['quantity_clean'])
    df = df[(df['quantity_clean'] >= 1) & (df['quantity_clean'] <= 50)]
    summary['quantity_invalid'] = before - len(df)
    df = df.drop(columns=['quantity'])
    df = df.rename(columns={'quantity_clean': 'quantity'})

    # ---------------------------------------------------------------------
    # R8 – discount_pct cleaning
    # ---------------------------------------------------------------------
    df['discount_pct_clean'] = df['discount_pct'].apply(clean_discount)
    before = len(df)
    # rows where parsing failed become NaN – drop them
    df = df.dropna(subset=['discount_pct_clean'])
    df = df[(df['discount_pct_clean'] >= 0) & (df['discount_pct_clean'] <= 100)]
    summary['discount_pct_invalid'] = before - len(df)
    df = df.drop(columns=['discount_pct'])
    df = df.rename(columns={'discount_pct_clean': 'discount_pct'})

    # ---------------------------------------------------------------------
    # R9 – customer_id handling
    # ---------------------------------------------------------------------
    df['customer_id'] = df['customer_id'].fillna('UNKNOWN').astype(str).str.upper()

    # ---------------------------------------------------------------------
    # R10 – revenue calculation
    # ---------------------------------------------------------------------
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

    # ---------------------------------------------------------------------
    # R11 – final column order and sorting
    # ---------------------------------------------------------------------
    final_cols = [
        'order_id', 'order_date', 'customer_id', 'region',
        'product_category', 'quantity', 'unit_price', 'discount_pct', 'revenue'
    ]
    df = df[final_cols]
    df = df.sort_values('order_id')

    cleaned_rows = len(df)
    summary['cleaned_rows'] = cleaned_rows

    # ---------------------------------------------------------------------
    # Write outputs
    # ---------------------------------------------------------------------
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(cleaned_path, index=False)

    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
