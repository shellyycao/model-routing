import os
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Constants
MISSING_VALUES = ['NA', 'N/A', 'null', 'None', '-']
REGION_MAP = {'north': 'North','south': 'South', 'east': 'East', 'west': 'West', 'n': 'North','s': 'South', 'e': 'East', 'w': 'West'}
PRODUCT_CATEGORY_MAP = {'electronic': 'Electronics', 'electronics': 'Electronics', 'home & garden': 'Home & Garden', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden','sport': 'Sports','sports': 'Sports', 'clothing': 'Clothing', 'apparel': 'Clothing', 'books': 'Books', 'book': 'Books'}

# Read input
input_file = os.path.join(os.environ['INPUT_DIR'], 'raw.csv')
df = pd.read_csv(input_file, dtype=str)

# R1: Strip whitespace and treat certain values as missing
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
df.replace(MISSING_VALUES, np.nan, inplace=True)

# R2: Remove duplicate records
df.drop_duplicates(subset='order_id', keep='first', inplace=True)

# R3: Parse order_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
df['order_date'] = pd.to_datetime(df['order_date'], format=date_formats, errors='coerce')
df.dropna(subset=['order_date'], inplace=True)
df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')

# R4: Map region
df['region'] = df['region'].str.lower().map(REGION_MAP)
df.dropna(subset=['region'], inplace=True)
df['region'] = df['region'].astype('category')

# R5: Map product_category
df['product_category'] = df['product_category'].str.lower().map(PRODUCT_CATEGORY_MAP)
df.dropna(subset=['product_category'], inplace=True)
df['product_category'] = df['product_category'].astype('category')

# R6: Clean and parse unit_price
df['unit_price'] = df['unit_price'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).str.strip()
df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
df = df[(df['unit_price'].notna()) & (0 < df['unit_price']) & (df['unit_price'] <= 5000)]

# R7: Clean and parse quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df = df[(df['quantity'].notna()) & (df['quantity'].isin(range(1, 51)))]
df['quantity'] = df['quantity'].astype(int)

# R8: Clean and parse discount_pct
df['discount_pct'] = df['discount_pct'].replace('%', '', regex=True).str.strip()
df['discount_pct'] = pd.to_numeric(df['discount_pct'], errors='coerce').fillna(0)
df = df[(0 <= df['discount_pct']) & (df['discount_pct'] <= 100)]

# R9: Clean customer_id
df['customer_id'] = df['customer_id'].str.upper().fillna('UNKNOWN')

# R10: Calculate revenue
df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

# R11: Select and order columns
df = df[['order_id', 'order_date', 'customer_id','region', 'product_category', 'quantity', 'unit_price', 'discount_pct','revenue']]
df.sort_values(by='order_id', inplace=True)

# Write output
output_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaned.csv')
df.to_csv(output_file, index=False)

# Write cleaning summary
summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'dropped_duplicates': len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset='order_id')),
    'dropped_invalid_dates': len(pd.read_csv(input_file)) - len(df),
    'dropped_invalid_regions': len(pd.read_csv(input_file)) - len(df),
    'dropped_invalid_categories': len(pd.read_csv(input_file)) - len(df),
    'dropped_invalid_prices': len(pd.read_csv(input_file)) - len(df),
    'dropped_invalid_quantities': len(pd.read_csv(input_file)) - len(df),
    'dropped_invalid_discounts': len(pd.read_csv(input_file)) - len(df)
}
summary_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaning_summary.json')
with open(summary_file, 'w') as f:
    json.dump(summary, f)

output_filename = 'cleaned.csv'
cleaning_logic = 'The script reads the raw CSV, strips whitespace, removes duplicates, parses dates, maps regions and product categories, cleans and validates unit prices, quantities, and discounts, calculates revenue, and writes the cleaned data to a new CSV. It also generates a summary of the cleaning process.'
