import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]
REGION_MAP = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West'}
PRODUCT_CATEGORY_MAP = {'Electronic': 'Electronics', 'Home and Garden': 'Home & Garden', 'Home&Garden': 'Home & Garden', 'Sport': 'Sports', 'Apparel': 'Clothing', 'Book': 'Books'}

# Read input
input_file = os.path.join(os.environ['INPUT_DIR'], 'raw.csv')
df = pd.read_csv(input_file, dtype=str)

# R1: Strip whitespace and treat specified values as missing
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
df.replace(MISSING_VALUES, np.nan, inplace=True)

# R2: Remove duplicate records
df.drop_duplicates(subset=['order_id'], keep='first', inplace=True)

# R3: Parse order_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce', format=date_formats)
df.dropna(subset=['order_date'], inplace=True)
df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')

# R4: Map region
df['region'] = df['region'].str.upper().map(lambda x: REGION_MAP.get(x, x) if len(x) == 1 else x)
df['region'] = df['region'].map(lambda x: x if x in ['NORTH', 'SOUTH', 'EAST', 'WEST'] else np.nan)
df.dropna(subset=['region'], inplace=True)
df['region'] = df['region'].astype('category')

# R5: Map product_category
df['product_category'] = df['product_category'].str.upper()
df['product_category'] = df['product_category'].map(lambda x: PRODUCT_CATEGORY_MAP.get(x, x))
df['product_category'] = df['product_category'].map(lambda x: x if x in ['ELECTRONICS', 'CLOTHING', 'HOME & GARDEN', 'SPORTS', 'BOOKS'] else np.nan)
df.dropna(subset=['product_category'], inplace=True)
df['product_category'] = df['product_category'].astype('category')

# R6: Clean unit_price
df['unit_price'] = df['unit_price'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).str.strip()
df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]

# R7: Clean quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df = df[(df['quantity'].ge(1)) & (df['quantity'].le(50)) & (df['quantity'].eq(df['quantity'].astype(int)))]
df['quantity'] = df['quantity'].astype(int)

# R8: Clean discount_pct
df['discount_pct'] = df['discount_pct'].replace('%', '', regex=True).str.strip()
df['discount_pct'] = pd.to_numeric(df['discount_pct'], errors='coerce').fillna(0)
df = df[(df['discount_pct'].ge(0)) & (df['discount_pct'].le(100))]

# R9: Clean customer_id
df['customer_id'] = df['customer_id'].str.upper().fillna('UNKNOWN')

# R10: Calculate revenue
df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

# R11: Select and order columns
df = df[['order_id', 'order_date', 'customer_id','region', 'product_category', 'quantity', 'unit_price', 'discount_pct','revenue']].sort_values(by='order_id')

# Write output
output_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaned.csv')
df.to_csv(output_file, index=False)

# Write cleaning summary
summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'dropped_duplicates': len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['order_id'], keep='first')),
    'dropped_invalid_dates': len(pd.read_csv(input_file)) - len(df.dropna(subset=['order_date']))
}
with open(os.path.join(os.environ['OUTPUT_DIR'], 'cleaning_summary.json'), 'w') as f:
    f.write(json.dumps(summary, indent=2))

output_filename = 'cleaned.csv'

cleaning_logic = 'The script performs the following cleaning steps: 1) Reads the raw CSV and strips whitespace from all values, treating specified values as missing. 2) Removes duplicate records based on order_id. 3) Parses order_date using specified formats and drops rows with invalid dates. 4) Maps region to standardized values and drops invalid regions. 5) Maps product_category to standardized values and drops invalid categories. 6) Cleans unit_price by removing currency symbols and commas, parsing as a number, and dropping invalid values. 7) Cleans quantity by parsing as a number and dropping invalid values. 8) Cleans discount_pct by removing the percentage sign, parsing as a number, and setting missing values to 0. 9) Converts customer_id to uppercase and sets missing values to UNKNOWN. 10) Calculates revenue as quantity * unit_price * (1 - discount_pct / 100). 11) Selects and orders the required columns, then writes the cleaned data to a CSV file.'