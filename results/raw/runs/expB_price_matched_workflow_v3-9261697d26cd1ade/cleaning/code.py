import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    # R1: Read raw CSV as text, strip whitespace, handle missing values
    df = pd.read_csv(os.path.join(input_dir, "raw.csv"), dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # Strip whitespace from all columns
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    
    # Define missing values and replace with np.nan
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    df = df.applymap(lambda x: np.nan if x in missing_vals else x)
    
    # R2: Remove duplicates by order_id, keep first occurrence
    before_dedup = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    duplicates_removed = before_dedup - len(df)
    
    # R3: Parse order_date
    def parse_date(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip()
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d-%b-%Y',
            '%Y/%m/%d',
            '%B %d, %Y'
        ]
        for fmt in formats:
            try:
                return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return np.nan
    
    df['order_date'] = df['order_date'].apply(parse_date)
    before_date = len(df)
    df = df[df['order_date'].notna()]
    date_dropped = before_date - len(df)
    
    # R4: Clean region
    region_map = {
        'north': 'North', 'n': 'North',
        'south': 'South', 's': 'South',
        'east': 'East', 'e': 'East',
        'west': 'West', 'w': 'West'
    }
    df['region'] = df['region'].str.lower().map(region_map)
    before_region = len(df)
    df = df[df['region'].notna()]
    region_dropped = before_region - len(df)
    
    # R5: Clean product_category
    cat_map = {
        'electronics': 'Electronics', 'electronic': 'Electronics',
        'clothing': 'Clothing', 'apparel': 'Clothing',
        'home & garden': 'Home & Garden', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden',
        'sports': 'Sports', 'sport': 'Sports',
        'books': 'Books', 'book': 'Books'
    }
    df['product_category'] = df['product_category'].str.lower().map(cat_map)
    before_cat = len(df)
    df = df[df['product_category'].notna()]
    cat_dropped = before_cat - len(df)
    
    # R6: Clean unit_price
    def clean_price(val):
        if pd.isna(val):
            return np.nan
        val = str(val).replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            return float(val)
        except:
            return np.nan
    
    df['unit_price'] = df['unit_price'].apply(clean_price)
    before_price = len(df)
    df = df[df['unit_price'].notna()]
    df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]
    price_dropped = before_price - len(df)
    
    # R7: Clean quantity
    def clean_quantity(val):
        if pd.isna(val):
            return np.nan
        try:
            f = float(val)
            if f == int(f):
                return int(f)
            return np.nan
        except:
            return np.nan
    
    df['quantity'] = df['quantity'].apply(clean_quantity)
    before_qty = len(df)
    df = df[df['quantity'].notna()]
    df = df[(df['quantity'] >= 1) & (df['quantity'] <= 50)]
    qty_dropped = before_qty - len(df)
    
    # R8: Clean discount_pct
    def clean_discount(val):
        if pd.isna(val):
            return 0.0
        val = str(val).strip().rstrip('%')
        try:
            return float(val)
        except:
            return np.nan
    
    df['discount_pct'] = df['discount_pct'].apply(clean_discount)
    before_disc = len(df)
    df = df[df['discount_pct'].notna()]
    df = df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]
    disc_dropped = before_disc - len(df)
    
    # R9: Clean customer_id
    df['customer_id'] = df['customer_id'].apply(lambda x: str(x).upper() if pd.notna(x) else 'UNKNOWN')
    df['customer_id'] = df['customer_id'].replace(['', 'NAN', 'NONE', 'NULL', 'NA', 'N/A', '-'], 'UNKNOWN')
    
    # R10: Calculate revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)
    
    # R11: Sort and select columns
    df = df.sort_values('order_id')
    cols = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[cols]
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    df.to_csv(os.path.join(output_dir, "cleaned.csv"), index=False)
    
    # Write cleaning summary
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows,
        "duplicates_removed": duplicates_removed,
        "date_parse_failures": date_dropped,
        "invalid_regions": region_dropped,
        "invalid_categories": cat_dropped,
        "invalid_prices": price_dropped,
        "invalid_quantities": qty_dropped,
        "invalid_discounts": disc_dropped
    }
    with open(os.path.join(output_dir, "cleaning_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()