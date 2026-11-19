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
df['product_category'] = df['product_category'].map(lambda x: x if x in ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books'] else np.nan)
df.dropna(subset=['product_category'], inplace=True)
df['product_category'] = pd.Categorical(df['product_category'], categories=['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books'])

# R6: Clean and parse unit_price
df['unit_price'] = df['unit_price'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).astype(float)
df = df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]

# R7: Clean and parse quantity
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').astype(int)
df = df[(df['quantity'] >= 1) & (df['quantity'] <= 50)]

# R8: Clean and parse discount_pct
df['discount_pct'] = df['discount_pct'].replace('%', '', regex=True).astype(float)
df['discount_pct'] = df['discount_pct'].fillna(0)
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
summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'dropped_duplicates': len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['order_id'], keep='first')),
    'dropped_invalid_dates': len(pd.read_csv(input_file)) - len(df.dropna(subset=['order_date'])) - (len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['order_id'], keep='first'))),
    'dropped_invalid_regions': len(df.dropna(subset=['region'])) - len(df),
    'dropped_invalid_categories': len(df.dropna(subset=['product_category'])) - len(df),
    'dropped_invalid_prices': len(df[(df['unit_price'] > 0) & (df['unit_price'] <= 5000)]) - len(df),
    'dropped_invalid_quantities': len(df[(df['quantity'] >= 1) & (df['quantity'] <= 50)]) - len(df),
    'dropped_invalid_discounts': len(df[(df['discount_pct'] >= 0) & (df['discount_pct'] <= 100)]) - len(df)
}
summary_file = os.path.join(os.environ["OUTPUT_DIR"], "cleaning_summary.json")
with open(summary_file, 'w') as f:
    f.write(json.dumps(summary, indent=2))