import os
import pandas as pd
import numpy as np
from datetime import datetime

# Define the input and output directories
input_dir = os.environ['INPUT_DIR']
output_dir = os.environ['OUTPUT_DIR']

# Read the raw data
df = pd.read_csv(os.path.join(input_dir, 'raw.csv'), dtype=str)

# R1: Strip whitespace and treat certain values as missing
missing_values = ['NA', 'N/A', 'null', 'None', '-']
df.replace(missing_values, np.nan, inplace=True)
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# R2: Remove duplicate records
df.drop_duplicates(subset=['order_id'], keep='first', inplace=True)

# R3: Parse order_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
df['order_date'] = pd.to_datetime(df['order_date'], format=date_formats, errors='coerce')
df.dropna(subset=['order_date'], inplace=True)
df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')

# R4: Map region
region_map = {'n': 'North','s': 'South', 'e': 'East', 'w': 'West'}
df['region'] = df['region'].str.lower().map(lambda x: region_map.get(x[0], x) if x else np.nan)
df['region'] = df['region'].str.title()
df.dropna(subset=['region'], inplace=True)
df['region'] = pd.Categorical(df['region'], categories=['North', 'South', 'East', 'West'])

# R5: Map product_category
product_category_map = {
    'electronic': 'Electronics', 'electronics': 'Electronics',
    'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden',
   'sport': 'Sports','sports': 'Sports',
    'apparel': 'Clothing', 'clothing': 'Clothing',
    'book': 'Books', 'books': 'Books'
}
df['product_category'] = df['product_category'].str.lower().map(product_category_map)
df.dropna(subset=['product_category'], inplace=True)
df['product_category'] = pd.Categorical(df['product_category'], categories=['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books'])

# R6: Clean and parse unit_price
df['unit_price'] = df['unit_price'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).str.strip()
df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
df.dropna(subset=['unit_price'], inplace=True)
df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]

# R7: Clean and parse quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df.dropna(subset=['quantity'], inplace=True)
df = df[(df['quantity'] >= 1) & (df['quantity'] <= 50)]
df['quantity'] = df['quantity'].astype(int)

# R8: Clean and parse discount_pct
df['discount_pct'] = df['discount_pct'].replace('%', '', regex=True).str.strip()
df['discount_pct'] = pd.to_numeric(df['discount_pct'], errors='coerce').fillna(0)
df.dropna(subset=['discount_pct'], inplace=True)
df = df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]

# R9: Clean customer_id
df['customer_id'] = df['customer_id'].str.upper().fillna('UNKNOWN')

# R10: Calculate revenue
df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

# R11: Select and order columns
df = df[['order_id', 'order_date', 'customer_id','region', 'product_category', 'quantity', 'unit_price', 'discount_pct','revenue']]
df.sort_values(by='order_id', inplace=True)

# Write the cleaned data to CSV
output_filename = 'cleaned.csv'
df.to_csv(os.path.join(output_dir, output_filename), index=False)

# Write cleaning summary
cleaning_summary = {
    'raw_rows': len(pd.read_csv(os.path.join(input_dir, 'raw.csv'))),
    'cleaned_rows': len(df),
    'dropped_duplicates': df.duplicated(subset=['order_id']).sum(),
    'dropped_missing_order_date': df['order_date'].isna().sum(),
    'dropped_invalid_region': df['region'].isna().sum(),
    'dropped_invalid_product_category': df['product_category'].isna().sum(),
    'dropped_invalid_unit_price': df['unit_price'].isna().sum(),
    'dropped_invalid_quantity': df['quantity'].isna().sum(),
    'dropped_invalid_discount_pct': df['discount_pct'].isna().sum()
}
with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
    f.write(json.dumps(cleaning_summary, indent=2))