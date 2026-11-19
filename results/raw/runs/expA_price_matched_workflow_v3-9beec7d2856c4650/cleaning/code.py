import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def parse_order_date(val):
    """Parse date string according to specified formats."""
    if not val:
        return None
    val = str(val).strip()
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

def main():
    input_dir = os.environ.get('INPUT_DIR', '.')
    output_dir = os.environ.get('OUTPUT_DIR', '.')
    
    raw_path = os.path.join(input_dir, 'raw.csv')
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    
    # R1: Read all columns as text, strip whitespace, handle missing values
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    
    # Strip whitespace from all values
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    
    # Define missing values
    missing_vals = ['', 'NA', 'N/A', 'NULL', 'NONE', '-']
    
    # Replace missing values with actual NaN for easier handling
    df = df.applymap(lambda x: np.nan if isinstance(x, str) and x.upper() in missing_vals else x)
    
    raw_rows = len(df)
    
    # R2: Remove duplicates based on order_id, keep first occurrence
    before_dedup = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    duplicates_removed = before_dedup - len(df)
    
    # R3: Parse order_date, drop invalid/missing
    before_r3 = len(df)
    df['order_date_parsed'] = df['order_date'].apply(parse_order_date)
    df = df[df['order_date_parsed'].notna()]
    df['order_date'] = df['order_date_parsed'].apply(lambda x: x.strftime('%Y-%m-%d'))
    df = df.drop(columns=['order_date_parsed'])
    r3_dropped = before_r3 - len(df)
    
    # R4: Map region, drop invalid/missing
    before_r4 = len(df)
    region_map = {
        'NORTH': 'North', 'N': 'North',
        'SOUTH': 'South', 'S': 'South',
        'EAST': 'East', 'E': 'East',
        'WEST': 'West', 'W': 'West'
    }
    df['region'] = df['region'].str.upper()
    df['region'] = df['region'].map(region_map)
    df = df[df['region'].notna()]
    r4_dropped = before_r4 - len(df)
    
    # R5: Map product_category, drop invalid/missing
    before_r5 = len(df)
    cat_map = {
        'ELECTRONICS': 'Electronics', 'ELECTRONIC': 'Electronics',
        'CLOTHING': 'Clothing', 'APPAREL': 'Clothing',
        'HOME & GARDEN': 'Home & Garden', 'HOME AND GARDEN': 'Home & Garden', 'HOME&GARDEN': 'Home & Garden',
        'SPORTS': 'Sports', 'SPORT': 'Sports',
        'BOOKS': 'Books', 'BOOK': 'Books'
    }
    df['product_category'] = df['product_category'].str.upper()
    df['product_category'] = df['product_category'].map(cat_map)
    df = df[df['product_category'].notna()]
    r5_dropped = before_r5 - len(df)
    
    # R6: Parse unit_price, drop invalid/missing/out of range
    before_r6 = len(df)
    def parse_unit_price(val):
        if pd.isna(val):
            return np.nan
        val = str(val)
        # Remove $, USD, commas and surrounding spaces
        val = re.sub(r'\$|USD|,', '', val).strip()
        try:
            return float(val)
        except ValueError:
            return np.nan
    df['unit_price'] = df['unit_price'].apply(parse_unit_price)
    df = df[df['unit_price'].notna()]
    df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]
    r6_dropped = before_r6 - len(df)
    
    # R7: Parse quantity, drop invalid/missing/out of range
    before_r7 = len(df)
    def parse_quantity(val):
        if pd.isna(val):
            return np.nan
        try:
            fval = float(val)
            if fval == int(fval):
                return int(fval)
            return np.nan
        except ValueError:
            return np.nan
    df['quantity'] = df['quantity'].apply(parse_quantity)
    df = df[df['quantity'].notna()]
    df = df[(df['quantity'] >= 1) & (df['quantity'] <= 50)]
    r7_dropped = before_r7 - len(df)
    
    # R8: Parse discount_pct, set missing to 0, drop invalid/out of range
    before_r8 = len(df)
    def parse_discount(val):
        if pd.isna(val):
            return 0.0
        val = str(val).strip()
        if val.endswith('%'):
            val = val[:-1].strip()
        try:
            return float(val)
        except ValueError:
            return np.nan
    df['discount_pct'] = df['discount_pct'].apply(parse_discount)
    df = df[df['discount_pct'].notna()]
    df = df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]
    r8_dropped = before_r8 - len(df)
    
    # R9: Convert customer_id to uppercase, set missing to 'UNKNOWN'
    df['customer_id'] = df['customer_id'].fillna('UNKNOWN')
    df['customer_id'] = df['customer_id'].astype(str).str.upper()
    df['customer_id'] = df['customer_id'].replace(['', 'NA', 'N/A', 'NULL', 'NONE', '-'], 'UNKNOWN')
    
    # R10: Calculate revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)
    
    # R11: Select and order columns, sort by order_id
    columns_order = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 
                     'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[columns_order]
    df = df.sort_values('order_id')
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False)
    
    # Write cleaning summary JSON
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed': duplicates_removed,
        'r3_date_invalid_dropped': r3_dropped,
        'r4_region_invalid_dropped': r4_dropped,
        'r5_category_invalid_dropped': r5_dropped,
        'r6_price_invalid_dropped': r6_dropped,
        'r7_quantity_invalid_dropped': r7_dropped,
        'r8_discount_invalid_dropped': r8_dropped
    }
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
