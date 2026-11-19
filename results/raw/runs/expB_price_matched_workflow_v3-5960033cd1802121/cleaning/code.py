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
    cleaning_stats = {"raw_rows": raw_rows}
    
    # R1: Strip whitespace and standardize missing values
    missing_markers = {'na', 'n/a', 'null', 'none', '-'}
    
    def clean_value(val):
        if not isinstance(val, str):
            return ''
        val = val.strip()
        if val.lower() in missing_markers or val == '':
            return ''
        return val
    
    for col in df.columns:
        df[col] = df[col].apply(clean_value)
    
    # R2: Remove duplicates based on order_id
    before_dedup = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    cleaning_stats['duplicates_removed'] = before_dedup - len(df)
    
    # R3: Parse order_date
    def parse_date(val):
        if val == '':
            return None
        
        # Try YYYY-MM-DD
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except ValueError:
            pass
        
        # Try MM/DD/YYYY
        try:
            return datetime.strptime(val, '%m/%d/%Y').date()
        except ValueError:
            pass
        
        # Try DD-Mon-YYYY (e.g., 05-Mar-2024)
        try:
            return datetime.strptime(val, '%d-%b-%Y').date()
        except ValueError:
            pass
        
        # Try YYYY/MM/DD
        try:
            return datetime.strptime(val, '%Y/%m/%d').date()
        except ValueError:
            pass
        
        # Try 'Month D, YYYY' (e.g., March 5, 2024)
        try:
            return datetime.strptime(val, '%B %d, %Y').date()
        except ValueError:
            pass
        
        return None
    
    before_r3 = len(df)
    df['order_date'] = df['order_date'].apply(parse_date)
    df = df[df['order_date'].notna()]
    cleaning_stats['r3_invalid_dates_dropped'] = before_r3 - len(df)
    df['order_date'] = df['order_date'].apply(lambda x: x.strftime('%Y-%m-%d'))
    
    # R4: Clean region
    region_map = {
        'north': 'North', 'n': 'North',
        'south': 'South', 's': 'South',
        'east': 'East', 'e': 'East',
        'west': 'West', 'w': 'West'
    }
    
    before_r4 = len(df)
    df['region'] = df['region'].str.lower().map(region_map)
    df = df[df['region'].notna()]
    cleaning_stats['r4_invalid_regions_dropped'] = before_r4 - len(df)
    
    # R5: Clean product_category
    category_map = {
        'electronics': 'Electronics', 'electronic': 'Electronics',
        'clothing': 'Clothing', 'apparel': 'Clothing',
        'home & garden': 'Home & Garden', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden',
        'sports': 'Sports', 'sport': 'Sports',
        'books': 'Books', 'book': 'Books'
    }
    
    before_r5 = len(df)
    df['product_category'] = df['product_category'].str.lower().map(category_map)
    df = df[df['product_category'].notna()]
    cleaning_stats['r5_invalid_categories_dropped'] = before_r5 - len(df)
    
    # R6: Clean unit_price
    def clean_price(val):
        if val == '':
            return np.nan
        # Remove $, USD, commas and surrounding spaces
        val = re.sub(r'\$|USD|,', '', val, flags=re.IGNORECASE).strip()
        try:
            return float(val)
        except ValueError:
            return np.nan
    
    before_r6 = len(df)
    df['unit_price'] = df['unit_price'].apply(clean_price)
    df = df[df['unit_price'].notna()]
    df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]
    cleaning_stats['r6_invalid_prices_dropped'] = before_r6 - len(df)
    
    # R7: Clean quantity
    def clean_quantity(val):
        if val == '':
            return np.nan
        try:
            q = float(val)
            if q == int(q) and 1 <= q <= 50:
                return int(q)
            return np.nan
        except ValueError:
            return np.nan
    
    before_r7 = len(df)
    df['quantity'] = df['quantity'].apply(clean_quantity)
    df = df[df['quantity'].notna()]
    cleaning_stats['r7_invalid_quantities_dropped'] = before_r7 - len(df)
    
    # R8: Clean discount_pct
    def clean_discount(val):
        if val == '':
            return 0.0
        # Remove trailing %
        val = val.rstrip('%').strip()
        try:
            d = float(val)
            if 0 <= d <= 100:
                return d
            return np.nan
        except ValueError:
            return np.nan
    
    before_r8 = len(df)
    df['discount_pct'] = df['discount_pct'].apply(clean_discount)
    df = df[df['discount_pct'].notna()]
    cleaning_stats['r8_invalid_discounts_dropped'] = before_r8 - len(df)
    
    # R9: Clean customer_id
    df['customer_id'] = df['customer_id'].apply(lambda x: x.upper() if x else 'UNKNOWN')
    
    # R10: Calculate revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)
    
    # R11: Sort and select final columns
    df = df.sort_values('order_id')
    final_columns = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 
                     'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[final_columns]
    
    cleaned_rows = len(df)
    cleaning_stats['cleaned_rows'] = cleaned_rows
    
    # Write cleaned CSV
    output_csv_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(output_csv_path, index=False)
    
    # Write cleaning summary JSON
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(cleaning_stats, f, indent=2)

if __name__ == "__main__":
    clean_data()