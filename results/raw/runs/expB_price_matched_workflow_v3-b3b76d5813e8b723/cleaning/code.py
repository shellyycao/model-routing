import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def parse_order_date(val):
    """Parse date string using specified formats."""
    if not val:
        return None
    val = str(val).strip()
    
    formats = [
        '%Y-%m-%d',       # YYYY-MM-DD
        '%m/%d/%Y',       # MM/DD/YYYY
        '%d-%b-%Y',       # DD-Mon-YYYY
        '%Y/%m/%d',       # YYYY/MM/DD
        '%B %d, %Y',      # Month D, YYYY
        '%B %d,%Y'        # Month D,YYYY (no space after comma)
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None

def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    # R1: Read all columns as text
    df = pd.read_csv(os.path.join(input_dir, "raw.csv"), dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # R1: Strip whitespace and standardize missing values
    missing_vals = {'', 'na', 'n/a', 'null', 'none', '-'}
    
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].apply(lambda x: '' if x.lower() in missing_vals else x)
    
    # R2: Remove duplicates (keep first occurrence)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['order_id'], keep='first')
    duplicates_removed = before_dedup - len(df)
    
    # R3: Parse order_date
    df['order_date'] = df['order_date'].apply(parse_order_date)
    before_date_filter = len(df)
    df = df[df['order_date'].notna()]
    dropped_invalid_dates = before_date_filter - len(df)
    
    # R4: Clean region
    region_map = {
        'north': 'North', 'n': 'North',
        'south': 'South', 's': 'South',
        'east': 'East', 'e': 'East',
        'west': 'West', 'w': 'West'
    }
    df['region'] = df['region'].str.lower().map(region_map)
    before_region_filter = len(df)
    df = df[df['region'].notna()]
    dropped_invalid_regions = before_region_filter - len(df)
    
    # R5: Clean product_category
    category_map = {
        'electronics': 'Electronics', 'electronic': 'Electronics',
        'clothing': 'Clothing', 'apparel': 'Clothing',
        'home & garden': 'Home & Garden', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden',
        'sports': 'Sports', 'sport': 'Sports',
        'books': 'Books', 'book': 'Books'
    }
    df['product_category'] = df['product_category'].str.lower().map(category_map)
    before_cat_filter = len(df)
    df = df[df['product_category'].notna()]
    dropped_invalid_categories = before_cat_filter - len(df)
    
    # R6: Clean unit_price
    def clean_price(val):
        if not val:
            return np.nan
        val = str(val).replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            return float(val)
        except ValueError:
            return np.nan
    
    df['unit_price'] = df['unit_price'].apply(clean_price)
    before_price_filter = len(df)
    df = df[df['unit_price'].notna()]
    df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]
    dropped_invalid_prices = before_price_filter - len(df)
    
    # R7: Clean quantity
    def clean_quantity(val):
        if not val:
            return np.nan
        try:
            f = float(val)
            if f == int(f):
                return int(f)
            return np.nan
        except ValueError:
            return np.nan
    
    df['quantity'] = df['quantity'].apply(clean_quantity)
    before_qty_filter = len(df)
    df = df[df['quantity'].notna()]
    df = df[(df['quantity'] >= 1) & (df['quantity'] <= 50)]
    dropped_invalid_quantity = before_qty_filter - len(df)
    
    # R8: Clean discount_pct
    def clean_discount(val):
        if not val:
            return 0.0
        val = str(val).strip().rstrip('%')
        try:
            return float(val)
        except ValueError:
            return np.nan
    
    df['discount_pct'] = df['discount_pct'].apply(clean_discount)
    before_disc_filter = len(df)
    df = df[df['discount_pct'].notna()]
    df = df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]
    dropped_invalid_discount = before_disc_filter - len(df)
    
    # R9: Clean customer_id
    df['customer_id'] = df['customer_id'].apply(lambda x: str(x).upper() if x else 'UNKNOWN')
    df['customer_id'] = df['customer_id'].replace('', 'UNKNOWN')
    
    # R10: Calculate revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)
    
    # R11: Sort and select columns
    df = df.sort_values('order_id')
    output_cols = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 
                   'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[output_cols]
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    df.to_csv(os.path.join(output_dir, "cleaned.csv"), index=False, date_format='%Y-%m-%d')
    
    # Write cleaning summary
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed': duplicates_removed,
        'dropped_invalid_dates': dropped_invalid_dates,
        'dropped_invalid_regions': dropped_invalid_regions,
        'dropped_invalid_categories': dropped_invalid_categories,
        'dropped_invalid_prices': dropped_invalid_prices,
        'dropped_invalid_quantity': dropped_invalid_quantity,
        'dropped_invalid_discount': dropped_invalid_discount
    }
    
    with open(os.path.join(output_dir, "cleaning_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
