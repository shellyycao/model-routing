import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

def clean_data():
    input_dir = os.environ['INPUT_DIR']
    output_dir = os.environ['OUTPUT_DIR']
    
    # R1: Read raw CSV as text, strip whitespace, handle missing values
    df = pd.read_csv(os.path.join(input_dir, 'raw.csv'), dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # Strip whitespace from all columns
    for col in df.columns:
        df[col] = df[col].str.strip()
    
    # Define missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    # Replace missing values with NaN
    for col in df.columns:
        df[col] = df[col].apply(lambda x: np.nan if str(x).strip() in missing_vals else x)
    
    # R2: Remove duplicates based on order_id, keep first occurrence
    df = df.drop_duplicates(subset='order_id', keep='first')
    
    # R3: Parse order_date
    def parse_date(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        
        # Try YYYY-MM-DD
        try:
            return datetime.strptime(val, '%Y-%m-%d').strftime('%Y-%m-%d')
        except:
            pass
        
        # Try MM/DD/YYYY
        try:
            return datetime.strptime(val, '%m/%d/%Y').strftime('%Y-%m-%d')
        except:
            pass
        
        # Try DD-Mon-YYYY
        try:
            return datetime.strptime(val, '%d-%b-%Y').strftime('%Y-%m-%d')
        except:
            pass
        
        # Try YYYY/MM/DD
        try:
            return datetime.strptime(val, '%Y/%m/%d').strftime('%Y-%m-%d')
        except:
            pass
        
        # Try Month D, YYYY
        try:
            return datetime.strptime(val, '%B %d, %Y').strftime('%Y-%m-%d')
        except:
            pass
        
        return None
    
    df['order_date'] = df['order_date'].apply(parse_date)
    df = df.dropna(subset=['order_date'])
    
    # R4: Map region
    region_map = {
        'north': 'North',
        'south': 'South',
        'east': 'East',
        'west': 'West',
        'n': 'North',
        's': 'South',
        'e': 'East',
        'w': 'West'
    }
    
    def map_region(val):
        if pd.isna(val):
            return None
        val_lower = str(val).strip().lower()
        return region_map.get(val_lower, None)
    
    df['region'] = df['region'].apply(map_region)
    df = df.dropna(subset=['region'])
    
    # R5: Map product_category
    category_map = {
        'electronics': 'Electronics',
        'electronic': 'Electronics',
        'clothing': 'Clothing',
        'apparel': 'Clothing',
        'home & garden': 'Home & Garden',
        'home and garden': 'Home & Garden',
        'home&garden': 'Home & Garden',
        'sports': 'Sports',
        'sport': 'Sports',
        'books': 'Books',
        'book': 'Books'
    }
    
    def map_category(val):
        if pd.isna(val):
            return None
        val_lower = str(val).strip().lower()
        return category_map.get(val_lower, None)
    
    df['product_category'] = df['product_category'].apply(map_category)
    df = df.dropna(subset=['product_category'])
    
    # R6: Parse unit_price
    def parse_price(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        # Remove $, USD, commas and surrounding spaces
        val = val.replace('$', '').replace('USD', '').replace(',', '')
        val = val.strip()
        try:
            price = float(val)
            if price <= 0 or price > 5000:
                return None
            return price
        except:
            return None
    
    df['unit_price'] = df['unit_price'].apply(parse_price)
    df = df.dropna(subset=['unit_price'])
    
    # R7: Parse quantity
    def parse_quantity(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        try:
            qty = float(val)
            # Check if whole number
            if qty != int(qty):
                return None
            qty = int(qty)
            if qty < 1 or qty > 50:
                return None
            return qty
        except:
            return None
    
    df['quantity'] = df['quantity'].apply(parse_quantity)
    df = df.dropna(subset=['quantity'])
    
    # R8: Parse discount_pct
    def parse_discount(val):
        if pd.isna(val):
            return 0.0
        val = str(val).strip()
        # Remove trailing %
        if val.endswith('%'):
            val = val[:-1]
        try:
            disc = float(val)
            if disc < 0 or disc > 100:
                return None
            return disc
        except:
            return None
    
    df['discount_pct'] = df['discount_pct'].apply(parse_discount)
    df = df.dropna(subset=['discount_pct'])
    
    # R9: Handle customer_id
    df['customer_id'] = df['customer_id'].apply(lambda x: 'UNKNOWN' if pd.isna(x) else str(x).upper())
    
    # R10: Calculate revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)
    
    # R11: Sort by order_id and select columns
    df = df.sort_values('order_id')
    df = df[['order_id', 'order_date', 'customer_id', 'region', 'product_category', 'quantity', 'unit_price', 'discount_pct', 'revenue']]
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    df.to_csv(os.path.join(output_dir, 'cleaned.csv'), index=False)
    
    # Write cleaning summary
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows
    }
    
    with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()
