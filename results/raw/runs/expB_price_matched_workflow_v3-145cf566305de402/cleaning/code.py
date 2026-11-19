import os
import json
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
        '%B %d, %Y'
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
    
    # Strip whitespace
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    # Define missing values
    missing_vals = ['', 'na', 'n/a', 'null', 'none', '-']
    df = df.applymap(lambda x: '' if isinstance(x, str) and x.lower() in missing_vals else x)
    
    # R2: Remove duplicates
    df = df.drop_duplicates(subset=['customer_id'], keep='first')
    
    # R3: signup_date
    df['signup_date'] = df['signup_date'].apply(parse_signup_date)
    df = df[df['signup_date'].notna() & (df['signup_date'] != '')]
    
    # R4: plan
    plan_map = {
        'basic': 'Basic', 'basic plan': 'Basic',
        'standard': 'Standard', 'std': 'Standard', 'standard plan': 'Standard',
        'premium': 'Premium', 'prem': 'Premium', 'premium plan': 'Premium'
    }
    df['plan'] = df['plan'].str.lower().map(plan_map)
    df = df[df['plan'].notna()]
    
    # R5: contract_type
    contract_map = {
        'monthly': 'Monthly', 'month-to-month': 'Monthly', 'm2m': 'Monthly',
        'annual': 'Annual', 'yearly': 'Annual', '1 year': 'Annual'
    }
    df['contract_type'] = df['contract_type'].str.lower().map(contract_map)
    df = df[df['contract_type'].notna()]
    
    # R6: monthly_fee
    df['monthly_fee'] = df['monthly_fee'].str.replace(r'\$|USD|,', '', regex=True).str.strip()
    df['monthly_fee'] = pd.to_numeric(df['monthly_fee'], errors='coerce')
    df = df[df['monthly_fee'].notna() & (df['monthly_fee'] > 0) & (df['monthly_fee'] <= 500)]
    
    # R7: tenure_months
    df['tenure_months'] = df['tenure_months'].str.replace(r'\s*months?\s*$', '', case=False, regex=True).str.strip()
    df['tenure_months'] = pd.to_numeric(df['tenure_months'], errors='coerce')
    df = df[df['tenure_months'].notna() & (df['tenure_months'] == df['tenure_months'].astype(int))]
    df['tenure_months'] = df['tenure_months'].astype(int)
    df = df[(df['tenure_months'] >= 0) & (df['tenure_months'] <= 120)]
    
    # R8: support_tickets
    df['support_tickets'] = df['support_tickets'].replace('', '0')
    df['support_tickets'] = pd.to_numeric(df['support_tickets'], errors='coerce')
    df = df[df['support_tickets'].notna() & (df['support_tickets'] == df['support_tickets'].astype(int))]
    df['support_tickets'] = df['support_tickets'].astype(int)
    df = df[(df['support_tickets'] >= 0) & (df['support_tickets'] <= 100)]
    
    # R9: satisfaction_score
    df['satisfaction_score'] = pd.to_numeric(df['satisfaction_score'], errors='coerce')
    # Check whole number
    df['satisfaction_score'] = df['satisfaction_score'].apply(lambda x: int(x) if pd.notna(x) and x == int(x) and 1 <= int(x) <= 5 else np.nan)
    
    # R10: churned
    churn_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1, 'churned': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0, 'active': 0
    }
    df['churned'] = df['churned'].str.lower().map(churn_map)
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
    
    # Write cleaned CSV
    df.to_csv(os.path.join(output_dir, 'cleaned.csv'), index=False)
    
    # Write summary
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows
    }
    with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()