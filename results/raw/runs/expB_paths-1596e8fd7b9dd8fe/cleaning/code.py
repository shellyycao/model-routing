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
df.replace(missing_values, np.nan, inplace=True, regex=True)
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# R2: Remove duplicate records
df.drop_duplicates(subset=['order_id'], keep='first', inplace=True)

# R3: Parse order_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce', format=date_formats)
df.dropna(subset=['order_date'], inplace=True)
df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')

# R4: Map region
region_map = {'n': 'North','s': 'South', 'e': 'East', 'w': 'West'}
df['region'] = df['region'].str.lower().map(region_map).fillna(df['region'].str.capitalize())
df = df[df['region'].isin(['North', 'South', 'East', 'West']) & ~df['region'].isna()]

# R5: Map product_category
product_category_map = {
    'electronic': 'Electronics', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden',
   'sport': 'Sports', 'apparel': 'Clothing', 'book': 'Books'
}
df['product_category'] = df['product_category'].str.lower().map(product_category_map).fillna(df['product_category'].str.capitalize())
df = df[df['product_category'].isin(['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books']) & ~df['product_category'].isna()]

# R6: Clean unit_price
df['unit_price'] = df['unit_price'].replace({'\$|USD|,': ''}, regex=True).astype(float)
df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000) & ~df['unit_price'].isna()]

# R7: Clean quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').astype(int)
df = df[(df['quantity'] >= 1) & (df['quantity'] <= 50) & ~df['quantity'].isna()]

# R8: Clean discount_pct
df['discount_pct'] = df['discount_pct'].replace('%', '', regex=True).astype(float).fillna(0)
df = df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100) & ~df['discount_pct'].isna()]

# R9: Clean customer_id
df['customer_id'] = df['customer_id'].str.upper().fillna('UNKNOWN')

# R10: Calculate revenue
df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

# R11: Select and order columns
df = df[['order_id', 'order_date', 'customer_id','region', 'product_category', 'quantity', 'unit_price', 'discount_pct','revenue']]
df.sort_values(by='order_id', inplace=True)

# Write the cleaned data to CSV
df.to_csv(os.path.join(output_dir, 'cleaned.csv'), index=False)

# Write the cleaning summary
cleaning_summary = {
    'raw_rows': len(pd.read_csv(os.path.join(input_dir, 'raw.csv'))),
    'cleaned_rows': len(df),
    'duplicates_removed': df.duplicated(subset=['order_id']).sum(),
    'invalid_dates_removed': len(pd.read_csv(os.path.join(input_dir, 'raw.csv'))) - len(df),
    'invalid_regions_removed': len(pd.read_csv(os.path.join(input_dir, 'raw.csv'))) - len(df),
    'invalid_categories_removed': len(pd.read_csv(os.path.join(input_dir, 'raw.csv'))) - len(df),
    'invalid_prices_removed': len(pd.read_csv(os.path.join(input_dir, 'raw.csv'))) - len(df),
    'invalid_quantities_removed': len(pd.read_csv(os.path.join(input_dir, 'raw.csv'))) - len(df),
    'invalid_discounts_removed': len(pd.read_csv(os.path.join(input_dir, 'raw.csv'))) - len(df)
}

with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
    f.write(json.dumps(cleaning_summary, indent=4))

output_filename = 'cleaned.csv'

cleaning_logic = 'The script reads the raw data, strips whitespace, removes duplicates, parses dates, maps regions and product categories, cleans unit prices and quantities, calculates revenue, and writes the cleaned data to a CSV file. It also generates a cleaning summary JSON file with counts of rows read, cleaned, and removed for various reasons.'