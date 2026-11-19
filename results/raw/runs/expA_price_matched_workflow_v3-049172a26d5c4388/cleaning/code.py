import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

def parse_signup_date(val):
    """Parse signup_date using specified formats."""
    if not val:
        return None
    val = val.strip()
    
    formats = [
        '%Y-%m-%d',       # YYYY-MM-DD
        '%m/%d/%Y',       # MM/DD/YYYY
        '%d-%b-%Y',       # DD-Mon-YYYY
        '%Y/%m/%d',       # YYYY/MM/DD
        '%B %d, %Y',      # Month D, YYYY
        '%B %d,%Y',       # Month D,YYYY (no space after comma)
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def clean_data():
    input_dir = os.environ['INPUT_DIR']
    output_dir = os.environ['OUTPUT_DIR']
    
    # R1: Read as text, strip whitespace, handle missing values
    df = pd.read_csv(os.path.join(input_dir, 'raw.csv'), dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    missing_values = {'', 'na', 'n/a', 'null', 'none', '-'}
    
    def standardize_missing(val):
        if val is None:
            return ''
        val_stripped = str(val).strip()
        if val_stripped.lower() in missing_values:
            return ''
        return val_stripped
    
    for col in df.columns:
        df[col] = df[col].apply(standardize_missing)
    
    # R2: Remove duplicates (keep first occurrence)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['customer_id'], keep='first')
    duplicates_removed = before_dedup - len(df)
    
    # R3: signup_date
    before_r3 = len(df)
    df['signup_date'] = df['signup_date'].apply(parse_signup_date)
    df = df[df['signup_date'].notna() & (df['signup_date'] != '')]
    dropped_r3 = before_r3 - len(df)
    
    # R4: plan
    plan_map = {
        'basic': 'Basic',
        'basic plan': 'Basic',
        'standard': 'Standard',
        'std': 'Standard',
        'standard plan': 'Standard',
        'premium': 'Premium',
        'prem': 'Premium',
        'premium plan': 'Premium'
    }
    before_r4 = len(df)
    df['plan'] = df['plan'].str.lower().map(plan_map)
    df = df[df['plan'].notna()]
    dropped_r4 = before_r4 - len(df)
    
    # R5: contract_type
    contract_map = {
        'monthly': 'Monthly',
        'month-to-month': 'Monthly',
        'm2m': 'Monthly',
        'annual': 'Annual',
        'yearly': 'Annual',
        '1 year': 'Annual'
    }
    before_r5 = len(df)
    df['contract_type'] = df['contract_type'].str.lower().map(contract_map)
    df = df[df['contract_type'].notna()]
    dropped_r5 = before_r5 - len(df)
    
    # R6: monthly_fee
    def parse_monthly_fee(val):
        if not val:
            return np.nan
        val = val.replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            return float(val)
        except:
            return np.nan
    
    before_r6 = len(df)
    df['monthly_fee'] = df['monthly_fee'].apply(parse_monthly_fee)
    df = df[df['monthly_fee'].notna() & (df['monthly_fee'] > 0) & (df['monthly_fee'] <= 500)]
    dropped_r6 = before_r6 - len(df)
    
    # R7: tenure_months
    def parse_tenure(val):
        if not val:
            return np.nan
        val = val.strip().lower()
        val = val.replace('months', '').replace('month', '').strip()
        try:
            num = float(val)
            if num == int(num):
                return int(num)
            return np.nan
        except:
            return np.nan
    
    before_r7 = len(df)
    df['tenure_months'] = df['tenure_months'].apply(parse_tenure)
    df = df[df['tenure_months'].notna() & (df['tenure_months'] >= 0) & (df['tenure_months'] <= 120)]
    dropped_r7 = before_r7 - len(df)
    
    # R8: support_tickets
    def parse_support_tickets(val):
        if not val:
            return 0
        try:
            num = float(val)
            if num == int(num):
                return int(num)
            return np.nan
        except:
            return np.nan
    
    before_r8 = len(df)
    df['support_tickets'] = df['support_tickets'].apply(parse_support_tickets)
    df = df[df['support_tickets'].notna() & (df['support_tickets'] >= 0) & (df['support_tickets'] <= 100)]
    dropped_r8 = before_r8 - len(df)
    
    # R9: satisfaction_score
    def parse_satisfaction(val):
        if not val:
            return np.nan
        try:
            num = float(val)
            if num == int(num):
                num = int(num)
                if 1 <= num <= 5:
                    return num
            return np.nan
        except:
            return np.nan
    
    df['satisfaction_score'] = df['satisfaction_score'].apply(parse_satisfaction)
    
    # R10: churned
    churned_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1, 'churned': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0, 'active': 0
    }
    before_r10 = len(df)
    df['churned'] = df['churned'].str.lower().map(churned_map)
    df = df[df['churned'].notna()]
    dropped_r10 = before_r10 - len(df)
    
    # R11: lifetime_value
    df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)
    
    # R12: Sort and select columns
    df = df.sort_values('customer_id')
    output_cols = ['customer_id', 'signup_date', 'plan', 'contract_type', 
                   'monthly_fee', 'tenure_months', 'support_tickets', 
                   'satisfaction_score', 'churned', 'lifetime_value']
    df = df[output_cols]
    
    # Convert types for output
    df['tenure_months'] = df['tenure_months'].astype(int)
    df['support_tickets'] = df['support_tickets'].astype(int)
    df['churned'] = df['churned'].astype(int)
    df['satisfaction_score'] = df['satisfaction_score'].astype('Int64')  # Nullable integer
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    df.to_csv(os.path.join(output_dir, 'cleaned.csv'), index=False, na_rep='')
    
    # Write cleaning summary
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed': duplicates_removed,
        'dropped_signup_date': dropped_r3,
        'dropped_plan': dropped_r4,
        'dropped_contract_type': dropped_r5,
        'dropped_monthly_fee': dropped_r6,
        'dropped_tenure_months': dropped_r7,
        'dropped_support_tickets': dropped_r8,
        'dropped_churned': dropped_r10
    }
    
    with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()
