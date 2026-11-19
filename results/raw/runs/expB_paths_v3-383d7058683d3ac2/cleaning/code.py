import os
import pandas as pd
import numpy as np
from datetime import datetime

# Define the input and output directories
input_dir = os.environ['INPUT_DIR']
output_dir = os.environ['OUTPUT_DIR']

# Read the raw data
df = pd.read_csv(os.path.join(input_dir, 'raw.csv'), dtype=str)

# R1: Strip whitespace and treat specified values as missing
missing_values = ['NA', 'N/A', 'null', 'None', '-']
df.replace(missing_values, np.nan, inplace=True)
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# R2: Remove duplicate records
df.drop_duplicates(subset=['order_id'], keep='first', inplace=True)

# R3: Parse order_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
df['order_date'] = pd.to_datetime(df['order_date'], format=date_formats, errors='coerce')
df.dropna(subset=['order_date'], inplace=True)
df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')

# R4: Map region
region_map = {'n': 'North','s': 'South', 'e': 'East', 'w': 'West'}
df['region'] = df['region'].str.lower().map(lambda x: region_map.get(x, x) if len(x) == 1 else x)
df['region'] = df['region'].str.title()
df = df[df['region'].isin(['North', 'South', 'East', 'West']) & ~df['region'].isna()]

# R5: Map product_category
category_map = {'Electronic': 'Electronics', 'Home and Garden': 'Home & Garden', 'Home&Garden': 'Home & Garden', 'Sport': 'Sports', 'Apparel': 'Clothing', 'Book': 'Books'}
df['product_category'] = df['product_category'].str.lower().map(lambda x: category_map.get(x, x))
df = df[df['product_category'].isin(['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books']) & ~df['product_category'].isna()]

# R6: Clean unit_price
df['unit_price'] = df['unit_price'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).astype(float)
df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000) & ~df['unit_price'].isna()]

# R7: Clean quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').astype(int)
df = df[(df['quantity'] >= 1) & (df['quantity'] <= 50) & ~df['quantity'].isna()]

# R8: Clean discount_pct
df['discount_pct'] = df['discount_pct'].replace('%', '', regex=True).astype(float)
df['discount_pct'] = df['discount_pct'].fillna(0)
df = df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]

# R9: Clean customer_id
df['customer_id'] = df['customer_id'].str.upper().fillna('UNKNOWN')

# R10: Calculate revenue
df['revenue'] = (df['quantity'] * df['unit_price'] * (1 - df['discount_pct'] / 100)).round(2)

# R11: Select and order columns
df = df[['order_id', 'order_date', 'customer_id','region', 'product_category', 'quantity', 'unit_price', 'discount_pct','revenue']]
df.sort_values(by='order_id', inplace=True)

# Write the cleaned data to CSV
output_filename = 'cleaned.csv'
df.to_csv(os.path.join(output_dir, output_filename), index=False)

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

# Cleaning logic explanation
cleaning_logic = 'The script performs the following cleaning steps: 1) Reads the raw data and strips whitespace from all values. 2) Treats specified values as missing. 3) Removes duplicate records based on order_id. 4) Parses order_date using specified formats and drops rows with invalid dates. 5) Maps region and product_category to standardized values and drops rows with invalid values. 6) Cleans unit_price by removing currency symbols and commas, parsing as a number, and dropping rows with invalid values. 7) Cleans quantity by parsing as an integer and dropping rows with invalid values. 8) Cleans discount_pct by removing the percentage sign, parsing as a number, and setting missing values to 0. 9) Converts customer_id to uppercase and sets missing values to UNKNOWN. 10) Calculates revenue as quantity * unit_price * (1 - discount_pct / 100). 11) Selects and orders the required columns and writes the cleaned data to a CSV file.'