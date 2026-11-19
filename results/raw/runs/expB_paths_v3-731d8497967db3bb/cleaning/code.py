import os
import json
import re
import pandas as pd
import numpy as np
from datetime import datetime

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def strip_and_normalize(df):
    """Strip whitespace from all string cells and convert defined missing tokens to NaN."""
    missing_tokens = {'', 'na', 'n/a', 'null', 'none', '-'}
    def clean_cell(x):
        if isinstance(x, str):
            x = x.strip()
            if x.lower() in missing_tokens:
                return np.nan
            return x
        return x
    return df.applymap(clean_cell)

def parse_date(val):
    if pd.isna(val):
        return pd.NaT
    val = val.strip()
    date_formats = [
        "%Y-%m-%d",          # 2021-01-01
        "%m/%d/%Y",          # 01/21/2021
        "%d-%b-%Y",          # 07-Jan-2021 (abbr month)
        "%Y/%m/%d",          # 2021/01/07
        "%B %d, %Y",         # March 5, 2024
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return pd.NaT

def map_plan(val):
    if pd.isna(val):
        return np.nan
    mapping = {
        'basic': 'Basic',
        'basic plan': 'Basic',
        'standard': 'Standard',
        'std': 'Standard',
        'standard plan': 'Standard',
        'premium': 'Premium',
        'prem': 'Premium',
        'premium plan': 'Premium',
    }
    key = val.strip().lower()
    return mapping.get(key, np.nan)

def map_contract(val):
    if pd.isna(val):
        return np.nan
    mapping = {
        'monthly': 'Monthly',
        'month-to-month': 'Monthly',
        'm2m': 'Monthly',
        'annual': 'Annual',
        'yearly': 'Annual',
        '1 year': 'Annual',
    }
    key = val.strip().lower()
    return mapping.get(key, np.nan)

def clean_monthly_fee(val):
    if pd.isna(val):
        return np.nan
    # remove $ , USD and surrounding spaces
    val = re.sub(r'\$|,', '', val, flags=re.IGNORECASE)
    val = re.sub(r'usd', '', val, flags=re.IGNORECASE)
    val = val.strip()
    try:
        num = float(val)
        return num
    except ValueError:
        return np.nan

def clean_tenure(val):
    if pd.isna(val):
        return np.nan
    # remove trailing 'month' or 'months'
    val = re.sub(r'(?i)\s*months?\s*$', '', val)
    val = val.strip()
    if not val:
        return np.nan
    try:
        num = float(val)
        if num.is_integer():
            return int(num)
        else:
            return np.nan
    except ValueError:
        return np.nan

def clean_support_tickets(val):
    if pd.isna(val):
        return 0
    val = val.strip()
    if not val:
        return 0
    try:
        num = float(val)
        if num.is_integer():
            return int(num)
        else:
            return np.nan
    except ValueError:
        return np.nan

def clean_satisfaction(val):
    if pd.isna(val):
        return np.nan
    val = val.strip()
    if not val:
        return np.nan
    try:
        num = float(val)
        if num.is_integer():
            iv = int(num)
            if 1 <= iv <= 5:
                return iv
        return np.nan
    except ValueError:
        return np.nan

def map_churned(val):
    if pd.isna(val):
        return np.nan
    mapping = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1, 'churned': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0, 'active': 0,
    }
    key = val.strip().lower()
    return mapping.get(key, np.nan)

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get('INPUT_DIR')
    output_dir = os.environ.get('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('INPUT_DIR and OUTPUT_DIR environment variables must be set')

    raw_path = os.path.join(input_dir, 'raw.csv')
    df_raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_values=[])
    raw_rows = len(df_raw)

    summary = {
        'raw_rows': raw_rows,
        'duplicates_removed': 0,
        'rows_dropped_R3_signup_date': 0,
        'rows_dropped_R4_plan': 0,
        'rows_dropped_R5_contract_type': 0,
        'rows_dropped_R6_monthly_fee': 0,
        'rows_dropped_R7_tenure_months': 0,
        'rows_dropped_R8_support_tickets': 0,
        'rows_dropped_R10_churned': 0,
        'cleaned_rows': 0,
    }

    # R1 – strip whitespace and normalise missing tokens
    df = strip_and_normalize(df_raw)

    # R2 – remove duplicate customer_id, keep first
    before_dup = len(df)
    df = df.drop_duplicates(subset=['customer_id'], keep='first')
    summary['duplicates_removed'] = before_dup - len(df)

    # R3 – signup_date parsing
    df['signup_date_parsed'] = df['signup_date'].apply(parse_date)
    before = len(df)
    df = df[~df['signup_date_parsed'].isna()]
    summary['rows_dropped_R3_signup_date'] = before - len(df)
    df['signup_date'] = df['signup_date_parsed'].astype(str)  # YYYY-MM-DD format
    df = df.drop(columns=['signup_date_parsed'])

    # R4 – plan mapping
    df['plan_mapped'] = df['plan'].apply(map_plan)
    before = len(df)
    df = df[~df['plan_mapped'].isna()]
    summary['rows_dropped_R4_plan'] = before - len(df)
    df['plan'] = df['plan_mapped']
    df = df.drop(columns=['plan_mapped'])

    # R5 – contract_type mapping
    df['contract_mapped'] = df['contract_type'].apply(map_contract)
    before = len(df)
    df = df[~df['contract_mapped'].isna()]
    summary['rows_dropped_R5_contract_type'] = before - len(df)
    df['contract_type'] = df['contract_mapped']
    df = df.drop(columns=['contract_mapped'])

    # R6 – monthly_fee cleaning
    df['monthly_fee_clean'] = df['monthly_fee'].apply(clean_monthly_fee)
    before = len(df)
    df = df[~df['monthly_fee_clean'].isna()]
    df = df[(df['monthly_fee_clean'] > 0) & (df['monthly_fee_clean'] <= 500)]
    summary['rows_dropped_R6_monthly_fee'] = before - len(df)
    df['monthly_fee'] = df['monthly_fee_clean']
    df = df.drop(columns=['monthly_fee_clean'])

    # R7 – tenure_months cleaning
    df['tenure_clean'] = df['tenure_months'].apply(clean_tenure)
    before = len(df)
    df = df[~df['tenure_clean'].isna()]
    df = df[(df['tenure_clean'] >= 0) & (df['tenure_clean'] <= 120)]
    summary['rows_dropped_R7_tenure_months'] = before - len(df)
    df['tenure_months'] = df['tenure_clean']
    df = df.drop(columns=['tenure_clean'])

    # R8 – support_tickets cleaning (missing -> 0)
    df['support_clean'] = df['support_tickets'].apply(clean_support_tickets)
    before = len(df)
    df = df[~df['support_clean'].isna()]
    df = df[(df['support_clean'] >= 0) & (df['support_clean'] <= 100)]
    summary['rows_dropped_R8_support_tickets'] = before - len(df)
    df['support_tickets'] = df['support_clean']
    df = df.drop(columns=['support_clean'])

    # R9 – satisfaction_score (invalid -> missing, keep row)
    df['satisfaction_clean'] = df['satisfaction_score'].apply(clean_satisfaction)
    df['satisfaction_score'] = df['satisfaction_clean']
    df = df.drop(columns=['satisfaction_clean'])

    # R10 – churned mapping
    df['churned_mapped'] = df['churned'].apply(map_churned)
    before = len(df)
    df = df[~df['churned_mapped'].isna()]
    summary['rows_dropped_R10_churned'] = before - len(df)
    df['churned'] = df['churned_mapped'].astype(int)
    df = df.drop(columns=['churned_mapped'])

    # Convert numeric columns to proper dtypes
    df['monthly_fee'] = df['monthly_fee'].astype(float)
    df['tenure_months'] = df['tenure_months'].astype(int)
    df['support_tickets'] = df['support_tickets'].astype(int)
    # satisfaction_score already int or NaN (float), keep as is

    # R11 – lifetime_value
    df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)

    # R12 – final column order and sorting
    final_cols = [
        'customer_id', 'signup_date', 'plan', 'contract_type',
        'monthly_fee', 'tenure_months', 'support_tickets',
        'satisfaction_score', 'churned', 'lifetime_value'
    ]
    df = df[final_cols]
    df = df.sort_values('customer_id')

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(cleaned_path, index=False, float_format='%.2f', na_rep='')

    # Summary JSON
    summary['cleaned_rows'] = len(df)
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
