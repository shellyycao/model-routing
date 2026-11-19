import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

def clean_data():
    # R1: Read input, strip whitespace, standardize missing values
    input_path = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # Strip whitespace from all values
    for col in df.columns:
        df[col] = df[col].str.strip()
    
    # Standardize missing values (case-insensitive)
    missing_vals = ['', 'na', 'n/a', 'null', 'none', '-']
    for col in df.columns:
        df[col] = df[col].apply(lambda x: '' if isinstance(x, str) and x.lower() in missing_vals else x)
    
    # R2: Remove duplicates (keep first occurrence by order_id)
    before_dedup = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    duplicates_removed = before_dedup - len(df)
    
    # R3: Parse order_date
    def parse_date(val):
        if not val:
            return None
        formats = [
            '%Y-%m-%d',      # YYYY-MM-DD
            '%m/%d/%Y',      # MM/DD/YYYY
            '%d-%b-%Y',      # DD-Mon-YYYY
            '%Y/%m/%d',      # YYYY/MM/DD
            '%B %d, %Y',     # Month D, YYYY
            '%B %d,%Y'       # Month D,YYYY (no space after comma)
        ]
        for fmt in formats:
            try:
                return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None
    
    df['order_date'] = df['order_date'].apply(parse_date)
    before_r3 = len(df)
    df = df[df['order_date'].notna()]
    r3_dropped = before_r3 - len(df)
    
    # R4: Validate and map region
    region_map = {'north': 'North', 'south': 'South', 'east': 'East', 'west': 'West',
                  'n': 'North', 's': 'South', 'e': 'East', 'w': 'West'}
    df['region'] = df['region'].str.lower().map(region_map)
    before_r4 = len(df)
    df = df[df['region'].notna()]
    r4_dropped = before_r4 - len(df)
    
    # R5: Validate and map product_category
    cat_map = {
        'electronics': 'Electronics', 'electronic': 'Electronics',
        'clothing': 'Clothing', 'apparel': 'Clothing',
        'home & garden': 'Home & Garden', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden',
        'sports': 'Sports', 'sport': 'Sports',
        'books': 'Books', 'book': 'Books'
    }
    df['product_category'] = df['product_category'].str.lower().map(cat_map)
    before_r5 = len(df)
    df = df[df['product_category'].notna()]
    r5_dropped = before_r5 - len(df)
    
    # R6: Parse unit_price
    def parse_price(val):
        if not val:
            return None
        # Remove $, USD, commas and surrounding spaces
        val = val.replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            return float(val)
        except ValueError:
            return None
    
    df['unit_price'] = df['unit_price'].apply(parse_price)
    before_r6 = len(df)
    df = df[df['unit_price'].notna()]
    df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]
    r6_dropped = before_r6 - len(df)
    
    # R7: Parse quantity
    def parse_quantity(val):
        if not val:
            return None
        try:
            f = float(val)
            if f == int(f) and 1 <= f <= 50:
                return int(f)
            return None
        except ValueError:
            return None
    
    df['quantity'] = df['quantity'].apply(parse_quantity)
    before_r7 = len(df)
    df = df[df['quantity'].notna()]
    r7_dropped = before_r7 - len(df)
    
    # R8: Parse discount_pct
    def parse_discount(val):
        if not val:
            return 0.0
        val = val.rstrip('%').strip()
        try:
            f = float(val)
            if 0 <= f <= 100:
                return f
            return None
        except ValueError:
            return None
    
    df['discount_pct'] = df['discount_pct'].apply(parse_discount)
    before_r8 = len(df)
    df = df[df['discount_pct'].notna()]
    r8_dropped = before_r8 - len(df)
    
    # R9: Handle customer_id
    df['customer_id'] = df['customer_id'].apply(lambda x: 'UNKNOWN' if not x else x.upper())
    
    # R10: Calculate revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)
    
    # R11: Sort and select final columns
    df = df.sort_values('order_id')
    final_cols = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 
                  'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[final_cols]
    
    cleaned_rows = len(df)
    
    # Write outputs
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "cleaned.csv")
    df.to_csv(output_path, index=False)
    
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows,
        "duplicates_removed": duplicates_removed,
        "r3_date_dropped": r3_dropped,
        "r4_region_dropped": r4_dropped,
        "r5_category_dropped": r5_dropped,
        "r6_price_dropped": r6_dropped,
        "r7_quantity_dropped": r7_dropped,
        "r8_discount_dropped": r8_dropped
    }
    summary_path = os.path.join(os.environ["OUTPUT_DIR"], "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()