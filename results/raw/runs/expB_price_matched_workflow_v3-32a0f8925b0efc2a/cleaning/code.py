import os
import json
import re
import pandas as pd
import numpy as np
from datetime import datetime

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # R1: Read as text, strip whitespace
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # R1: Normalize missing values
    missing_vals = ['', 'na', 'n/a', 'null', 'none', '-']
    df = df.applymap(lambda x: '' if isinstance(x, str) and x.lower() in missing_vals else x)

    # R2: Remove duplicates (keep first)
    df = df.drop_duplicates(subset=['customer_id'], keep='first')

    # R3: Parse signup_date
    def parse_date(val):
        if not val: return None
        # YYYY-MM-DD
        try: return datetime.strptime(val, '%Y-%m-%d').date()
        except: pass
        # MM/DD/YYYY
        try: return datetime.strptime(val, '%m/%d/%Y').date()
        except: pass
        # DD-Mon-YYYY
        try: return datetime.strptime(val, '%d-%b-%Y').date()
        except: pass
        # YYYY/MM/DD
        try: return datetime.strptime(val, '%Y/%m/%d').date()
        except: pass
        # Month D, YYYY
        try: return datetime.strptime(val, '%B %d, %Y').date()
        except: pass
        return None

    df['signup_date_parsed'] = df['signup_date'].apply(parse_date)
    df = df[df['signup_date_parsed'].notna()]
    df['signup_date'] = df['signup_date_parsed'].apply(lambda x: x.strftime('%Y-%m-%d'))
    df.drop(columns=['signup_date_parsed'], inplace=True)

    # R4: Map plan
    plan_map = {
        'basic': 'Basic', 'basic plan': 'Basic',
        'standard': 'Standard', 'std': 'Standard', 'standard plan': 'Standard',
        'premium': 'Premium', 'prem': 'Premium', 'premium plan': 'Premium'
    }
    df['plan'] = df['plan'].str.lower().map(plan_map)
    df = df[df['plan'].notna()]

    # R5: Map contract_type
    contract_map = {
        'monthly': 'Monthly', 'month-to-month': 'Monthly', 'm2m': 'Monthly',
        'annual': 'Annual', 'yearly': 'Annual', '1 year': 'Annual'
    }
    df['contract_type'] = df['contract_type'].str.lower().map(contract_map)
    df = df[df['contract_type'].notna()]

    # R6: Parse monthly_fee
    def parse_fee(val):
        if not val: return np.nan
        val = val.replace('$', '').replace('USD', '').replace(',', '').strip()
        try: return float(val)
        except: return np.nan
    df['monthly_fee'] = df['monthly_fee'].apply(parse_fee)
    df = df[df['monthly_fee'].notna()]
    df = df[(df['monthly_fee'] > 0) & (df['monthly_fee'] <= 500)]

    # R7: Parse tenure_months
    def parse_tenure(val):
        if not val: return np.nan
        val = re.sub(r'\s*months?\s*$', '', val, flags=re.IGNORECASE).strip()
        try:
            f = float(val)
            if f.is_integer(): return int(f)
            return np.nan
        except: return np.nan
    df['tenure_months'] = df['tenure_months'].apply(parse_tenure)
    df = df[df['tenure_months'].notna()]
    df = df[(df['tenure_months'] >= 0) & (df['tenure_months'] <= 120)]

    # R8: Parse support_tickets
    def parse_tickets(val):
        if not val: return 0
        try:
            f = float(val)
            if f.is_integer(): return int(f)
            return np.nan
        except: return np.nan
    df['support_tickets'] = df['support_tickets'].apply(parse_tickets)
    df = df[df['support_tickets'].notna()]
    df = df[(df['support_tickets'] >= 0) & (df['support_tickets'] <= 100)]

    # R9: Parse satisfaction_score
    def parse_satisfaction(val):
        if not val: return np.nan
        try:
            f = float(val)
            if f.is_integer() and 1 <= f <= 5: return int(f)
            return np.nan
        except: return np.nan
    df['satisfaction_score'] = df['satisfaction_score'].apply(parse_satisfaction)

    # R10: Map churned
    churn_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1, 'churned': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0, 'active': 0
    }
    df['churned'] = df['churned'].str.lower().map(churn_map)
    df = df[df['churned'].notna()]

    # R11: Calculate lifetime_value
    df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)

    # R12: Final formatting
    final_cols = ['customer_id', 'signup_date', 'plan', 'contract_type', 'monthly_fee', 
                  'tenure_months', 'support_tickets', 'satisfaction_score', 'churned', 'lifetime_value']
    df = df[final_cols]
    df = df.sort_values('customer_id')
    
    # Write outputs
    df.to_csv(cleaned_path, index=False)
    
    cleaned_rows = len(df)
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows
    }
    with open(summary_path, 'w') as f:
        json.dump(summary, f)

if __name__ == "__main__":
    clean_data()