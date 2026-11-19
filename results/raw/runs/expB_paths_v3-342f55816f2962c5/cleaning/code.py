import os
import pandas as pd
import numpy as np
from datetime import datetime

# Define the input and output directories
input_dir = os.environ['INPUT_DIR']
output_dir = os.environ['OUTPUT_DIR']

# Read the raw data
raw_data = pd.read_csv(os.path.join(input_dir, 'raw.csv'), dtype=str)

# R1: Strip whitespace and treat specified values as missing
missing_values = ['', 'NA', 'N/A', 'null', 'None', '-']
raw_data.replace(missing_values, np.nan, inplace=True)
raw_data = raw_data.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# R2: Remove duplicate records based on order_id
raw_data.drop_duplicates(subset='order_id', keep='first', inplace=True)

# R3: Parse order_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
raw_data['order_date'] = pd.to_datetime(raw_data['order_date'], errors='coerce', format=date_formats)
raw_data.dropna(subset=['order_date'], inplace=True)
raw_data['order_date'] = raw_data['order_date'].dt.strftime('%Y-%m-%d')

# R4: Map region
region_map = {'n': 'North','s': 'South', 'e': 'East', 'w': 'West'}
raw_data['region'] = raw_data['region'].str.lower().map(region_map).fillna(raw_data['region'].str.capitalize())
raw_data = raw_data[raw_data['region'].isin(['North', 'South', 'East', 'West']) & ~raw_data['region'].isna()]

# R5: Map product_category
product_category_map = {
    'electronic': 'Electronics', 'electronics': 'Electronics',
    'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden',
   'sport': 'Sports','sports': 'Sports',
    'apparel': 'Clothing', 'clothing': 'Clothing',
    'book': 'Books', 'books': 'Books'
}
raw_data['product_category'] = raw_data['product_category'].str.lower().map(product_category_map).fillna(raw_data['product_category'].str.capitalize())
raw_data = raw_data[raw_data['product_category'].isin(['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books']) & ~raw_data['product_category'].isna()]

# R6: Clean and parse unit_price
raw_data['unit_price'] = raw_data['unit_price'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).str.strip()
raw_data['unit_price'] = pd.to_numeric(raw_data['unit_price'], errors='coerce')
raw_data = raw_data[(raw_data['unit_price'] > 0) & (raw_data['unit_price'] <= 5000) & ~raw_data['unit_price'].isna()]

# R7: Clean and parse quantity
raw_data['quantity'] = pd.to_numeric(raw_data['quantity'], errors='coerce')
raw_data = raw_data[(raw_data['quantity'] >= 1) & (raw_data['quantity'] <= 50) & ~raw_data['quantity'].isna()]
raw_data['quantity'] = raw_data['quantity'].astype(int)

# R8: Clean and parse discount_pct
raw_data['discount_pct'] = raw_data['discount_pct'].replace('%', '', regex=True).str.strip()
raw_data['discount_pct'] = pd.to_numeric(raw_data['discount_pct'], errors='coerce')
raw_data['discount_pct'] = raw_data['discount_pct'].fillna(0)
raw_data = raw_data[(raw_data['discount_pct'] >= 0) & (raw_data['discount_pct'] <= 100) & ~raw_data['discount_pct'].isna()]

# R9: Clean customer_id
raw_data['customer_id'] = raw_data['customer_id'].str.upper().fillna('UNKNOWN')

# R10: Calculate revenue
raw_data['revenue'] = (raw_data['quantity'] * raw_data['unit_price'] * (1 - raw_data['discount_pct'] / 100)).round(2)

# R11: Select and order columns
cleaned_data = raw_data[['order_id', 'order_date', 'customer_id','region', 'product_category', 'quantity', 'unit_price', 'discount_pct','revenue']].sort_values(by='order_id')

# Write the cleaned data to CSV
output_filename = 'cleaned.csv'
cleaned_data.to_csv(os.path.join(output_dir, output_filename), index=False)

# Write the cleaning summary
cleaning_summary = {
    'raw_rows': len(raw_data),
    'cleaned_rows': len(cleaned_data),
    'dropped_duplicates': len(raw_data) - len(cleaned_data),
    'dropped_invalid_dates': len(raw_data) - len(raw_data.dropna(subset=['order_date']))
}
with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
    f.write(json.dumps(cleaning_summary, indent=4))