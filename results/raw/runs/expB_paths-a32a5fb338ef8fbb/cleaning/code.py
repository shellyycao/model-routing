import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]
REGION_MAP = {'north': 'North','south': 'South', 'east': 'East', 'west': 'West', 'n': 'North','s': 'South', 'e': 'East', 'w': 'West'}
PRODUCT_CATEGORY_MAP = {'electronic': 'Electronics', 'electronics': 'Electronics', 'home & garden': 'Home & Garden', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden','sport': 'Sports','sports': 'Sports', 'clothing': 'Clothing', 'apparel': 'Clothing', 'book': 'Books', 'books': 'Books'}

# Read input
input_file = os.path.join(os.environ['INPUT_DIR'], 'raw.csv')
df = pd.read_csv(input_file, dtype=str)

# R1: Strip whitespace and treat specified values as missing
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
df = df.replace(MISSING_VALUES, np.nan)

# R2: Remove duplicate records
df = df.drop_duplicates(subset=['order_id'], keep='first')

# R3: Parse order_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
df['order_date'] = df['order_date'].apply(lambda x: pd.to_datetime(x, format=date_formats, errors='coerce'))
df = df.dropna(subset=['order_date'])
df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')

# R4: Map region
df['region'] = df['region'].str.lower().map(REGION_MAP)
df = df.dropna(subset=['region'])

# R5: Map product_category
df['product_category'] = df['product_category'].str.lower().map(PRODUCT_CATEGORY_MAP)
df = df.dropna(subset=['product_category'])

# R6: Clean and parse unit_price
df['unit_price'] = df['unit_price'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).astype(float)
df = df.dropna(subset=['unit_price'])
df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]

# R7: Clean and parse quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df = df.dropna(subset=['quantity'])
df = df[(df['quantity'] >= 1) & (df['quantity'] <= 50)]
df['quantity'] = df['quantity'].astype(int)

# R8: Clean and parse discount_pct
df['discount_pct'] = df['discount_pct'].replace('%', '', regex=True).astype(float)
df['discount_pct'] = df['discount_pct'].fillna(0)
df = df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]

# R9: Clean customer_id
df['customer_id'] = df['customer_id'].str.upper().fillna('UNKNOWN')

# R10: Calculate revenue
df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

# R11: Select and order columns
df = df[['order_id', 'order_date', 'customer_id','region', 'product_category', 'quantity', 'unit_price', 'discount_pct','revenue']]
df = df.sort_values(by='order_id')

# Write output
output_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaned.csv')
df.to_csv(output_file, index=False)

# Write cleaning summary
summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'dropped_duplicates': len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['order_id'], keep='first')),
    'dropped_invalid_dates': len(df.dropna(subset=['order_date'])) - len(df),
    'dropped_invalid_regions': len(df.dropna(subset=['region'])) - len(df),
    'dropped_invalid_categories': len(df.dropna(subset=['product_category'])) - len(df),
    'dropped_invalid_prices': len(df.dropna(subset=['unit_price'])) - len(df),
    'dropped_invalid_quantities': len(df.dropna(subset=['quantity'])) - len(df),
    'dropped_invalid_discounts': len(df.dropna(subset=['discount_pct'])) - len(df)
}
summary_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaning_summary.json')
with open(summary_file, 'w') as f:
    f.write(json.dumps(summary, indent=2))

output_filename = 'cleaned.csv'
cleaning_logic = 'The script reads the raw CSV, strips whitespace, removes duplicates, parses dates and regions, maps product categories, cleans and parses unit prices and quantities, calculates revenue, and writes the cleaned data to a new CSV. It also generates a cleaning summary JSON with row counts for each cleaning step.'
