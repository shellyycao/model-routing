import os
import re
import json
import math
from datetime import datetime
import pandas as pd

MISSING_TOKENS = {'', 'na', 'n/a', 'null', 'none', '-'}
EXPECTED_COLUMNS = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 'quantity', 'unit_price', 'discount_pct']
OUTPUT_COLUMNS = ['order_id', 'order_date', 'customer_id', 'region', 'product_category', 'quantity', 'unit_price', 'discount_pct', 'revenue']
REGION_MAP = {'north': 'North', 'n': 'North', 'south': 'South', 's': 'South', 'east': 'East', 'e': 'East', 'west': 'West', 'w': 'West'}
CATEGORY_MAP = {'electronics': 'Electronics', 'electronic': 'Electronics', 'clothing': 'Clothing', 'apparel': 'Clothing', 'home & garden': 'Home & Garden', 'home and garden': 'Home & Garden', 'home&garden': 'Home & Garden', 'sports': 'Sports', 'sport': 'Sports', 'books': 'Books', 'book': 'Books'}
DATE_FORMATS = ('%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y')

def clean_cell(value):
    s = '' if value is None else str(value)
    s = s.strip()
    if s.lower() in MISSING_TOKENS:
        return pd.NA
    return s

def parse_date(value):
    if pd.isna(value):
        return None
    s = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None

def parse_price(value):
    if pd.isna(value):
        return None
    s = str(value).strip().replace('$', '').replace(',', '')
    s = re.sub('usd', '', s, flags=re.IGNORECASE).strip()
    if s == '':
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    if not math.isfinite(v) or v <= 0 or v > 5000:
        return None
    return v

def parse_quantity(value):
    if pd.isna(value):
        return None
    s = str(value).strip()
    try:
        v = float(s)
    except ValueError:
        return None
    if not math.isfinite(v) or not v.is_integer() or v < 1 or v > 50:
        return None
    return int(v)

def parse_discount(value):
    if pd.isna(value):
        return 0.0
    s = str(value).strip()
    if s.endswith('%'):
        s = s[:-1].strip()
    if s == '':
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    if not math.isfinite(v) or v < 0 or v > 100:
        return None
    return v

def map_region(value):
    if pd.isna(value):
        return pd.NA
    return REGION_MAP.get(str(value).strip().lower(), pd.NA)

def map_category(value):
    if pd.isna(value):
        return pd.NA
    return CATEGORY_MAP.get(str(value).strip().lower(), pd.NA)

def drop_invalid(df, summary, column, parsed, count_name):
    invalid = parsed.isna()
    summary[count_name] = int(invalid.sum())
    kept = df.loc[~invalid].copy()
    kept[column] = parsed.loc[~invalid]
    return kept

def main():
    input_dir = os.environ['INPUT_DIR']
    output_dir = os.environ['OUTPUT_DIR']
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(os.path.join(input_dir, 'raw.csv'), dtype=str, keep_default_na=False, na_filter=False, encoding='utf-8-sig')
    summary = {'raw_rows': int(len(df))}
    df = df[EXPECTED_COLUMNS].copy()
    for col in EXPECTED_COLUMNS:
        df[col] = df[col].map(clean_cell)
    id_missing = df['order_id'].isna()
    duplicate_mask = pd.Series(False, index=df.index)
    if bool((~id_missing).any()):
        duplicate_mask.loc[~id_missing] = df.loc[~id_missing, 'order_id'].duplicated(keep='first')
    summary['duplicates_removed_order_id'] = int(duplicate_mask.sum())
    df = df.loc[~duplicate_mask].copy()
    missing_id = df['order_id'].isna()
    summary['dropped_missing_order_id'] = int(missing_id.sum())
    df = df.loc[~missing_id].copy()
    df = drop_invalid(df, summary, 'order_date', df['order_date'].map(parse_date), 'dropped_order_date')
    df = drop_invalid(df, summary, 'region', df['region'].map(map_region), 'dropped_region')
    df = drop_invalid(df, summary, 'product_category', df['product_category'].map(map_category), 'dropped_product_category')
    df = drop_invalid(df, summary, 'unit_price', df['unit_price'].map(parse_price), 'dropped_unit_price')
    df = drop_invalid(df, summary, 'quantity', df['quantity'].map(parse_quantity), 'dropped_quantity')
    summary['discount_pct_missing_set_zero'] = int(df['discount_pct'].isna().sum())
    df = drop_invalid(df, summary, 'discount_pct', df['discount_pct'].map(parse_discount), 'dropped_discount_pct')
    summary['customer_id_missing_set_unknown'] = int(df['customer_id'].isna().sum())
    df['customer_id'] = df['customer_id'].map(lambda x: 'UNKNOWN' if pd.isna(x) else str(x).strip().upper())
    df['quantity'] = df['quantity'].astype(int)
    df['unit_price'] = df['unit_price'].astype(float)
    df['discount_pct'] = df['discount_pct'].astype(float)
    df['revenue'] = (df['quantity'] * df['unit_price'] * (1.0 - df['discount_pct'] / 100.0)).map(lambda x: round(float(x), 2))
    df = df[OUTPUT_COLUMNS].copy()
    df = df.sort_values('order_id', ascending=True, kind='mergesort').reset_index(drop=True)
    df['order_date'] = df['order_date'].map(lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x))
    summary['cleaned_rows'] = int(len(df))
    df.to_csv(os.path.join(output_dir, 'cleaned.csv'), index=False, header=True, encoding='utf-8', lineterminator='\n')
    with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, sort_keys=True)

if __name__ == '__main__':
    main()
