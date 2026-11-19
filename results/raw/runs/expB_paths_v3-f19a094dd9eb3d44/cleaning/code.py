import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]
REGION_MAP = {'north': 'North','south': 'South', 'east': 'East', 'west': 'West', 'n': 'North','s': 'South', 'e': 'East', 'w': 'West'}
PRODUCT_CATEGORY_MAP = {'electronics': 'Electronics', 'clothing': 'Clothing', 'home & garden': 'Home & Garden','sports': 'Sports', 'books': 'Books', 'electronic': 'Electronics', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden','sport': 'Sports', 'apparel': 'Clothing', 'book': 'Books'}

# Read input
input_file = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
df = pd.read_csv(input_file, dtype=str)

# R1: Strip whitespace and treat specified values as missing
df = df.applymap(lambda x: x.strip() if pd.notna(x) else x)
df = df.replace(MISSING_VALUES, np.nan)

# R2: Remove duplicate records
df = df.drop_duplicates(subset=['order_id'], keep='first')

# R3: Parse order_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
df['order_date'] = df['order_date'].apply(lambda x: pd.to_datetime(x, format=date_formats, errors='coerce')).dropna()
df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')

# R4: Map region
df['region'] = df['region'].str.lower().map(REGION_MAP).dropna()

# R5: Map product_category
df['product_category'] = df['product_category'].str.lower().map(PRODUCT_CATEGORY_MAP).dropna()

# R6: Clean and parse unit_price
df['unit_price'] = df['unit_price'].replace({'\$': '', 'USD': '', ',': '', '\%': ''}, regex=True).str.strip()
df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
df = df[(df['unit_price'].notna()) & (df['unit_price'] > 0) & (df['unit_price'] <= 5000)]

# R7: Parse quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df = df[(df['quantity'].notna()) & (df['quantity'].ge(1)) & (df['quantity'].le(50))]
df['quantity'] = df['quantity'].astype(int)

# R8: Clean and parse discount_pct
df['discount_pct'] = df['discount_pct'].replace({'\%': ''}, regex=True).str.strip()
df['discount_pct'] = pd.to_numeric(df['discount_pct'], errors='coerce').fillna(0)
df = df[(df['discount_pct'].ge(0)) & (df['discount_pct'].le(100))]

# R9: Clean customer_id
df['customer_id'] = df['customer_id'].str.upper().fillna('UNKNOWN')

# R10: Calculate revenue
df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

# Select and order columns
df = df[['order_id', 'order_date', 'customer_id','region', 'product_category', 'quantity', 'unit_price', 'discount_pct','revenue']].sort_values(by='order_id')

# Write output
output_file = os.path.join(os.environ["OUTPUT_DIR"], "cleaned.csv")
df.to_csv(output_file, index=False)

# Write cleaning summary
summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'duplicates_removed': len(df) - len(df.drop_duplicates(subset=['order_id'], keep='first')),
    'invalid_dates_dropped': len(pd.read_csv(input_file)) - len(df[df['order_date'].notna()]),
    'invalid_regions_dropped': len(pd.read_csv(input_file)) - len(df[df['region'].notna()]),
    'invalid_categories_dropped': len(pd.read_csv(input_file)) - len(df[df['product_category'].notna()]),
    'invalid_prices_dropped': len(pd.read_csv(input_file)) - len(df[(df['unit_price'].notna()) & (df['unit_price'] > 0) & (df['unit_price'] <= 5000)]),
    'invalid_quantities_dropped': len(pd.read_csv(input_file)) - len(df[(df['quantity'].notna()) & (df['quantity'].ge(1)) & (df['quantity'].le(50))]),
    'invalid_discounts_dropped': len(pd.read_csv(input_file)) - len(df[(df['discount_pct'].ge(0)) & (df['discount_pct'].le(100))])
}
summary_file = os.path.join(os.environ["OUTPUT_DIR"], "cleaning_summary.json")
with open(summary_file, 'w') as f:
    f.write(json.dumps(summary, indent=2))

output_filename = "cleaned.csv"
cleaning_logic = "The script reads the raw CSV, strips whitespace, treats specified values as missing, removes duplicates, parses dates, maps regions and product categories, cleans and parses unit prices and quantities, calculates revenue, and writes the cleaned data to a new CSV. It also generates a cleaning summary JSON."