import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    raw_path = os.path.join(input_dir, "raw.csv")
    
    # R1: Read every column as text
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # R1: Strip whitespace and standardize missing values
    def standardize_missing(val):
        if pd.isna(val):
            return None
        val_str = str(val).strip()
        if val_str.lower() in ['', 'na', 'n/a', 'null', 'none', '-']:
            return None
        return val_str
    
    for col in df.columns:
        df[col] = df[col].apply(standardize_missing)
    
    # R2: Remove duplicates based on order_id (keep first)
    rows_before_r2 = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    count_r2 = rows_before_r2 - len(df)
    
    # R3: Parse order_date
    def parse_order_date(val):
        if val is None:
            return None
        # Format: YYYY-MM-DD
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except ValueError:
            pass
        # Format: MM/DD/YYYY
        try:
            return datetime.strptime(val, '%m/%d/%Y').date()
        except ValueError:
            pass
        # Format: DD-Mon-YYYY
        try:
            return datetime.strptime(val, '%d-%b-%Y').date()
        except ValueError:
            pass
        # Format: YYYY/MM/DD
        try:
            return datetime.strptime(val, '%Y/%m/%d').date()
        except ValueError:
            pass
        # Format: Month D, YYYY
        try:
            return datetime.strptime(val, '%B %d, %Y').date()
        except ValueError:
            pass
        return None
    
    rows_before_r3 = len(df)
    df['order_date'] = df['order_date'].apply(parse_order_date)
    df = df[df['order_date'].notna()]
    count_r3 = rows_before_r3 - len(df)
    
    # R4: Map region
    region_map = {
        'north': 'North', 'n': 'North',
        'south': 'South', 's': 'South',
        'east': 'East', 'e': 'East',
        'west': 'West', 'w': 'West'
    }
    def map_region(val):
        if val is None:
            return None
        return region_map.get(val.lower())
    
    rows_before_r4 = len(df)
    df['region'] = df['region'].apply(map_region)
    df = df[df['region'].notna()]
    count_r4 = rows_before_r4 - len(df)
    
    # R5: Map product_category
    category_map = {
        'electronics': 'Electronics', 'electronic': 'Electronics',
        'clothing': 'Clothing', 'apparel': 'Clothing',
        'home & garden': 'Home & Garden', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden',
        'sports': 'Sports', 'sport': 'Sports',
        'books': 'Books', 'book': 'Books'
    }
    def map_category(val):
        if val is None:
            return None
        return category_map.get(val.lower())
    
    rows_before_r5 = len(df)
    df['product_category'] = df['product_category'].apply(map_category)
    df = df[df['product_category'].notna()]
    count_r5 = rows_before_r5 - len(df)
    
    # R6: Parse unit_price
    def parse_unit_price(val):
        if val is None:
            return None
        # Remove $, USD, commas and surrounding spaces
        val = val.replace('$', '').replace('USD', '').replace(',', '')
        val = val.strip()
        try:
            return float(val)
        except ValueError:
            return None
    
    rows_before_r6 = len(df)
    df['unit_price'] = df['unit_price'].apply(parse_unit_price)
    df = df[df['unit_price'].notna()]
    df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]
    count_r6 = rows_before_r6 - len(df)
    
    # R7: Parse quantity
    def parse_quantity(val):
        if val is None:
            return None
        try:
            fval = float(val)
            if fval == int(fval):
                return int(fval)
            return None
        except ValueError:
            return None
    
    rows_before_r7 = len(df)
    df['quantity'] = df['quantity'].apply(parse_quantity)
    df = df[df['quantity'].notna()]
    df = df[(df['quantity'] >= 1) & (df['quantity'] <= 50)]
    count_r7 = rows_before_r7 - len(df)
    
    # R8: Parse discount_pct
    def parse_discount(val):
        if val is None:
            return 0.0
        val = val.strip()
        if val.endswith('%'):
            val = val[:-1]
        try:
            return float(val)
        except ValueError:
            return None
    
    rows_before_r8 = len(df)
    df['discount_pct'] = df['discount_pct'].apply(parse_discount)
    df = df[df['discount_pct'].notna()]
    df = df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]
    count_r8 = rows_before_r8 - len(df)
    
    # R9: Convert customer_id to uppercase, set missing to UNKNOWN
    def clean_customer_id(val):
        if val is None:
            return 'UNKNOWN'
        return val.upper()
    
    df['customer_id'] = df['customer_id'].apply(clean_customer_id)
    
    # R10: Calculate revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)
    
    # R11: Sort by order_id and select columns
    df = df.sort_values('order_id')
    output_cols = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 
                   'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[output_cols]
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    output_csv_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(output_csv_path, index=False, date_format='%Y-%m-%d')
    
    # Write cleaning summary JSON
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows,
        "duplicates_removed": count_r2,
        "invalid_dates": count_r3,
        "invalid_regions": count_r4,
        "invalid_categories": count_r5,
        "invalid_prices": count_r6,
        "invalid_quantities": count_r7,
        "invalid_discounts": count_r8
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()