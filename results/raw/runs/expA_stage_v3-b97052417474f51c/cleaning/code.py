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

# R1: Strip whitespace and treat certain values as missing
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
df = df.replace(MISSING_VALUES, np.nan)

# R2: Remove duplicate records
df = df.drop_duplicates(subset=['order_id'], keep='first')

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
df = df.dropna(subset=['order_date'])

# R4: Map region
def map_region(region):
    region = region.upper()
    return REGION_MAP.get(region, region) if region in REGION_MAP else np.nan
df['region'] = df['region'].apply(map_region)
df = df.dropna(subset=['region'])

# R5: Map product_category
def map_product_category(category):
    category = category.lower()
    if category in PRODUCT_CATEGORY_MAP:
        return PRODUCT_CATEGORY_MAP[category]
    return category.title()
df['product_category'] = df['product_category'].apply(map_product_category)
valid_categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books']
df = df[df['product_category'].isin(valid_categories)]

# R6: Clean unit_price
def clean_unit_price(price):
    price = str(price).replace('$', '').replace('USD', '').replace(',', '').strip()
    try:
        price = float(price)
        if price <= 0 or price > 5000:
            return np.nan
        return price
    except ValueError:
        return np.nan
df['unit_price'] = df['unit_price'].apply(clean_unit_price)
df = df.dropna(subset=['unit_price'])

# R7: Clean quantity
def clean_quantity(qty):
    try:
        qty = int(float(qty))
        if qty < 1 or qty > 50:
            return np.nan
        return qty
    except ValueError:
        return np.nan
df['quantity'] = df['quantity'].apply(clean_quantity)
df = df.dropna(subset=['quantity'])

# R8: Clean discount_pct
def clean_discount_pct(discount):
    discount = str(discount).rstrip('%').strip()
    try:
        discount = float(discount)
        if discount < 0 or discount > 100:
            return np.nan
        return discount
    except ValueError:
        return np.nan
df['discount_pct'] = df['discount_pct'].apply(clean_discount_pct).fillna(0)

# R9: Clean customer_id
df['customer_id'] = df['customer_id'].str.upper().fillna('UNKNOWN')

# R10: Calculate revenue
df['revenue'] = (df['quantity'].astype(float) * df['unit_price'].astype(float) * (1 - df['discount_pct'].astype(float) / 100)).round(2)

# R11: Select and order columns
df = df[['order_id', 'order_date', 'customer_id','region', 'product_category', 'quantity', 'unit_price', 'discount_pct','revenue']].sort_values(by='order_id')

# Write output
output_file = os.path.join(os.environ["OUTPUT_DIR"], "cleaned.csv")
df.to_csv(output_file, index=False)

# Write cleaning summary
cleaning_summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'duplicates_removed': len(df) - len(df.drop_duplicates(subset=['order_id'], keep='first')),
    'invalid_dates': len(pd.read_csv(input_file)) - len(df.dropna(subset=['order_date'])) - (len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['order_id'], keep='first'))),
    'invalid_regions': len(df.dropna(subset=['order_date'])) - len(df.dropna(subset=['region'])) - (len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['order_id'], keep='first'))),
    'invalid_categories': len(df.dropna(subset=['region'])) - len(df[df['product_category'].isin(valid_categories)]) - (len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['order_id'], keep='first'))),
    'invalid_prices': len(df[df['product_category'].isin(valid_categories)]) - len(df.dropna(subset=['unit_price'])) - (len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['order_id'], keep='first'))),
    'invalid_quantities': len(df.dropna(subset=['unit_price'])) - len(df.dropna(subset=['quantity'])) - (len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['order_id'], keep='first'))),
    'invalid_discounts': len(df.dropna(subset=['quantity'])) - len(df.dropna(subset=['discount_pct'])) - (len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['order_id'], keep='first')))
}
summary_file = os.path.join(os.environ["OUTPUT_DIR"], "cleaning_summary.json")
with open(summary_file, 'w') as f:
    f.write(json.dumps(cleaning_summary, indent=4))