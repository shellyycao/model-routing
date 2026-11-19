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
df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce', format=date_formats).dt.strftime('%Y-%m-%d')
df.dropna(subset=['order_date'], inplace=True)

# R4: Map region
region_map = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West'}
df['region'] = df['region'].str.upper().map(lambda x: region_map.get(x, x) if len(x) == 1 else x)
df['region'] = df['region'].replace({'NORTH': 'North', 'SOUTH': 'South', 'EAST': 'East', 'WEST': 'West'})
df.dropna(subset=['region'], inplace=True)
df['region'] = pd.Categorical(df['region'], categories=['North', 'South', 'East', 'West'])

# R5: Map product_category
product_category_map = {
    'ELECTRONIC': 'Electronics', 'ELECTRONICS': 'Electronics',
    'HOME AND GARDEN': 'Home & Garden', 'HOME&GARDEN': 'Home & Garden',
    'SPORT': 'Sports', 'SPORTS': 'Sports',
    'APPAREL': 'Clothing', 'CLOTHING': 'Clothing',
    'BOOK': 'Books', 'BOOKS': 'Books'
}
df['product_category'] = df['product_category'].str.upper().map(product_category_map)
df.dropna(subset=['product_category'], inplace=True)
df['product_category'] = pd.Categorical(df['product_category'], categories=['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books'])

# R6: Clean unit_price
df['unit_price'] = df['unit_price'].str.replace('[$,USD]', '', regex=True).str.replace(',', '').str.strip()
df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]

# R7: Clean quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df['quantity'] = df['quantity'].astype(int)
df = df[(df['quantity'] >= 1) & (df['quantity'] <= 50)]

# R8: Clean discount_pct
df['discount_pct'] = df['discount_pct'].str.replace('%', '').str.strip()
df['discount_pct'] = pd.to_numeric(df['discount_pct'], errors='coerce').fillna(0)
df = df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]

# R9: Clean customer_id
df['customer_id'] = df['customer_id'].str.upper().fillna('UNKNOWN')

# R10: Add revenue column
df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

# R11: Select and order columns
df = df[['order_id', 'order_date', 'customer_id','region', 'product_category', 'quantity', 'unit_price', 'discount_pct','revenue']].sort_values(by='order_id')

# Write the cleaned data to CSV
df.to_csv(os.path.join(output_dir, 'cleaned.csv'), index=False)

# Write the cleaning summary
cleaning_summary = {
    'raw_rows': len(pd.read_csv(os.path.join(input_dir, 'raw.csv'))),
    'cleaned_rows': len(df)
}
with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
    f.write(json.dumps(cleaning_summary))