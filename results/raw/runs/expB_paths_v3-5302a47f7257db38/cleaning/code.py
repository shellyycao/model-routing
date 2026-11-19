import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]
REGION_MAP = {'north': 'North','south': 'South', 'east': 'East', 'west': 'West', 'n': 'North','s': 'South', 'e': 'East', 'w': 'West'}
PRODUCT_CATEGORY_MAP = {'electronics': 'Electronics', 'clothing': 'Clothing', 'home & garden': 'Home & Garden','sports': 'Sports', 'books': 'Books', 'electronic': 'Electronics', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden','sport': 'Sports', 'apparel': 'Clothing', 'book': 'Books'}

# Read input
input_file = os.path.join(os.environ['INPUT_DIR'], 'raw.csv')
df = pd.read_csv(input_file, dtype=str)

# R1: Strip whitespace and treat certain values as missing
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
df = df.replace(MISSING_VALUES, np.nan)

# R2: Remove duplicate records
df = df.drop_duplicates(subset=['order_id'], keep='first')

# R3: Parse order_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
df['order_date'] = pd.to_datetime(df['order_date'], format=date_formats, errors='coerce')
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
df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]

# R7: Clean and parse quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df = df[(df['quantity'].isin(range(1, 51))) & (df['quantity'].notna())]
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
    'duplicates_removed': df.duplicated(subset=['order_id']).sum(),
    'invalid_dates': len(pd.read_csv(input_file)) - len(df[pd.to_datetime(df['order_date'], errors='coerce').notna()]),
    'invalid_regions': len(pd.read_csv(input_file)) - len(df[df['region'].isin(REGION_MAP.values())]),
    'invalid_categories': len(pd.read_csv(input_file)) - len(df[df['product_category'].isin(PRODUCT_CATEGORY_MAP.values())]),
    'invalid_prices': len(pd.read_csv(input_file)) - len(df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]),
    'invalid_quantities': len(pd.read_csv(input_file)) - len(df[(df['quantity'].isin(range(1, 51))) & (df['quantity'].notna())]),
    'invalid_discounts': len(pd.read_csv(input_file)) - len(df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)])
}
summary_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaning_summary.json')
with open(summary_file, 'w') as f:
    f.write(json.dumps(summary, indent=2))