import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]
REGION_MAP = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West'}
PRODUCT_CATEGORY_MAP = {'Electronic': 'Electronics', 'Home and Garden': 'Home & Garden', 'Home&Garden': 'Home & Garden', 'Sport': 'Sports', 'Apparel': 'Clothing', 'Book': 'Books'}

# Read input
input_file = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
df = pd.read_csv(input_file, dtype=str)

# R1: Strip whitespace and treat specified values as missing
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
df.replace(MISSING_VALUES, np.nan, inplace=True)

# R2: Remove duplicate records
df.drop_duplicates(subset=['order_id'], keep='first', inplace=True)

# R3: Parse order_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
def parse_date(date_str):
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return np.nan
df['order_date'] = df['order_date'].apply(parse_date)
df.dropna(subset=['order_date'], inplace=True)

# R4: Map region
df['region'] = df['region'].str.upper().map(lambda x: REGION_MAP.get(x, x) if len(x) == 1 else x)
df['region'] = df['region'].map(lambda x: x.title() if x not in REGION_MAP.values() else x)
df.dropna(subset=['region'], inplace=True)
df['region'] = pd.Categorical(df['region'], categories=['North', 'South', 'East', 'West'])

# R5: Map product_category
df['product_category'] = df['product_category'].str.title().map(lambda x: PRODUCT_CATEGORY_MAP.get(x, x))
df['product_category'] = df['product_category'].map(lambda x: x.title() if x not in PRODUCT_CATEGORY_MAP.values() else x)
df.dropna(subset=['product_category'], inplace=True)
df['product_category'] = pd.Categorical(df['product_category'], categories=['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books'])

# R6: Clean unit_price
df['unit_price'] = df['unit_price'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).str.strip()
df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
df.dropna(subset=['unit_price'], inplace=True)
df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]

# R7: Clean quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df.dropna(subset=['quantity'], inplace=True)
df = df[(df['quantity'].astype(int) >= 1) & (df['quantity'].astype(int) <= 50)]
df['quantity'] = df['quantity'].astype(int)

# R8: Clean discount_pct
df['discount_pct'] = df['discount_pct'].replace('%', '', regex=True).str.strip()
df['discount_pct'] = pd.to_numeric(df['discount_pct'], errors='coerce').fillna(0)
df.dropna(subset=['discount_pct'], inplace=True)
df = df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]

# R9: Clean customer_id
df['customer_id'] = df['customer_id'].str.upper().fillna('UNKNOWN')

# R10: Calculate revenue
df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

# R11: Select and order columns
df = df[['order_id', 'order_date', 'customer_id','region', 'product_category', 'quantity', 'unit_price', 'discount_pct','revenue']].sort_values(by='order_id')

# Write output
output_file = os.path.join(os.environ["OUTPUT_DIR"], "cleaned.csv")
df.to_csv(output_file, index=False)

# Write cleaning summary
cleaning_summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'dropped_duplicates': len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['order_id'], keep='first')),
    'dropped_invalid_dates': len(pd.read_csv(input_file)) - len(df.dropna(subset=['order_date'])) - (len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['order_id'], keep='first'))),
    'dropped_invalid_regions': len(df.dropna(subset=['region'])) - len(df),
    'dropped_invalid_categories': len(df.dropna(subset=['product_category'])) - len(df),
    'dropped_invalid_prices': len(df.dropna(subset=['unit_price'])) - len(df),
    'dropped_invalid_quantities': len(df.dropna(subset=['quantity'])) - len(df),
    'dropped_invalid_discounts': len(df.dropna(subset=['discount_pct'])) - len(df),
}

with open(os.path.join(os.environ["OUTPUT_DIR"], 'cleaning_summary.json'), 'w') as f:
    import json
    json.dump(cleaning_summary, f)

output_filename = "cleaned.csv"
cleaning_logic = "The script reads the raw CSV, strips whitespace, treats specified values as missing, removes duplicates, parses dates, maps regions and product categories, cleans unit prices, quantities, and discounts, calculates revenue, and writes the cleaned data to a new CSV. It also generates a cleaning summary JSON."