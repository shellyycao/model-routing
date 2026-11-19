import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # R1: Read as text, strip whitespace, handle missing values
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # Strip whitespace from all columns
    for col in df.columns:
        df[col] = df[col].str.strip()
    
    # Define missing values
    missing_vals = ['', 'na', 'n/a', 'null', 'none', '-']
    
    # Replace missing values with NaN for easier handling
    df = df.applymap(lambda x: np.nan if isinstance(x, str) and x.lower() in missing_vals else x)
    
    # R2: Remove duplicates based on order_id, keep first occurrence
    before_dedup = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    duplicates_removed = before_dedup - len(df)
    
    # R3: Parse order_date
    def parse_date(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        formats = [
            '%Y-%m-%d',      # 2023-01-04
            '%m/%d/%Y',      # 01/05/2023
            '%d-%b-%Y',      # 05-Mar-2024
            '%Y/%m/%d',      # 2023/01/13
            '%B %d, %Y',     # March 5, 2024
            '%B %d,%Y'       # March 5,2024 (no space after comma)
        ]
        for fmt in formats:
            try:
                return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None
    
    df['order_date'] = df['order_date'].apply(parse_date)
    before_date = len(df)
    df = df[df['order_date'].notna()]
    dropped_date = before_date - len(df)
    
    # R4: Map region
    region_map = {
        'north': 'North', 'n': 'North',
        'south': 'South', 's': 'South',
        'east': 'East', 'e': 'East',
        'west': 'West', 'w': 'West'
    }
    df['region'] = df['region'].apply(lambda x: region_map.get(str(x).lower(), None) if pd.notna(x) else None)
    before_region = len(df)
    df = df[df['region'].notna()]
    dropped_region = before_region - len(df)
    
    # R5: Map product_category
    category_map = {
        'electronics': 'Electronics', 'electronic': 'Electronics',
        'clothing': 'Clothing', 'apparel': 'Clothing',
        'home & garden': 'Home & Garden', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden',
        'sports': 'Sports', 'sport': 'Sports',
        'books': 'Books', 'book': 'Books'
    }
    df['product_category'] = df['product_category'].apply(lambda x: category_map.get(str(x).lower(), None) if pd.notna(x) else None)
    before_category = len(df)
    df = df[df['product_category'].notna()]
    dropped_category = before_category - len(df)
    
    # R6: Parse unit_price
    def parse_price(val):
        if pd.isna(val):
            return None
        val = str(val).replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            price = float(val)
            return price if 0 < price <= 5000 else None
        except ValueError:
            return None
    
    df['unit_price'] = df['unit_price'].apply(parse_price)
    before_price = len(df)
    df = df[df['unit_price'].notna()]
    dropped_price = before_price - len(df)
    
    # R7: Parse quantity
    def parse_quantity(val):
        if pd.isna(val):
            return None
        try:
            qty = float(str(val).strip())
            if qty.is_integer() and 1 <= qty <= 50:
                return int(qty)
            return None
        except ValueError:
            return None
    
    df['quantity'] = df['quantity'].apply(parse_quantity)
    before_qty = len(df)
    df = df[df['quantity'].notna()]
    dropped_qty = before_qty - len(df)
    
    # R8: Parse discount_pct
    def parse_discount(val):
        if pd.isna(val):
            return 0.0
        val = str(val).strip().rstrip('%')
        try:
            disc = float(val)
            return disc if 0 <= disc <= 100 else None
        except ValueError:
            return None
    
    df['discount_pct'] = df['discount_pct'].apply(parse_discount)
    before_disc = len(df)
    df = df[df['discount_pct'].notna()]
    dropped_disc = before_disc - len(df)
    
    # R9: Handle customer_id
    df['customer_id'] = df['customer_id'].apply(lambda x: str(x).upper() if pd.notna(x) else 'UNKNOWN')
    df['customer_id'] = df['customer_id'].replace('UNKNOWN', 'UNKNOWN')
    
    # R10: Calculate revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)
    
    # R11: Sort by order_id and select final columns
    df = df.sort_values('order_id')
    final_cols = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 
                  'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[final_cols]
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False)
    
    # Write cleaning summary
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed': duplicates_removed,
        'dropped_invalid_date': dropped_date,
        'dropped_invalid_region': dropped_region,
        'dropped_invalid_category': dropped_category,
        'dropped_invalid_price': dropped_price,
        'dropped_invalid_quantity': dropped_qty,
        'dropped_invalid_discount': dropped_disc
    }
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()
