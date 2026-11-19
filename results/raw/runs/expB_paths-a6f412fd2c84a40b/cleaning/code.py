import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_DIR = os.getenv('INPUT_DIR')
OUTPUT_DIR = os.getenv('OUTPUT_DIR')
RAW_FILE = os.path.join(INPUT_DIR, 'raw.csv')
CLEANED_FILE = os.path.join(OUTPUT_DIR, 'cleaned.csv')
SUMMARY_FILE = os.path.join(OUTPUT_DIR, 'cleaning_summary.json')
output_filename = 'cleaned.csv'

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
MISSING_VALUES = {'', 'na', 'n/a', 'null', 'none', '-'}

def is_missing(val):
    if pd.isna(val):
        return True
    return str(val).strip().lower() in MISSING_VALUES

def clean_str(val):
    if pd.isna(val):
        return np.nan
    return str(val).strip()

def parse_date(date_str):
    if pd.isna(date_str):
        return None
    date_str = date_str.strip()
    formats = [
        '%Y-%m-%d',          # 2023-01-04
        '%m/%d/%Y',          # 01/05/2023
        '%d-%b-%Y',          # 05-Mar-2024
        '%Y/%m/%d',          # 2023/01/13
        '%B %d, %Y',         # March 5, 2024
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

REGION_MAP = {
    'n': 'North', 'north': 'North',
    's': 'South', 'south': 'South',
    'e': 'East',  'east': 'East',
    'w': 'West',  'west': 'West',
}

def map_region(val):
    if pd.isna(val):
        return None
    key = val.strip().lower()
    return REGION_MAP.get(key)

PRODUCT_MAP = {
    'electronics': 'Electronics',
    'electronic': 'Electronics',
    'clothing': 'Clothing',
    'apparel': 'Clothing',
    'home & garden': 'Home & Garden',
    'home and garden': 'Home & Garden',
    'home&garden': 'Home & Garden',
    'sports': 'Sports',
    'sport': 'Sports',
    'books': 'Books',
    'book': 'Books',
}

def map_product(val):
    if pd.isna(val):
        return None
    key = val.strip().lower()
    return PRODUCT_MAP.get(key)

def clean_unit_price(val):
    if pd.isna(val):
        return None
    s = str(val).replace('$', '').replace('USD', '').replace(',', '').strip()
    try:
        price = float(s)
        return price
    except ValueError:
        return None

def clean_quantity(val):
    if pd.isna(val):
        return None
    try:
        q = float(str(val).strip())
        if not q.is_integer():
            return None
        q_int = int(q)
        return q_int
    except ValueError:
        return None

def clean_discount(val):
    if pd.isna(val) or str(val).strip() == '':
        return 0.0
    s = str(val).strip()
    if s.endswith('%'):
        s = s[:-1]
    try:
        d = float(s)
        return d
    except ValueError:
        return None

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------
summary = {
    'raw_rows': 0,
    'cleaned_rows': 0,
    'duplicate_rows_removed': 0,
    'rows_dropped_due_to_date': 0,
    'rows_dropped_due_to_region': 0,
    'rows_dropped_due_to_product_category': 0,
    'rows_dropped_due_to_unit_price': 0,
    'rows_dropped_due_to_quantity': 0,
    'rows_dropped_due_to_discount_pct': 0,
}

# 1. Load raw CSV, read everything as text
raw_df = pd.read_csv(RAW_FILE, dtype=str, keep_default_na=False)
summary['raw_rows'] = len(raw_df)

# 2. Strip whitespace from every cell
raw_df = raw_df.applymap(clean_str)

# 3. Convert defined missing tokens to NaN
raw_df = raw_df.replace({v: np.nan for v in MISSING_VALUES})

# 4. Remove duplicate order_id rows (keep first)
before_dup = len(raw_df)
raw_df = raw_df.drop_duplicates(subset='order_id', keep='first')
summary['duplicate_rows_removed'] = before_dup - len(raw_df)

cleaned_rows = []

for idx, row in raw_df.iterrows():
    # ----- R3: order_date -----
    order_date = parse_date(row.get('order_date'))
    if not order_date:
        summary['rows_dropped_due_to_date'] += 1
        continue

    # ----- R4: region -----
    region = map_region(row.get('region'))
    if not region:
        summary['rows_dropped_due_to_region'] += 1
        continue

    # ----- R5: product_category -----
    product = map_product(row.get('product_category'))
    if not product:
        summary['rows_dropped_due_to_product_category'] += 1
        continue

    # ----- R6: unit_price -----
    unit_price = clean_unit_price(row.get('unit_price'))
    if unit_price is None or unit_price <= 0 or unit_price > 5000:
        summary['rows_dropped_due_to_unit_price'] += 1
        continue

    # ----- R7: quantity -----
    quantity = clean_quantity(row.get('quantity'))
    if quantity is None or quantity < 1 or quantity > 50:
        summary['rows_dropped_due_to_quantity'] += 1
        continue

    # ----- R8: discount_pct -----
    discount = clean_discount(row.get('discount_pct'))
    if discount is None or discount < 0 or discount > 100:
        summary['rows_dropped_due_to_discount_pct'] += 1
        continue

    # ----- R9: customer_id -----
    cust = row.get('customer_id')
    if pd.isna(cust) or cust == '' or cust is None:
        cust = 'UNKNOWN'
    else:
        cust = str(cust).upper()

    # ----- R10: revenue -----
    revenue = round(quantity * unit_price * (1 - discount / 100), 2)

    cleaned_rows.append({
        'order_id': row.get('order_id'),
        'order_date': order_date,
        'customer_id': cust,
        'region': region,
        'product_category': product,
        'quantity': quantity,
        'unit_price': unit_price,
        'discount_pct': discount,
        'revenue': revenue,
    })

# Build cleaned DataFrame
cleaned_df = pd.DataFrame(cleaned_rows)
summary['cleaned_rows'] = len(cleaned_df)

# ----- R11: final ordering and output -----
if not cleaned_df.empty:
    cleaned_df = cleaned_df.sort_values('order_id')
    cleaned_df.to_csv(CLEANED_FILE, index=False, float_format='%.2f')
else:
    # Write an empty file with header only
    cleaned_df.to_csv(CLEANED_FILE, index=False)

# Write summary JSON
with open(SUMMARY_FILE, 'w') as f:
    json.dump(summary, f, indent=2)
