import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

def clean_data():
    input_dir = os.environ['INPUT_DIR']
    output_dir = os.environ['OUTPUT_DIR']
    
    # R1: Read and strip whitespace, handle missing values
    df = pd.read_csv(os.path.join(input_dir, 'raw.csv'), dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # Strip whitespace from all values
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    # Define missing values
    missing_vals = ['', 'na', 'n/a', 'null', 'none', '-']
    
    # Replace missing values with NaN for easier handling
    df = df.applymap(lambda x: np.nan if isinstance(x, str) and x.lower() in missing_vals else x)
    
    # R2: Remove duplicates based on order_id
    df = df.drop_duplicates(subset='order_id', keep='first')
    
    # R3: Parse order_date
    def parse_date(val):
        if pd.isna(val):
            return np.nan
        val = str(val)
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
    df = df.dropna(subset=['order_date'])
    
    # R4: Clean region
    region_map = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West'}
    valid_regions = ['North', 'South', 'East', 'West']
    
    def clean_region(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip().title()
        if val in valid_regions:
            return val
        if val.upper() in region_map:
            return region_map[val.upper()]
        return np.nan
    
    df['region'] = df['region'].apply(clean_region)
    df = df.dropna(subset=['region'])
    
    # R5: Clean product_category
    cat_map = {
        'electronic': 'Electronics',
        'home and garden': 'Home & Garden',
        'home&garden': 'Home & Garden',
        'sport': 'Sports',
        'apparel': 'Clothing',
        'book': 'Books'
    }
    valid_cats = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books']
    
    def clean_category(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip().lower()
        if val in cat_map:
            return cat_map[val]
        if val.title() in valid_cats:
            return val.title()
        return np.nan
    
    df['product_category'] = df['product_category'].apply(clean_category)
    df = df.dropna(subset=['product_category'])
    
    # R6: Clean unit_price
    def clean_price(val):
        if pd.isna(val):
            return np.nan
        val = str(val).replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            price = float(val)
            if price <= 0 or price > 5000:
                return np.nan
            return price
        except ValueError:
            return np.nan
    
    df['unit_price'] = df['unit_price'].apply(clean_price)
    df = df.dropna(subset=['unit_price'])
    
    # R7: Clean quantity
    def clean_quantity(val):
        if pd.isna(val):
            return np.nan
        try:
            qty = float(str(val).strip())
            if qty < 1 or qty > 50 or not qty.is_integer():
                return np.nan
            return int(qty)
        except ValueError:
            return np.nan
    
    df['quantity'] = df['quantity'].apply(clean_quantity)
    df = df.dropna(subset=['quantity'])
    
    # R8: Clean discount_pct
    def clean_discount(val):
        if pd.isna(val):
            return 0.0
        val = str(val).strip().rstrip('%')
        try:
            disc = float(val)
            if disc < 0 or disc > 100:
                return np.nan
            return disc
        except ValueError:
            return np.nan
    
    df['discount_pct'] = df['discount_pct'].apply(clean_discount)
    df = df.dropna(subset=['discount_pct'])
    
    # R9: Clean customer_id
    df['customer_id'] = df['customer_id'].apply(lambda x: str(x).upper() if pd.notna(x) else 'UNKNOWN')
    df['customer_id'] = df['customer_id'].replace('NAN', 'UNKNOWN')
    
    # R10: Calculate revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)
    
    # R11: Sort and select columns
    df = df.sort_values('order_id')
    cols = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 
            'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[cols]
    
    cleaned_rows = len(df)
    
    # Write outputs
    df.to_csv(os.path.join(output_dir, 'cleaned.csv'), index=False)
    
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows
    }
    with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()