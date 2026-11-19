import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def clean_str(val):
    """Strip whitespace and convert recognised missing strings to NaN."""
    if pd.isna(val):
        return np.nan
    val = str(val).strip()
    if val.lower() in {"", "na", "n/a", "null", "none", "-"}:
        return np.nan
    return val

def parse_order_date(date_str):
    """Try the allowed date formats, return a YYYY‑MM‑DD string or None."""
    if pd.isna(date_str):
        return None
    date_str = str(date_str).strip()
    formats = [
        "%Y-%m-%d",          # 2023-01-04
        "%m/%d/%Y",          # 01/05/2023
        "%d-%b-%Y",          # 05-Mar-2024 (abbr month, case‑insensitive)
        "%Y/%m/%d",          # 2023/01/13
        "%B %d, %Y"          # March 5, 2024
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return None

def map_region(val):
    if pd.isna(val):
        return None
    val = str(val).strip().lower()
    mapping = {
        "north": "North", "n": "North",
        "south": "South", "s": "South",
        "east": "East", "e": "East",
        "west": "West", "w": "West"
    }
    return mapping.get(val)

def map_product_category(val):
    if pd.isna(val):
        return None
    val = str(val).strip().lower()
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
        "book": "Books"
    }
    return mapping.get(val)

def clean_unit_price(val):
    if pd.isna(val):
        return None
    # Remove $ , USD (case‑insensitive) and surrounding spaces
    s = str(val)
    s = s.replace('$', '')
    s = s.replace(',', '')
    s = s.replace('USD', '')
    s = s.strip()
    if s == "":
        return None
    try:
        price = float(s)
        return price
    except Exception:
        return None

def clean_quantity(val):
    if pd.isna(val):
        return None
    try:
        q = float(str(val).strip())
        if not q.is_integer():
            return None
        q_int = int(q)
        return q_int
    except Exception:
        return None

def clean_discount(val):
    if pd.isna(val) or str(val).strip() == "":
        return 0.0
    s = str(val).strip()
    if s.endswith('%'):
        s = s[:-1]
    try:
        d = float(s)
        return d
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
    df_raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df_raw)

    # R1 – strip whitespace and normalise missing values
    df = df_raw.applymap(clean_str)

    # R2 – drop duplicate order_id, keep first
    before_dup = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    dup_removed = before_dup - len(df)

    # Prepare counters for summary
    counters = {
        'duplicates_removed': dup_removed,
        'order_date_invalid': 0,
        'region_invalid': 0,
        'product_category_invalid': 0,
        'unit_price_invalid': 0,
        'quantity_invalid': 0,
        'discount_pct_invalid': 0
    }

    # R3 – order_date parsing
    df['order_date_parsed'] = df['order_date'].apply(parse_order_date)
    mask = df['order_date_parsed'].notna()
    counters['order_date_invalid'] = (~mask).sum()
    df = df[mask].copy()
    df['order_date'] = df['order_date_parsed']
    df.drop(columns=['order_date_parsed'], inplace=True)

    # R4 – region mapping
    df['region_mapped'] = df['region'].apply(map_region)
    mask = df['region_mapped'].notna()
    counters['region_invalid'] = (~mask).sum()
    df = df[mask].copy()
    df['region'] = df['region_mapped']
    df.drop(columns=['region_mapped'], inplace=True)

    # R5 – product_category mapping
    df['category_mapped'] = df['product_category'].apply(map_product_category)
    mask = df['category_mapped'].notna()
    counters['product_category_invalid'] = (~mask).sum()
    df = df[mask].copy()
    df['product_category'] = df['category_mapped']
    df.drop(columns=['category_mapped'], inplace=True)

    # R6 – unit_price cleaning
    df['unit_price_clean'] = df['unit_price'].apply(clean_unit_price)
    mask = df['unit_price_clean'].notna() & (df['unit_price_clean'] > 0) & (df['unit_price_clean'] <= 5000)
    counters['unit_price_invalid'] = (~mask).sum()
    df = df[mask].copy()
    df['unit_price'] = df['unit_price_clean']
    df.drop(columns=['unit_price_clean'], inplace=True)

    # R7 – quantity cleaning
    df['quantity_clean'] = df['quantity'].apply(clean_quantity)
    mask = df['quantity_clean'].notna() & (df['quantity_clean'] >= 1) & (df['quantity_clean'] <= 50)
    counters['quantity_invalid'] = (~mask).sum()
    df = df[mask].copy()
    df['quantity'] = df['quantity_clean']
    df.drop(columns=['quantity_clean'], inplace=True)

    # R8 – discount_pct cleaning
    df['discount_clean'] = df['discount_pct'].apply(clean_discount)
    mask = df['discount_clean'].notna() & (df['discount_clean'] >= 0) & (df['discount_clean'] <= 100)
    counters['discount_pct_invalid'] = (~mask).sum()
    df = df[mask].copy()
    df['discount_pct'] = df['discount_clean']
    df.drop(columns=['discount_clean'], inplace=True)

    # R9 – customer_id handling
    df['customer_id'] = df['customer_id'].apply(lambda x: 'UNKNOWN' if pd.isna(x) else str(x).upper())

    # Ensure correct dtypes
    df['quantity'] = df['quantity'].astype(int)
    df['unit_price'] = df['unit_price'].astype(float)
    df['discount_pct'] = df['discount_pct'].astype(float)

    # R10 – revenue calculation
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

    # R11 – final column order and sorting
    final_cols = [
        'order_id', 'order_date', 'customer_id', 'region',
        'product_category', 'quantity', 'unit_price', 'discount_pct', 'revenue'
    ]
    df = df[final_cols]
    df = df.sort_values(by='order_id')

    cleaned_rows = len(df)

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(cleaned_path, index=False)

    # Write cleaning summary JSON
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        **counters
    }
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
