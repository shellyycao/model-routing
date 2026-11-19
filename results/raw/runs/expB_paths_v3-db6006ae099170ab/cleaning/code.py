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
    """Try the allowed date formats, return a string YYYY-MM-DD or NaT."""
    if pd.isna(val):
        return pd.NaT
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            continue
    return pd.NaT

def clean_monthly_fee(val):
    if pd.isna(val):
        return np.nan
    # remove $ , USD and surrounding spaces
    cleaned = re.sub(r"\$|USD|,", "", str(val), flags=re.IGNORECASE).strip()
    try:
        num = float(cleaned)
        return num
    except Exception:
        return np.nan

def clean_tenure(val):
    if pd.isna(val):
        return np.nan
    # remove trailing word month(s)
    cleaned = re.sub(r"(?i)\s*months?$", "", str(val)).strip()
    try:
        num = float(cleaned)
        if num.is_integer():
            return int(num)
        return np.nan
    except Exception:
        return np.nan

def clean_support_tickets(val):
    if pd.isna(val):
        return 0
    try:
        num = float(val)
        if num.is_integer():
            return int(num)
        return np.nan
    except Exception:
        return np.nan

def clean_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        num = float(val)
        if num.is_integer() and 1 <= int(num) <= 5:
            return int(num)
        else:
            return np.nan
    except Exception:
        return np.nan

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
        'premium plan': 'Premium'
    }
    return mapping.get(val.lower())

def map_contract(val):
    if pd.isna(val):
        return np.nan
    mapping = {
        'monthly': 'Monthly',
        'month-to-month': 'Monthly',
        'm2m': 'Monthly',
        'annual': 'Annual',
        'yearly': 'Annual',
        '1 year': 'Annual'
    }
    return mapping.get(val.lower())

def map_churned(val):
    if pd.isna(val):
        return np.nan
    yes_set = {'yes', 'y', 'true', '1', 'churned'}
    no_set = {'no', 'n', 'false', '0', 'active'}
    low = val.lower()
    if low in yes_set:
        return 1
    if low in no_set:
        return 0
    return np.nan

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get('INPUT_DIR')
    output_dir = os.environ.get('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('INPUT_DIR and OUTPUT_DIR environment variables must be set')

    raw_path = os.path.join(input_dir, 'raw.csv')
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_values=[])
    raw_rows = len(df)

    summary = {
        'raw_rows': raw_rows,
        'duplicate_rows_removed': 0,
        'rows_dropped_R3': 0,
        'rows_dropped_R4': 0,
        'rows_dropped_R5': 0,
        'rows_dropped_R6': 0,
        'rows_dropped_R7': 0,
        'rows_dropped_R8': 0,
        'rows_dropped_R10': 0,
        'cleaned_rows': 0
    }

    # R1 – strip whitespace and normalise missing tokens
    df = strip_and_normalize(df)

    # R2 – remove duplicate customer_id, keep first
    before_dup = len(df)
    df = df.drop_duplicates(subset='customer_id', keep='first')
    summary['duplicate_rows_removed'] = before_dup - len(df)

    # R3 – signup_date parsing
    df['signup_date_parsed'] = df['signup_date'].apply(parse_date)
    mask_r3 = df['signup_date_parsed'].notna()
    summary['rows_dropped_R3'] = len(df) - mask_r3.sum()
    df = df[mask_r3].copy()
    df['signup_date'] = df['signup_date_parsed']
    df.drop(columns=['signup_date_parsed'], inplace=True)

    # R4 – plan mapping
    df['plan_mapped'] = df['plan'].apply(map_plan)
    mask_r4 = df['plan_mapped'].notna()
    summary['rows_dropped_R4'] = len(df) - mask_r4.sum()
    df = df[mask_r4].copy()
    df['plan'] = df['plan_mapped']
    df.drop(columns=['plan_mapped'], inplace=True)

    # R5 – contract_type mapping
    df['contract_mapped'] = df['contract_type'].apply(map_contract)
    mask_r5 = df['contract_mapped'].notna()
    summary['rows_dropped_R5'] = len(df) - mask_r5.sum()
    df = df[mask_r5].copy()
    df['contract_type'] = df['contract_mapped']
    df.drop(columns=['contract_mapped'], inplace=True)

    # R6 – monthly_fee cleaning
    df['monthly_fee_clean'] = df['monthly_fee'].apply(clean_monthly_fee)
    mask_r6 = df['monthly_fee_clean'].notna() & (df['monthly_fee_clean'] > 0) & (df['monthly_fee_clean'] <= 500)
    summary['rows_dropped_R6'] = len(df) - mask_r6.sum()
    df = df[mask_r6].copy()
    df['monthly_fee'] = df['monthly_fee_clean']
    df.drop(columns=['monthly_fee_clean'], inplace=True)

    # R7 – tenure_months cleaning
    df['tenure_clean'] = df['tenure_months'].apply(clean_tenure)
    mask_r7 = df['tenure_clean'].notna() & (df['tenure_clean'] >= 0) & (df['tenure_clean'] <= 120)
    summary['rows_dropped_R7'] = len(df) - mask_r7.sum()
    df = df[mask_r7].copy()
    df['tenure_months'] = df['tenure_clean']
    df.drop(columns=['tenure_clean'], inplace=True)

    # R8 – support_tickets cleaning (missing -> 0)
    df['support_clean'] = df['support_tickets'].apply(clean_support_tickets)
    mask_r8 = df['support_clean'].notna() & (df['support_clean'] >= 0) & (df['support_clean'] <= 100)
    summary['rows_dropped_R8'] = len(df) - mask_r8.sum()
    df = df[mask_r8].copy()
    df['support_tickets'] = df['support_clean']
    df.drop(columns=['support_clean'], inplace=True)

    # R9 – satisfaction_score (invalid -> missing, keep row)
    df['satisfaction_clean'] = df['satisfaction_score'].apply(clean_satisfaction)
    df['satisfaction_score'] = df['satisfaction_clean']
    df.drop(columns=['satisfaction_clean'], inplace=True)

    # R10 – churned mapping
    df['churned_mapped'] = df['churned'].apply(map_churned)
    mask_r10 = df['churned_mapped'].notna()
    summary['rows_dropped_R10'] = len(df) - mask_r10.sum()
    df = df[mask_r10].copy()
    df['churned'] = df['churned_mapped'].astype(int)
    df.drop(columns=['churned_mapped'], inplace=True)

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
    df.sort_values('customer_id', inplace=True)

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(cleaned_path, index=False, float_format='%.2f', na_rep='')

    # Update summary
    summary['cleaned_rows'] = len(df)
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
