import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]
REGION_MAP = {'n': 'North','s': 'South', 'e': 'East', 'w': 'West'}
PRODUCT_CATEGORY_MAP = {'Electronic': 'Electronics', 'Home and Garden': 'Home & Garden', 'Home&Garden': 'Home & Garden', 'Sport': 'Sports', 'Apparel': 'Clothing', 'Book': 'Books'}
DATE_FORMATS = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']

# Read input
input_file = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
df = pd.read_csv(input_file, dtype=str)

# R1: Strip whitespace and treat specified values as missing
df = df.applymap(lambda x: x.strip() if pd.notna(x) else x)
df.replace(to_replace=MISSING_VALUES, value=np.nan, inplace=True)

# R2: Remove duplicate records
df.drop_duplicates(subset=['order_id'], keep='first', inplace=True)

# R3: Parse order_date
def parse_date(date_str):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return np.nan
df['order_date'] = df['order_date'].apply(parse_date)
df.dropna(subset=['order_date'], inplace=True)

# R4: Map region
df['region'] = df['region'].str.lower().map(lambda x: REGION_MAP.get(x[0], np.nan) if x else np.nan)
df.dropna(subset=['region'], inplace=True)
df['region'] = df['region'].astype('category')

# R5: Map product_category
df['product_category'] = df['product_category'].str.lower().map(lambda x: PRODUCT_CATEGORY_MAP.get(x, x) if x else np.nan)
df['product_category'] = df['product_category'].map(lambda x: x.title())
valid_categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books']
df = df[df['product_category'].isin(valid_categories)]
df['product_category'] = df['product_category'].astype('category')

# R6: Clean and parse unit_price
df['unit_price'] = df['unit_price'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).str.strip()
df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]

# R7: Clean and parse quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df = df[(df['quantity'].ge(1)) & (df['quantity'].le(50)) & (df['quantity'].mod(1) == 0)]
df['quantity'] = df['quantity'].astype(int)

# R8: Clean and parse discount_pct
df['discount_pct'] = df['discount_pct'].replace({'%': ''}, regex=True).str.strip()
df['discount_pct'] = df['discount_pct'].fillna(0).astype(float)
df = df[(df['discount_pct'].ge(0)) & (df['discount_pct'].le(100))]

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
summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'duplicates_removed': len(pd.read_csv(input_file)) - df['order_id'].nunique(),
    'date_parse_errors': len(pd.read_csv(input_file)) - len(df[df['order_date'].notna()]),
   'region_errors': len(pd.read_csv(input_file)) - len(df[df['region'].notna()]),
    'category_errors': len(pd.read_csv(input_file)) - len(df[df['product_category'].notna()]),
    'price_errors': len(pd.read_csv(input_file)) - len(df[(df['unit_price'].notna()) & (df['unit_price'] > 0) & (df['unit_price'] <= 5000)]),
    'quantity_errors': len(pd.read_csv(input_file)) - len(df[(df['quantity'].notna()) & (df['quantity'].ge(1)) & (df['quantity'].le(50)) & (df['quantity'].mod(1) == 0)]),
    'discount_errors': len(pd.read_csv(input_file)) - len(df[(df['discount_pct'].notna()) & (df['discount_pct'].ge(0)) & (df['discount_pct'].le(100))])
}
with open(os.path.join(os.environ["OUTPUT_DIR"], 'cleaning_summary.json'), 'w') as f:
    json.dump(summary, f)

output_filename = "cleaned.csv"
cleaning_logic = "The script reads the raw CSV, strips whitespace, removes duplicates, parses dates, maps regions and product categories, cleans and validates unit prices, quantities, and discount percentages, calculates revenue, and writes the cleaned data to a new CSV. It also generates a summary of the cleaning process."