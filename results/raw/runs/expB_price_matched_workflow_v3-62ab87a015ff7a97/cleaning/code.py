import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    # Read raw data
    raw_path = os.path.join(input_dir, "raw.csv")
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # Initialize summary stats
    stats = {
        'raw_rows': raw_rows,
        'duplicates_removed': 0,
        'invalid_order_date': 0,
        'invalid_region': 0,
        'invalid_category': 0,
        'invalid_price': 0,
        'invalid_quantity': 0,
        'invalid_discount': 0
    }
    
    # R1: Strip whitespace and standardize missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    for col in df.columns:
        df[col] = df[col].str.strip()
        df[col] = df[col].apply(lambda x: '' if x in missing_vals else x)
    
    # R2: Remove duplicates (keep first occurrence)
    before_dedup = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    stats['duplicates_removed'] = before_dedup - len(df)
    
    # R3: Parse order_date
    def parse_date(val):
        if not val:
            return None
        # Try YYYY-MM-DD
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except:
            pass
        # Try MM/DD/YYYY
        try:
            return datetime.strptime(val, '%m/%d/%Y').date()
        except:
            pass
        # Try DD-Mon-YYYY
        try:
            return datetime.strptime(val, '%d-%b-%Y').date()
        except:
            pass
        # Try YYYY/MM/DD
        try:
            return datetime.strptime(val, '%Y/%m/%d').date()
        except:
            pass
        # Try Month D, YYYY
        try:
            return datetime.strptime(val, '%B %d, %Y').date()
        except:
            pass
        return None
    
    df['order_date_parsed'] = df['order_date'].apply(parse_date)
    before_date = len(df)
    df = df[df['order_date_parsed'].notna()]
    stats['invalid_order_date'] = before_date - len(df)
    df['order_date'] = df['order_date_parsed'].apply(lambda x: x.strftime('%Y-%m-%d'))
    df = df.drop(columns=['order_date_parsed'])
    
    # R4: Validate and map region
    region_map = {
        'NORTH': 'North', 'N': 'North',
        'SOUTH': 'South', 'S': 'South',
        'EAST': 'East', 'E': 'East',
        'WEST': 'West', 'W': 'West'
    }
    df['region_upper'] = df['region'].str.upper()
    df['region'] = df['region_upper'].map(region_map)
    before_region = len(df)
    df = df[df['region'].notna()]
    stats['invalid_region'] = before_region - len(df)
    df = df.drop(columns=['region_upper'])
    
    # R5: Validate and map product_category
    cat_map = {
        'ELECTRONICS': 'Electronics', 'ELECTRONIC': 'Electronics',
        'CLOTHING': 'Clothing', 'APPAREL': 'Clothing',
        'HOME & GARDEN': 'Home & Garden', 'HOME AND GARDEN': 'Home & Garden', 'HOME&GARDEN': 'Home & Garden',
        'SPORTS': 'Sports', 'SPORT': 'Sports',
        'BOOKS': 'Books', 'BOOK': 'Books'
    }
    df['cat_upper'] = df['product_category'].str.upper()
    df['product_category'] = df['cat_upper'].map(cat_map)
    before_cat = len(df)
    df = df[df['product_category'].notna()]
    stats['invalid_category'] = before_cat - len(df)
    df = df.drop(columns=['cat_upper'])
    
    # R6: Parse unit_price
    def parse_price(val):
        if not val:
            return None
        # Remove $, USD, commas and surrounding spaces
        val = re.sub(r'\$|USD|,', '', val, flags=re.IGNORECASE).strip()
        try:
            price = float(val)
            return price
        except:
            return None
    
    df['unit_price'] = df['unit_price'].apply(parse_price)
    before_price = len(df)
    df = df[(df['unit_price'].notna()) & (df['unit_price'] > 0) & (df['unit_price'] <= 5000)]
    stats['invalid_price'] = before_price - len(df)
    
    # R7: Parse quantity
    def parse_quantity(val):
        if not val:
            return None
        try:
            q = float(val)
            if q == int(q) and 1 <= q <= 50:
                return int(q)
            return None
        except:
            return None
    
    df['quantity'] = df['quantity'].apply(parse_quantity)
    before_qty = len(df)
    df = df[df['quantity'].notna()]
    stats['invalid_quantity'] = before_qty - len(df)
    
    # R8: Parse discount_pct
    def parse_discount(val):
        if not val:
            return 0.0
        # Remove trailing %
        val = val.rstrip('%').strip()
        try:
            d = float(val)
            if 0 <= d <= 100:
                return d
            return None
        except:
            return None
    
    df['discount_pct'] = df['discount_pct'].apply(parse_discount)
    before_disc = len(df)
    df = df[df['discount_pct'].notna()]
    stats['invalid_discount'] = before_disc - len(df)
    
    # R9: Handle customer_id
    df['customer_id'] = df['customer_id'].apply(lambda x: x.upper() if x else 'UNKNOWN')
    
    # R10: Calculate revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)
    
    # R11: Sort and select final columns
    df = df.sort_values('order_id')
    final_cols = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 
                  'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[final_cols]
    
    cleaned_rows = len(df)
    stats['cleaned_rows'] = cleaned_rows
    
    # Write cleaned CSV
    output_csv = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(output_csv, index=False)
    
    # Write cleaning summary
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(stats, f, indent=2)

if __name__ == "__main__":
    clean_data()
