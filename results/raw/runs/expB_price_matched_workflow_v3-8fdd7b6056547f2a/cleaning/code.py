import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    raw_path = os.path.join(input_dir, "raw.csv")
    
    # R1: Read every column as text, strip whitespace
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # Strip leading/trailing whitespace from all values
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    
    # R1: Treat specific values as missing
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    df = df.replace(missing_vals, np.nan)
    
    # R2: Remove duplicates based on order_id, keep first occurrence
    before_dedup = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    duplicates_removed = before_dedup - len(df)
    
    # Initialize counters for cleaning summary
    cleaning_counts = {
        'raw_rows': raw_rows,
        'duplicates_removed': duplicates_removed
    }
    
    # R3: Parse order_date
    def parse_order_date(val):
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
    
    df['order_date'] = df['order_date'].apply(parse_order_date)
    before = len(df)
    df = df.dropna(subset=['order_date'])
    cleaning_counts['dropped_invalid_dates'] = before - len(df)
    
    # R4: Map and validate region
    region_map = {
        'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West',
        'North': 'North', 'South': 'South', 'East': 'East', 'West': 'West'
    }
    def map_region(val):
        if pd.isna(val):
            return np.nan
        val_lower = str(val).strip().title()
        return region_map.get(val_lower, np.nan)
    
    df['region'] = df['region'].apply(map_region)
    before = len(df)
    df = df.dropna(subset=['region'])
    cleaning_counts['dropped_invalid_regions'] = before - len(df)
    
    # R5: Map and validate product_category
    category_map = {
        'Electronics': 'Electronics', 'Electronic': 'Electronics',
        'Clothing': 'Clothing', 'Apparel': 'Clothing',
        'Home & Garden': 'Home & Garden', 'Home And Garden': 'Home & Garden', 'Home&Garden': 'Home & Garden',
        'Sports': 'Sports', 'Sport': 'Sports',
        'Books': 'Books', 'Book': 'Books'
    }
    def map_category(val):
        if pd.isna(val):
            return np.nan
        val_clean = str(val).strip().title()
        return category_map.get(val_clean, np.nan)
    
    df['product_category'] = df['product_category'].apply(map_category)
    before = len(df)
    df = df.dropna(subset=['product_category'])
    cleaning_counts['dropped_invalid_categories'] = before - len(df)
    
    # R6: Parse unit_price
    def parse_unit_price(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip()
        # Remove $, USD, commas and surrounding spaces
        val = re.sub(r'\$|USD|,', '', val).strip()
        try:
            return float(val)
        except ValueError:
            return np.nan
    
    df['unit_price'] = df['unit_price'].apply(parse_unit_price)
    before = len(df)
    df = df.dropna(subset=['unit_price'])
    df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]
    cleaning_counts['dropped_invalid_prices'] = before - len(df)
    
    # R7: Parse quantity
    def parse_quantity(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip()
        try:
            fval = float(val)
            if fval == int(fval):
                return int(fval)
            return np.nan
        except ValueError:
            return np.nan
    
    df['quantity'] = df['quantity'].apply(parse_quantity)
    before = len(df)
    df = df.dropna(subset=['quantity'])
    df = df[(df['quantity'] >= 1) & (df['quantity'] <= 50)]
    cleaning_counts['dropped_invalid_quantities'] = before - len(df)
    
    # R8: Parse discount_pct
    def parse_discount(val):
        if pd.isna(val):
            return 0.0
        val = str(val).strip()
        # Remove trailing %
        if val.endswith('%'):
            val = val[:-1].strip()
        try:
            return float(val)
        except ValueError:
            return np.nan
    
    df['discount_pct'] = df['discount_pct'].apply(parse_discount)
    before = len(df)
    df = df.dropna(subset=['discount_pct'])
    df = df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]
    cleaning_counts['dropped_invalid_discounts'] = before - len(df)
    
    # R9: Handle customer_id
    df['customer_id'] = df['customer_id'].fillna('UNKNOWN')
    df['customer_id'] = df['customer_id'].astype(str).str.upper()
    
    # R10: Calculate revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)
    
    # R11: Sort and select final columns
    df = df.sort_values('order_id')
    final_cols = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 
                  'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[final_cols]
    
    cleaned_rows = len(df)
    cleaning_counts['cleaned_rows'] = cleaned_rows
    
    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(cleaned_path, index=False)
    
    # Write cleaning summary JSON
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(cleaning_counts, f, indent=2)

if __name__ == "__main__":
    clean_data()
