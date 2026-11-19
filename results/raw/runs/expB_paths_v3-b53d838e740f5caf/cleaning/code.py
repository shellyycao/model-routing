import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]
REGION_MAP = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West'}
PRODUCT_CATEGORY_MAP = {'Electronic': 'Electronics', 'Home and Garden': 'Home & Garden', 'Home&Garden': 'Home & Garden', 'Sport': 'Sports', 'Apparel': 'Clothing', 'Book': 'Books'}

# Read input
input_filepath = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
df = pd.read_csv(input_filepath, dtype=str)

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
df['region'] = df['region'].str.upper().map(lambda x: REGION_MAP.get(x, x) if len(x) == 1 else x)
df = df[df['region'].isin(['NORTH', 'SOUTH', 'EAST', 'WEST']) & ~df['region'].isna()]
df['region'] = df['region'].str.title()

# R5: Map product_category
df['product_category'] = df['product_category'].str.title().map(lambda x: PRODUCT_CATEGORY_MAP.get(x, x))
df = df[df['product_category'].isin(['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books']) & ~df['product_category'].isna()]

# R6: Clean and parse unit_price
df['unit_price'] = df['unit_price'].replace({'\$|USD|,': ''}, regex=True).str.strip()
df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
df = df[(df['unit_price'].notna()) & (df['unit_price'] > 0) & (df['unit_price'] <= 5000)]

# R7: Clean and parse quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df = df[(df['quantity'].notna()) & (df['quantity'].astype(int) == df['quantity']) & (df['quantity'] >= 1) & (df['quantity'] <= 50)]
df['quantity'] = df['quantity'].astype(int)

# R8: Clean and parse discount_pct
df['discount_pct'] = df['discount_pct'].replace('%', '', regex=True).str.strip()
df['discount_pct'] = pd.to_numeric(df['discount_pct'], errors='coerce').fillna(0)
df = df[(df['discount_pct'].notna()) & (df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]

# R9: Clean customer_id
df['customer_id'] = df['customer_id'].str.upper().fillna('UNKNOWN')

# R10: Calculate revenue
df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

# R11: Select and order columns
df = df[['order_id', 'order_date', 'customer_id','region', 'product_category', 'quantity', 'unit_price', 'discount_pct','revenue']].sort_values(by='order_id')

# Write output
output_filepath = os.path.join(os.environ["OUTPUT_DIR"], "cleaned.csv")
df.to_csv(output_filepath, index=False)

# Write cleaning summary
cleaning_summary = {
    'raw_rows': len(pd.read_csv(input_filepath)),
    'cleaned_rows': len(df),
    'duplicates_removed': len(df) - len(df.drop_duplicates(subset=['order_id'], keep='first')),
    'invalid_dates_dropped': len(pd.read_csv(input_filepath)) - len(df.dropna(subset=['order_date']))
}
summary_filepath = os.path.join(os.environ["OUTPUT_DIR"], "cleaning_summary.json")
with open(summary_filepath, 'w') as f:
    f.write(json.dumps(cleaning_summary, indent=2))

output_filename = "cleaned.csv"
