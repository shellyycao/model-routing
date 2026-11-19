import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    raw_path = os.path.join(input_dir, "raw.csv")
    
    # R1: Read all columns as text
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # R1: Strip whitespace and standardize missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    def standardize_value(val):
        if pd.isna(val):
            return np.nan
        val_str = str(val).strip()
        if val_str.lower() in [m.lower() for m in missing_vals]:
            return np.nan
        return val_str
    
    for col in df.columns:
        df[col] = df[col].apply(standardize_value)
    
    # R2: Remove duplicates based on customer_id, keep first
    df.drop_duplicates(subset=['customer_id'], keep='first', inplace=True)
    
    # R3: Parse signup_date
    def parse_signup_date(val):
        if pd.isna(val):
            return None
        # Try YYYY-MM-DD
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']:
            try:
                return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None
    
    df['signup_date'] = df['signup_date'].apply(parse_signup_date)
    df = df[df['signup_date'].notna()]
    
    # R4: Map plan
    plan_map = {
        'basic': 'Basic', 'basic plan': 'Basic',
        'standard': 'Standard', 'std': 'Standard', 'standard plan': 'Standard',
        'premium': 'Premium', 'prem': 'Premium', 'premium plan': 'Premium'
    }
    def map_plan(val):
        if pd.isna(val):
            return None
        return plan_map.get(val.lower())
    
    df['plan'] = df['plan'].apply(map_plan)
    df = df[df['plan'].notna()]
    
    # R5: Map contract_type
    contract_map = {
        'monthly': 'Monthly', 'month-to-month': 'Monthly', 'm2m': 'Monthly',
        'annual': 'Annual', 'yearly': 'Annual', '1 year': 'Annual'
    }
    def map_contract(val):
        if pd.isna(val):
            return None
        return contract_map.get(val.lower())
    
    df['contract_type'] = df['contract_type'].apply(map_contract)
    df = df[df['contract_type'].notna()]
    
    # R6: Clean monthly_fee
    def clean_fee(val):
        if pd.isna(val):
            return np.nan
        val = re.sub(r'\$|USD|,', '', val, flags=re.I).strip()
        try:
            return float(val)
        except:
            return np.nan
    
    df['monthly_fee'] = df['monthly_fee'].apply(clean_fee)
    df = df[df['monthly_fee'].notna() & (df['monthly_fee'] > 0) & (df['monthly_fee'] <= 500)]
    
    # R7: Clean tenure_months
    def clean_tenure(val):
        if pd.isna(val):
            return np.nan
        val = re.sub(r'months?$', '', val, flags=re.I).strip()
        try:
            f = float(val)
            if f == int(f):
                return int(f)
            return np.nan
        except:
            return np.nan
    
    df['tenure_months'] = df['tenure_months'].apply(clean_tenure)
    df = df[df['tenure_months'].notna() & (df['tenure_months'] >= 0) & (df['tenure_months'] <= 120)]
    
    # R8: Clean support_tickets
    def clean_tickets(val):
        if pd.isna(val):
            return 0
        try:
            f = float(val)
            if f == int(f):
                return int(f)
            return np.nan
        except:
            return np.nan
    
    df['support_tickets'] = df['support_tickets'].apply(clean_tickets)
    df = df[df['support_tickets'].notna() & (df['support_tickets'] >= 0) & (df['support_tickets'] <= 100)]
    
    # R9: Clean satisfaction_score
    def clean_satisfaction(val):
        if pd.isna(val):
            return np.nan
        try:
            f = float(val)
            if f == int(f) and 1 <= f <= 5:
                return int(f)
            return np.nan
        except:
            return np.nan
    
    df['satisfaction_score'] = df['satisfaction_score'].apply(clean_satisfaction)
    # Keep rows even if satisfaction_score is missing
    
    # R10: Map churned
    churn_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1, 'churned': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0, 'active': 0
    }
    def map_churned(val):
        if pd.isna(val):
            return None
        return churn_map.get(str(val).lower())
    
    df['churned'] = df['churned'].apply(map_churned)
    df = df[df['churned'].notna()]
    
    # R11: Calculate lifetime_value
    df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)
    
    # R12: Sort and select columns
    df.sort_values('customer_id', inplace=True)
    cols = ['customer_id', 'signup_date', 'plan', 'contract_type', 'monthly_fee', 
            'tenure_months', 'support_tickets', 'satisfaction_score', 'churned', 'lifetime_value']
    df = df[cols]
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(cleaned_path, index=False)
    
    # Write cleaning summary
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()