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
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    
    raw_rows = len(df)
    cleaning_stats = {'raw_rows': raw_rows}
    
    # R1: Strip whitespace and standardize missing values
    missing_vals = ['', 'na', 'n/a', 'null', 'none', '-']
    
    def clean_value(x):
        if isinstance(x, str):
            x = x.strip()
            if x.lower() in missing_vals:
                return np.nan
        return x
    
    for col in df.columns:
        df[col] = df[col].apply(clean_value)
    
    # R2: Remove duplicates (keep first occurrence)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['order_id'], keep='first')
    cleaning_stats['duplicates_removed'] = before_dedup - len(df)
    
    # R3: Parse order_date
    date_formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d-%b-%Y',
        '%Y/%m/%d',
        '%B %d, %Y',
        '%B %d,%Y' # Handle missing space after comma just in case
    ]
    
    def parse_date(x):
        if pd.isna(x):
            return np.nan
        for fmt in date_formats:
            try:
                return datetime.strptime(x, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return np.nan
    
    df['order_date'] = df['order_date'].apply(parse_date)
    before_date = len(df)
    df = df.dropna(subset=['order_date'])
    cleaning_stats['invalid_dates_dropped'] = before_date - len(df)
    
    # R4: Clean region
    region_map = {
        'north': 'North', 'n': 'North',
        'south': 'South', 's': 'South',
        'east': 'East', 'e': 'East',
        'west': 'West', 'w': 'West'
    }
    
    def clean_region(x):
        if pd.isna(x):
            return np.nan
        return region_map.get(str(x).lower(), np.nan)
    
    df['region'] = df['region'].apply(clean_region)
    before_region = len(df)
    df = df.dropna(subset=['region'])
    cleaning_stats['invalid_regions_dropped'] = before_region - len(df)
    
    # R5: Clean product_category
    category_map = {
        'electronics': 'Electronics', 'electronic': 'Electronics',
        'clothing': 'Clothing', 'apparel': 'Clothing',
        'home & garden': 'Home & Garden', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden',
        'sports': 'Sports', 'sport': 'Sports',
        'books': 'Books', 'book': 'Books'
    }
    
    def clean_category(x):
        if pd.isna(x):
            return np.nan
        return category_map.get(str(x).lower(), np.nan)
    
    df['product_category'] = df['product_category'].apply(clean_category)
    before_cat = len(df)
    df = df.dropna(subset=['product_category'])
    cleaning_stats['invalid_categories_dropped'] = before_cat - len(df)
    
    # R6: Clean unit_price
    def clean_price(x):
        if pd.isna(x):
            return np.nan
        # Remove $, USD, commas and surrounding spaces
        x = re.sub(r'\$|USD|,', '', str(x)).strip()
        try:
            val = float(x)
            if not (0 < val <= 5000):
                return np.nan
            return val
        except ValueError:
            return np.nan
    
    df['unit_price'] = df['unit_price'].apply(clean_price)
    before_price = len(df)
    df = df.dropna(subset=['unit_price'])
    cleaning_stats['invalid_prices_dropped'] = before_price - len(df)
    
    # R7: Clean quantity
    def clean_quantity(x):
        if pd.isna(x):
            return np.nan
        try:
            val = float(str(x).strip())
            if val == int(val) and 1 <= val <= 50:
                return int(val)
            return np.nan
        except ValueError:
            return np.nan
    
    df['quantity'] = df['quantity'].apply(clean_quantity)
    before_qty = len(df)
    df = df.dropna(subset=['quantity'])
    cleaning_stats['invalid_quantities_dropped'] = before_qty - len(df)
    
    # R8: Clean discount_pct
    def clean_discount(x):
        if pd.isna(x):
            return 0.0
        x = str(x).strip()
        if x.endswith('%'):
            x = x[:-1]
        try:
            val = float(x)
            if 0 <= val <= 100:
                return val
            return np.nan
        except ValueError:
            return np.nan
    
    df['discount_pct'] = df['discount_pct'].apply(clean_discount)
    before_disc = len(df)
    df = df.dropna(subset=['discount_pct'])
    cleaning_stats['invalid_discounts_dropped'] = before_disc - len(df)
    
    # R9: Clean customer_id
    df['customer_id'] = df['customer_id'].apply(lambda x: str(x).upper() if pd.notna(x) else 'UNKNOWN')
    df.loc[df['customer_id'] == 'NAN', 'customer_id'] = 'UNKNOWN' # Handle case where original was NaN
    df.loc[df['customer_id'].str.strip() == '', 'customer_id'] = 'UNKNOWN'
    
    # R10: Calculate revenue
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)
    
    # R11: Sort and select columns
    df = df.sort_values(by='order_id', ascending=True)
    final_cols = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 
                  'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[final_cols]
    
    cleaned_rows = len(df)
    cleaning_stats['cleaned_rows'] = cleaned_rows
    
    # Write outputs
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(cleaned_path, index=False)
    
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(cleaning_stats, f, indent=2)

if __name__ == "__main__":
    clean_data()