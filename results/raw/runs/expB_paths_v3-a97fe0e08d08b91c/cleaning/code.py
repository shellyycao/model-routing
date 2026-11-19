import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import re

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def normalize_missing(val):
    """Return np.nan for values considered missing according to R1."""
    if pd.isna(val):
        return np.nan
    if isinstance(val, str):
        v = val.strip()
        if v.lower() in {'', 'na', 'n/a', 'null', 'none', '-'}:
            return np.nan
        return v
    return val

def parse_date(val):
    """Parse date according to the allowed formats (R3). Return YYYY-MM-DD string or None."""
    if pd.isna(val):
        return None
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return None

def map_plan(val):
    if pd.isna(val):
        return None
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
        return None
    mapping = {
        'monthly': 'Monthly',
        'month-to-month': 'Monthly',
        'm2m': 'Monthly',
        'annual': 'Annual',
        'yearly': 'Annual',
        '1 year': 'Annual'
    }
    return mapping.get(val.lower())

def clean_monthly_fee(val):
    if pd.isna(val):
        return None
    # Remove $, USD, commas and surrounding spaces
    cleaned = re.sub(r"\$|USD|,", "", val, flags=re.IGNORECASE).strip()
    try:
        num = float(cleaned)
        return num
    except Exception:
        return None

def clean_tenure(val):
    if pd.isna(val):
        return None
    # Remove trailing 'month' or 'months' (case‑insensitive)
    cleaned = re.sub(r"(?i)\s*months?$", "", val).strip()
    try:
        num = float(cleaned)
        if not num.is_integer():
            return None
        return int(num)
    except Exception:
        return None

def clean_support_tickets(val):
    if pd.isna(val):
        return 0
    try:
        num = float(val)
        if not num.is_integer():
            return None
        return int(num)
    except Exception:
        return None

def clean_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        num = float(val)
        if not num.is_integer():
            return np.nan
        iv = int(num)
        if 1 <= iv <= 5:
            return iv
        else:
            return np.nan
    except Exception:
        return np.nan

def map_churned(val):
    if pd.isna(val):
        return None
    mapping = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1, 'churned': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0, 'active': 0
    }
    return mapping.get(val.lower())

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get('INPUT_DIR')
    output_dir = os.environ.get('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('INPUT_DIR and OUTPUT_DIR environment variables must be set')

    raw_path = os.path.join(input_dir, 'raw.csv')
    df_raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df_raw)

    # R1 – strip whitespace and normalise missing values
    df = df_raw.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.applymap(normalize_missing)

    # Counters for summary
    summary = {
        'raw_rows': raw_rows,
        'duplicates_removed': 0,
        'signup_date_invalid': 0,
        'plan_invalid': 0,
        'contract_type_invalid': 0,
        'monthly_fee_invalid': 0,
        'tenure_months_invalid': 0,
        'support_tickets_invalid': 0,
        'churned_invalid': 0,
        'cleaned_rows': 0
    }

    # R2 – remove duplicate customer_id, keep first
    dup_mask = df.duplicated(subset='customer_id', keep='first')
    summary['duplicates_removed'] = int(dup_mask.sum())
    df = df[~dup_mask]

    # R3 – signup_date parsing
    df['signup_date_parsed'] = df['signup_date'].apply(parse_date)
    invalid_signup = df['signup_date_parsed'].isna()
    summary['signup_date_invalid'] = int(invalid_signup.sum())
    df = df[~invalid_signup]
    df = df.drop(columns=['signup_date'])
    df = df.rename(columns={'signup_date_parsed': 'signup_date'})

    # R4 – plan mapping
    df['plan_mapped'] = df['plan'].apply(map_plan)
    invalid_plan = df['plan_mapped'].isna()
    summary['plan_invalid'] = int(invalid_plan.sum())
    df = df[~invalid_plan]
    df = df.drop(columns=['plan']).rename(columns={'plan_mapped': 'plan'})

    # R5 – contract_type mapping
    df['contract_mapped'] = df['contract_type'].apply(map_contract)
    invalid_contract = df['contract_mapped'].isna()
    summary['contract_type_invalid'] = int(invalid_contract.sum())
    df = df[~invalid_contract]
    df = df.drop(columns=['contract_type']).rename(columns={'contract_mapped': 'contract_type'})

    # R6 – monthly_fee cleaning
    df['monthly_fee_clean'] = df['monthly_fee'].apply(clean_monthly_fee)
    invalid_fee = df['monthly_fee_clean'].isna() | (df['monthly_fee_clean'] <= 0) | (df['monthly_fee_clean'] > 500)
    summary['monthly_fee_invalid'] = int(invalid_fee.sum())
    df = df[~invalid_fee]
    df = df.drop(columns=['monthly_fee']).rename(columns={'monthly_fee_clean': 'monthly_fee'})

    # R7 – tenure_months cleaning
    df['tenure_clean'] = df['tenure_months'].apply(clean_tenure)
    invalid_tenure = df['tenure_clean'].isna() | (df['tenure_clean'] < 0) | (df['tenure_clean'] > 120)
    summary['tenure_months_invalid'] = int(invalid_tenure.sum())
    df = df[~invalid_tenure]
    df = df.drop(columns=['tenure_months']).rename(columns={'tenure_clean': 'tenure_months'})

    # R8 – support_tickets cleaning (missing -> 0)
    df['support_clean'] = df['support_tickets'].apply(clean_support_tickets)
    invalid_support = df['support_clean'].isna() | (df['support_clean'] < 0) | (df['support_clean'] > 100)
    summary['support_tickets_invalid'] = int(invalid_support.sum())
    df = df[~invalid_support]
    df = df.drop(columns=['support_tickets']).rename(columns={'support_clean': 'support_tickets'})

    # R9 – satisfaction_score cleaning (invalid -> missing, keep row)
    df['satisfaction_clean'] = df['satisfaction_score'].apply(clean_satisfaction)
    df = df.drop(columns=['satisfaction_score']).rename(columns={'satisfaction_clean': 'satisfaction_score'})

    # R10 – churned mapping
    df['churned_mapped'] = df['churned'].apply(map_churned)
    invalid_churn = df['churned_mapped'].isna()
    summary['churned_invalid'] = int(invalid_churn.sum())
    df = df[~invalid_churn]
    df = df.drop(columns=['churned']).rename(columns={'churned_mapped': 'churned'})

    # Ensure correct dtypes
    df['monthly_fee'] = df['monthly_fee'].astype(float)
    df['tenure_months'] = df['tenure_months'].astype(int)
    df['support_tickets'] = df['support_tickets'].astype(int)
    df['churned'] = df['churned'].astype(int)
    # satisfaction_score may be NaN; keep as float then convert to Int64 nullable
    df['satisfaction_score'] = df['satisfaction_score'].astype('Int64')

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
    df.to_csv(cleaned_path, index=False, na_rep='')

    # Summary JSON
    summary['cleaned_rows'] = len(df)
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
