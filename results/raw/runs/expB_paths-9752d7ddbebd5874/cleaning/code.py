import os
import json
import pandas as pd
import numpy as np
import datetime

# ---------- Helper functions ----------

def is_missing(val):
    if pd.isna(val):
        return True
    if isinstance(val, str):
        return val.strip().lower() in {"", "na", "n/a", "null", "none", "-"}
    return False

def parse_date(val):
    if pd.isna(val):
        return None
    val = val.strip()
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(val, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

REGION_MAP = {
    "n": "North",
    "north": "North",
    "s": "South",
    "south": "South",
    "e": "East",
    "east": "East",
    "w": "West",
    "west": "West",
}

def map_region(val):
    if pd.isna(val):
        return None
    key = val.strip().lower()
    return REGION_MAP.get(key)

CATEGORY_MAP = {
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

def map_category(val):
    if pd.isna(val):
        return None
    key = val.strip().lower()
    return CATEGORY_MAP.get(key)

def clean_price(val):
    if pd.isna(val):
        return None
    s = val.replace('$', '').replace('USD', '').replace(',', '').strip()
    try:
        f = float(s)
        return f
    except ValueError:
        return None

def clean_quantity(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    try:
        f = float(s)
        if not f.is_integer():
            return None
        i = int(f)
        return i
    except ValueError:
        return None

def clean_discount(val):
    if pd.isna(val) or (isinstance(val, str) and val.strip() == ""):
        return 0.0
    s = str(val).strip()
    if s.endswith('%'):
        s = s[:-1]
    try:
        f = float(s)
        return f
    except ValueError:
        return None

# ---------- Main cleaning routine ----------

def main():
    input_dir = os.environ.get('INPUT_DIR')
    output_dir = os.environ.get('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('INPUT_DIR and OUTPUT_DIR environment variables must be set')

    raw_path = os.path.join(input_dir, 'raw.csv')
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')

    # 1. Read raw CSV as text, no automatic NA handling
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)

    # 2. Strip whitespace from every cell
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # 3. Convert defined missing tokens to NaN
    missing_tokens = {"", "na", "n/a", "null", "none", "-"}
    df = df.replace(to_replace=missing_tokens, value=np.nan, regex=False)

    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": None,
        "duplicates_removed": 0,
        "rows_dropped_date": 0,
        "rows_dropped_region": 0,
        "rows_dropped_category": 0,
        "rows_dropped_price": 0,
        "rows_dropped_quantity": 0,
        "rows_dropped_discount": 0,
    }

    # R2: Remove duplicate order_id (keep first)
    dup_mask = df.duplicated(subset='order_id', keep='first')
    summary['duplicates_removed'] = int(dup_mask.sum())
    df = df[~dup_mask].copy()

    # R3: order_date parsing
    df['order_date_parsed'] = df['order_date'].apply(parse_date)
    mask_date = df['order_date_parsed'].notna()
    summary['rows_dropped_date'] = int((~mask_date).sum())
    df = df[mask_date].copy()
    df['order_date'] = df['order_date_parsed']
    df.drop(columns=['order_date_parsed'], inplace=True)

    # R4: region mapping
    df['region_mapped'] = df['region'].apply(map_region)
    mask_region = df['region_mapped'].notna()
    summary['rows_dropped_region'] = int((~mask_region).sum())
    df = df[mask_region].copy()
    df['region'] = df['region_mapped']
    df.drop(columns=['region_mapped'], inplace=True)

    # R5: product_category mapping
    df['category_mapped'] = df['product_category'].apply(map_category)
    mask_cat = df['category_mapped'].notna()
    summary['rows_dropped_category'] = int((~mask_cat).sum())
    df = df[mask_cat].copy()
    df['product_category'] = df['category_mapped']
    df.drop(columns=['category_mapped'], inplace=True)

    # R6: unit_price cleaning and validation
    df['unit_price_clean'] = df['unit_price'].apply(clean_price)
    mask_price = df['unit_price_clean'].notna() & (df['unit_price_clean'] > 0) & (df['unit_price_clean'] <= 5000)
    summary['rows_dropped_price'] = int((~mask_price).sum())
    df = df[mask_price].copy()
    df['unit_price'] = df['unit_price_clean']
    df.drop(columns=['unit_price_clean'], inplace=True)

    # R7: quantity cleaning and validation
    df['quantity_clean'] = df['quantity'].apply(clean_quantity)
    mask_qty = df['quantity_clean'].notna() & (df['quantity_clean'] >= 1) & (df['quantity_clean'] <= 50)
    summary['rows_dropped_quantity'] = int((~mask_qty).sum())
    df = df[mask_qty].copy()
    df['quantity'] = df['quantity_clean']
    df.drop(columns=['quantity_clean'], inplace=True)

    # R8: discount_pct cleaning and validation
    df['discount_clean'] = df['discount_pct'].apply(clean_discount)
    mask_disc = df['discount_clean'].notna() & (df['discount_clean'] >= 0) & (df['discount_clean'] <= 100)
    summary['rows_dropped_discount'] = int((~mask_disc).sum())
    df = df[mask_disc].copy()
    df['discount_pct'] = df['discount_clean']
    df.drop(columns=['discount_clean'], inplace=True)

    # R9: customer_id handling
    df['customer_id'] = df['customer_id'].apply(lambda x: 'UNKNOWN' if pd.isna(x) else str(x).upper())

    # Ensure correct dtypes
    df['quantity'] = df['quantity'].astype(int)
    df['unit_price'] = df['unit_price'].astype(float)
    df['discount_pct'] = df['discount_pct'].astype(float)

    # R10: revenue calculation
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

    # R11: select and order columns
    final_cols = [
        'order_id', 'order_date', 'customer_id', 'region',
        'product_category', 'quantity', 'unit_price', 'discount_pct', 'revenue'
    ]
    df = df[final_cols]
    df.sort_values(by='order_id', inplace=True)

    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False)

    # Summary
    summary['cleaned_rows'] = len(df)
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
