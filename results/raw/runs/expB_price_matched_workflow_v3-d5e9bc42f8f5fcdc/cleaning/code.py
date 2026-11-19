import os
import json
import re
import pandas as pd
import numpy as np
from datetime import datetime

def parse_signup_date(val):
    """Parse signup_date using specified formats."""
    if not val:
        return None
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d-%b-%Y',
        '%Y/%m/%d',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    # Try 'Month D, YYYY' format
    match = re.match(r'^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})$', val)
    if match:
        month_str, day_str, year_str = match.groups()
        try:
            dt = datetime.strptime(f"{month_str} {day_str} {year_str}", '%B %d %Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
    return None

def clean_data():
    input_dir = os.environ['INPUT_DIR']
    output_dir = os.environ['OUTPUT_DIR']
    raw_path = os.path.join(input_dir, 'raw.csv')
    
    # R1: Read as text, strip whitespace
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    # R1: Treat specific values as missing
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    df = df.applymap(lambda x: '' if isinstance(x, str) and x.lower() in [v.lower() for v in missing_vals] else x)
    
    raw_rows = len(df)
    
    # R2: Remove duplicates by customer_id, keep first
    df = df.drop_duplicates(subset='customer_id', keep='first')
    
    # R3: signup_date parsing
    df['signup_date_parsed'] = df['signup_date'].apply(parse_signup_date)
    df = df[df['signup_date_parsed'].notna() & (df['signup_date_parsed'] != '')]
    df['signup_date'] = df['signup_date_parsed']
    df.drop(columns=['signup_date_parsed'], inplace=True)
    
    # R4: plan mapping
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
    df['plan'] = df['plan'].str.lower().str.strip()
    df['plan'] = df['plan'].map(plan_map)
    df = df[df['plan'].notna()]
    
    # R5: contract_type mapping
    contract_map = {
        'monthly': 'Monthly',
        'month-to-month': 'Monthly',
        'm2m': 'Monthly',
        'annual': 'Annual',
        'yearly': 'Annual',
        '1 year': 'Annual'
    }
    df['contract_type'] = df['contract_type'].str.lower().str.strip()
    df['contract_type'] = df['contract_type'].map(contract_map)
    df = df[df['contract_type'].notna()]
    
    # R6: monthly_fee
    def clean_fee(val):
        if not val:
            return np.nan
        val = val.replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            return float(val)
        except:
            return np.nan
    df['monthly_fee'] = df['monthly_fee'].apply(clean_fee)
    df = df[df['monthly_fee'].notna()]
    df = df[(df['monthly_fee'] > 0) & (df['monthly_fee'] <= 500)]
    
    # R7: tenure_months
    def clean_tenure(val):
        if not val:
            return np.nan
        val = re.sub(r'\s*months?\s*$', '', val, flags=re.IGNORECASE).strip()
        try:
            f = float(val)
            if f == int(f):
                return int(f)
            return np.nan
        except:
            return np.nan
    df['tenure_months'] = df['tenure_months'].apply(clean_tenure)
    df = df[df['tenure_months'].notna()]
    df = df[(df['tenure_months'] >= 0) & (df['tenure_months'] <= 120)]
    
    # R8: support_tickets
    def clean_tickets(val):
        if not val:
            return 0
        try:
            f = float(val)
            if f == int(f):
                return int(f)
            return np.nan
        except:
            return np.nan
    df['support_tickets'] = df['support_tickets'].apply(clean_tickets)
    df = df[df['support_tickets'].notna()]
    df = df[(df['support_tickets'] >= 0) & (df['support_tickets'] <= 100)]
    
    # R9: satisfaction_score
    def clean_satisfaction(val):
        if not val:
            return np.nan
        try:
            f = float(val)
            if f == int(f) and 1 <= f <= 5:
                return int(f)
            return np.nan
        except:
            return np.nan
    df['satisfaction_score'] = df['satisfaction_score'].apply(clean_satisfaction)
    # Keep rows even if satisfaction_score is NaN
    
    # R10: churned
    churn_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1, 'churned': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0, 'active': 0
    }
    df['churned'] = df['churned'].str.lower().str.strip()
    df['churned'] = df['churned'].map(churn_map)
    df = df[df['churned'].notna()]
    df['churned'] = df['churned'].astype(int)
    
    # R11: lifetime_value
    df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)
    
    # R12: Sort and select columns
    df = df.sort_values('customer_id')
    cols = ['customer_id', 'signup_date', 'plan', 'contract_type', 'monthly_fee', 
            'tenure_months', 'support_tickets', 'satisfaction_score', 'churned', 'lifetime_value']
    df = df[cols]
    
    cleaned_rows = len(df)
    
    # Write outputs
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(cleaned_path, index=False, na_rep='')
    
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows
    }
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()