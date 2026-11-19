import os
import json
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
MISSING_VALUES = {'', 'na', 'n/a', 'null', 'none', '-'}

def normalize_missing(val):
    """Strip whitespace and convert defined missing strings to None."""
    if isinstance(val, str):
        val = val.strip()
        if val.lower() in MISSING_VALUES:
            return None
        return val
    return val

def parse_date(val):
    """Try the allowed date formats, return ISO string or None."""
    if val is None:
        return None
    formats = [
        "%Y-%m-%d",          # 2023-01-04
        "%m/%d/%Y",          # 01/05/2023
        "%d-%b-%Y",          # 05-Mar-2024 (abbr month)
        "%Y/%m/%d",          # 2023/01/13
        "%B %d, %Y"          # March 5, 2024 (full month name)
    ]
    # For the abbrev month format make the month title‑cased (e.g. "mar" -> "Mar")
    for fmt in formats:
        try:
            if fmt == "%d-%b-%Y":
                # Ensure month abbreviation has first letter capitalised
                parts = val.split('-')
                if len(parts) == 3:
                    parts[1] = parts[1].title()
                    val_adj = '-'.join(parts)
                else:
                    val_adj = val
                dt = datetime.strptime(val_adj, fmt)
            else:
                dt = datetime.strptime(val, fmt)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            continue
    return None

def map_region(val):
    if val is None:
        return None
    mapping = {
        'north': 'North', 'n': 'North',
        'south': 'South', 's': 'South',
        'east':  'East',  'e': 'East',
        'west':  'West',  'w': 'West'
    }
    return mapping.get(val.lower())

def map_category(val):
    if val is None:
        return None
    mapping = {
        'electronics': 'Electronics',
        'electronic':  'Electronics',
        'clothing':    'Clothing',
        'apparel':     'Clothing',
        'home & garden': 'Home & Garden',
        'home and garden': 'Home & Garden',
        'home&garden': 'Home & Garden',
        'sports':      'Sports',
        'sport':       'Sports',
        'books':       'Books',
        'book':        'Books'
    }
    return mapping.get(val.lower())

def clean_price(val):
    if val is None:
        return None
    # Remove $ , USD and surrounding spaces
    for token in ['$', 'USD', ',']:
        val = val.replace(token, '')
    val = val.strip()
    try:
        price = float(val)
        return price
    except Exception:
        return None

def clean_quantity(val):
    if val is None:
        return None
    try:
        qty = float(val)
        if abs(qty - round(qty)) > 1e-9:
            return None
        qty_int = int(round(qty))
        return qty_int
    except Exception:
        return None

def clean_discount(val):
    if val is None:
        return 0.0
    val = val.strip()
    if val.endswith('%'):
        val = val[:-1]
    try:
        disc = float(val)
        return disc
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------
def main():
    input_dir = os.getenv('INPUT_DIR')
    output_dir = os.getenv('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('INPUT_DIR and OUTPUT_DIR environment variables must be set')

    raw_path = os.path.join(input_dir, 'raw.csv')
    df_raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df_raw)

    # R1 – strip whitespace and normalise missing values for every cell
    df = df_raw.applymap(normalize_missing)

    # R2 – drop duplicate order_id, keep first occurrence
    before_dup = len(df)
    df = df.drop_duplicates(subset='order_id', keep='first')
    dup_removed = before_dup - len(df)

    # Prepare a dict to collect per‑rule drop counts
    drops = {
        'date': 0,
        'region': 0,
        'category': 0,
        'unit_price': 0,
        'quantity': 0,
        'discount_pct': 0
    }

    # -----------------------------------------------------------------------
    # R3 – order_date parsing
    # -----------------------------------------------------------------------
    df['order_date_parsed'] = df['order_date'].apply(parse_date)
    mask = df['order_date_parsed'].notna()
    drops['date'] = mask.size - mask.sum()
    df = df[mask]

    # -----------------------------------------------------------------------
    # R4 – region mapping
    # -----------------------------------------------------------------------
    df['region_mapped'] = df['region'].apply(map_region)
    mask = df['region_mapped'].notna()
    drops['region'] = mask.size - mask.sum()
    df = df[mask]

    # -----------------------------------------------------------------------
    # R5 – product_category mapping
    # -----------------------------------------------------------------------
    df['category_mapped'] = df['product_category'].apply(map_category)
    mask = df['category_mapped'].notna()
    drops['category'] = mask.size - mask.sum()
    df = df[mask]

    # -----------------------------------------------------------------------
    # R6 – unit_price cleaning & validation
    # -----------------------------------------------------------------------
    df['unit_price_clean'] = df['unit_price'].apply(clean_price)
    mask = df['unit_price_clean'].notna() & (df['unit_price_clean'] > 0) & (df['unit_price_clean'] <= 5000)
    drops['unit_price'] = mask.size - mask.sum()
    df = df[mask]

    # -----------------------------------------------------------------------
    # R7 – quantity cleaning & validation
    # -----------------------------------------------------------------------
    df['quantity_int'] = df['quantity'].apply(clean_quantity)
    mask = df['quantity_int'].notna() & (df['quantity_int'] >= 1) & (df['quantity_int'] <= 50)
    drops['quantity'] = mask.size - mask.sum()
    df = df[mask]

    # -----------------------------------------------------------------------
    # R8 – discount_pct cleaning & validation (missing -> 0)
    # -----------------------------------------------------------------------
    df['discount_clean'] = df['discount_pct'].apply(clean_discount)
    mask = df['discount_clean'].notna() & (df['discount_clean'] >= 0) & (df['discount_clean'] <= 100)
    drops['discount_pct'] = mask.size - mask.sum()
    df = df[mask]

    # -----------------------------------------------------------------------
    # R9 – customer_id handling
    # -----------------------------------------------------------------------
    df['customer_id_clean'] = df['customer_id'].apply(lambda x: 'UNKNOWN' if x is None else str(x).upper())

    # -----------------------------------------------------------------------
    # R10 – revenue calculation
    # -----------------------------------------------------------------------
    df['revenue'] = (
        df['quantity_int'] * df['unit_price_clean'] * (1 - df['discount_clean'] / 100)
    ).round(2)

    # -----------------------------------------------------------------------
    # R11 – final column selection & ordering
    # -----------------------------------------------------------------------
    final_df = df[[
        'order_id',
        'order_date_parsed',
        'customer_id_clean',
        'region_mapped',
        'category_mapped',
        'quantity_int',
        'unit_price_clean',
        'discount_clean',
        'revenue'
    ]].copy()
    final_df.columns = [
        'order_id',
        'order_date',
        'customer_id',
        'region',
        'product_category',
        'quantity',
        'unit_price',
        'discount_pct',
        'revenue'
    ]
    final_df = final_df.sort_values('order_id')

    cleaned_rows = len(final_df)

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    final_df.to_csv(cleaned_path, index=False)

    # Write cleaning summary JSON
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed': dup_removed,
        'drops': drops
    }
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
