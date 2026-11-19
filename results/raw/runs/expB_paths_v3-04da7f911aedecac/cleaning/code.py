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
    """Strip whitespace from all string cells and replace defined missing values with NaN."""
    # Strip whitespace
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    # Define missing tokens (case‑insensitive)
    missing_tokens = {'', 'na', 'n/a', 'null', 'none', '-'}
    def to_nan(v):
        if isinstance(v, str) and v.strip().lower() in missing_tokens:
            return np.nan
        return v
    return df.replace(to_nan)

def parse_order_date(val):
    """Try the allowed date formats, return a string YYYY‑MM‑DD or None."""
    if pd.isna(val):
        return None
    val = val.strip()
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
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
    key = val.strip().lower()
    mapping = {
        'north': 'North', 'n': 'North',
        'south': 'South', 's': 'South',
        'east':  'East',  'e': 'East',
        'west':  'West',  'w': 'West'
    }
    return mapping.get(key)

def map_product_category(val):
    if pd.isna(val):
        return None
    key = val.strip().lower()
    mapping = {
        'electronics': 'Electronics',
        'electronic':  'Electronics',
        'clothing':    'Clothing',
        'apparel':     'Clothing',
        'home & garden': 'Home & Garden',
        'home and garden': 'Home & Garden',
        'home&garden': 'Home & Garden',
        'sports':      'Sports',
        'sport':       'Sports',
        'books':       'Books',
        'book':        'Books'
    }
    return mapping.get(key)

def clean_unit_price(val):
    if pd.isna(val):
        return None
    # Remove $ , USD (case‑insensitive) and surrounding spaces
    cleaned = re.sub(r"[\$,]", "", str(val), flags=re.IGNORECASE)
    cleaned = re.sub(r"usd", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
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
        num = float(str(val).strip())
        if abs(num - round(num)) > 1e-6:
            return None
        return int(round(num))
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
    df_raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df_raw)

    # R1 – strip whitespace and normalise missing values
    df = strip_and_normalize(df_raw)

    # Counters for summary
    summary = {
        'raw_rows': raw_rows,
        'duplicates_removed': 0,
        'order_date_invalid': 0,
        'region_invalid': 0,
        'product_category_invalid': 0,
        'unit_price_invalid': 0,
        'quantity_invalid': 0,
        'discount_invalid': 0
    }

    # R2 – remove duplicate order_id, keep first
    before_dup = len(df)
    df = df.drop_duplicates(subset=['order_id'], keep='first')
    summary['duplicates_removed'] = before_dup - len(df)

    # R3 – parse order_date
    df['order_date_parsed'] = df['order_date'].apply(parse_order_date)
    before = len(df)
    df = df[~df['order_date_parsed'].isna()]
    summary['order_date_invalid'] = before - len(df)
    df = df.drop(columns=['order_date'])
    df = df.rename(columns={'order_date_parsed': 'order_date'})

    # R4 – map region
    df['region_mapped'] = df['region'].apply(map_region)
    before = len(df)
    df = df[~df['region_mapped'].isna()]
    summary['region_invalid'] = before - len(df)
    df = df.drop(columns=['region'])
    df = df.rename(columns={'region_mapped': 'region'})

    # R5 – map product_category
    df['product_category_mapped'] = df['product_category'].apply(map_product_category)
    before = len(df)
    df = df[~df['product_category_mapped'].isna()]
    summary['product_category_invalid'] = before - len(df)
    df = df.drop(columns=['product_category'])
    df = df.rename(columns={'product_category_mapped': 'product_category'})

    # R6 – clean unit_price
    df['unit_price_clean'] = df['unit_price'].apply(clean_unit_price)
    before = len(df)
    df = df[~df['unit_price_clean'].isna()]
    # filter range
    df = df[(df['unit_price_clean'] > 0) & (df['unit_price_clean'] <= 5000)]
    summary['unit_price_invalid'] = before - len(df)
    df = df.drop(columns=['unit_price'])
    df = df.rename(columns={'unit_price_clean': 'unit_price'})

    # R7 – clean quantity
    df['quantity_clean'] = df['quantity'].apply(clean_quantity)
    before = len(df)
    df = df[~df['quantity_clean'].isna()]
    df = df[(df['quantity_clean'] >= 1) & (df['quantity_clean'] <= 50)]
    summary['quantity_invalid'] = before - len(df)
    df = df.drop(columns=['quantity'])
    df = df.rename(columns={'quantity_clean': 'quantity'})

    # R8 – clean discount_pct
    df['discount_pct_clean'] = df['discount_pct'].apply(clean_discount)
    before = len(df)
    df = df[~df['discount_pct_clean'].isna()]
    df = df[(df['discount_pct_clean'] >= 0) & (df['discount_pct_clean'] <= 100)]
    summary['discount_invalid'] = before - len(df)
    df = df.drop(columns=['discount_pct'])
    df = df.rename(columns={'discount_pct_clean': 'discount_pct'})

    # R9 – customer_id handling
    df['customer_id'] = df['customer_id'].fillna('UNKNOWN').astype(str).str.upper()

    # Ensure correct dtypes
    df['quantity'] = df['quantity'].astype(int)
    df['unit_price'] = df['unit_price'].astype(float)
    df['discount_pct'] = df['discount_pct'].astype(float)

    # R10 – revenue calculation
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

    # R11 – final column order and sorting
    final_cols = ['order_id', 'order_date', 'customer_id', 'region', 'product_category',
                  'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[final_cols]
    df = df.sort_values(by='order_id')

    cleaned_rows = len(df)
    summary['cleaned_rows'] = cleaned_rows

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(cleaned_path, index=False)

    # Write cleaning summary JSON
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
