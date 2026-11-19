import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

def clean_data():
    input_path = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
    output_csv_path = os.path.join(os.environ["OUTPUT_DIR"], "cleaned.csv")
    output_json_path = os.path.join(os.environ["OUTPUT_DIR"], "cleaning_summary.json")

    # R1: Read as text, strip whitespace, map missing values
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    missing_values = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    def clean_value(val):
        if pd.isna(val):
            return np.nan
        val_str = str(val).strip()
        if val_str.lower() in [m.lower() for m in missing_values]:
            return np.nan
        return val_str

    for col in df.columns:
        df[col] = df[col].apply(clean_value)
    
    # R2: Remove duplicates based on order_id
    before_dedup = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    duplicates_removed = before_dedup - len(df)

    # R3: Parse order_date
    def parse_date(val):
        if pd.isna(val):
            return None
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
        return None

    df['order_date'] = df['order_date'].apply(parse_date)
    before_date = len(df)
    df = df[df['order_date'].notna()]
    date_invalid = before_date - len(df)

    # R4: Clean region
    region_map = {
        'north': 'North', 'south': 'South', 'east': 'East', 'west': 'West',
        'n': 'North', 's': 'South', 'e': 'East', 'w': 'West'
    }
    def clean_region(val):
        if pd.isna(val):
            return None
        return region_map.get(str(val).lower().strip(), None)
    
    df['region'] = df['region'].apply(clean_region)
    before_region = len(df)
    df = df[df['region'].notna()]
    region_invalid = before_region - len(df)

    # R5: Clean product_category
    category_map = {
        'electronics': 'Electronics', 'electronic': 'Electronics',
        'clothing': 'Clothing', 'apparel': 'Clothing',
        'home & garden': 'Home & Garden', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden',
        'sports': 'Sports', 'sport': 'Sports',
        'books': 'Books', 'book': 'Books'
    }
    def clean_category(val):
        if pd.isna(val):
            return None
        return category_map.get(str(val).lower().strip(), None)
    
    df['product_category'] = df['product_category'].apply(clean_category)
    before_cat = len(df)
    df = df[df['product_category'].notna()]
    category_invalid = before_cat - len(df)

    # R6: Clean unit_price
    def clean_price(val):
        if pd.isna(val):
            return None
        val = str(val).replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            return float(val)
        except ValueError:
            return None
    
    df['unit_price'] = df['unit_price'].apply(clean_price)
    before_price = len(df)
    df = df[df['unit_price'].notna()]
    df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]
    price_invalid = before_price - len(df)

    # R7: Clean quantity
    def clean_quantity(val):
        if pd.isna(val):
            return None
        try:
            f = float(str(val).strip())
            if f == int(f):
                return int(f)
            return None
        except ValueError:
            return None
    
    df['quantity'] = df['quantity'].apply(clean_quantity)
    before_qty = len(df)
    df = df[df['quantity'].notna()]
    df = df[(df['quantity'] >= 1) & (df['quantity'] <= 50)]
    quantity_invalid = before_qty - len(df)

    # R8: Clean discount_pct
    def clean_discount(val):
        if pd.isna(val):
            return 0.0
        val = str(val).strip()
        if val.endswith('%'):
            val = val[:-1].strip()
        try:
            return float(val)
        except ValueError:
            return None
    
    df['discount_pct'] = df['discount_pct'].apply(clean_discount)
    before_disc = len(df)
    df = df[df['discount_pct'].notna()]
    df = df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]
    discount_invalid = before_disc - len(df)

    # R9: Clean customer_id
    df['customer_id'] = df['customer_id'].apply(lambda x: str(x).upper() if pd.notna(x) else 'UNKNOWN')
    df['customer_id'] = df['customer_id'].replace('NAN', 'UNKNOWN')

    # R10: Calculate revenue
    df['revenue'] = df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)
    df['revenue'] = df['revenue'].round(2)

    # R11: Sort and select columns
    df = df.sort_values('order_id')
    columns = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 'quantity', 'unit_price', 'discount_pct', 'revenue']
    df = df[columns]
    
    cleaned_rows = len(df)
    
    # Write outputs
    df.to_csv(output_csv_path, index=False)
    
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed': duplicates_removed,
        'date_invalid': date_invalid,
        'region_invalid': region_invalid,
        'category_invalid': category_invalid,
        'price_invalid': price_invalid,
        'quantity_invalid': quantity_invalid,
        'discount_invalid': discount_invalid
    }
    
    with open(output_json_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()