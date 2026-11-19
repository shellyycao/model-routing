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
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    
    # R1: Read as text, strip whitespace, treat specific values as missing
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    
    raw_rows = len(df)
    
    # Strip whitespace from all columns and values
    df.columns = df.columns.str.strip()
    for col in df.columns:
        df[col] = df[col].str.strip()
    
    # Define missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    def is_missing(val):
        if pd.isna(val):
            return True
        return str(val).strip().lower() in [m.lower() for m in missing_vals]
    
    # Apply missing value standardization (replace with NaN for easier handling)
    for col in df.columns:
        df[col] = df[col].apply(lambda x: np.nan if is_missing(x) else x)
    
    # R2: Remove duplicates based on customer_id (keep first)
    before_r2 = len(df)
    df = df.drop_duplicates(subset=['customer_id'], keep='first')
    r2_removed = before_r2 - len(df)
    
    # R3: signup_date parsing
    def parse_signup_date(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        
        # Try YYYY-MM-DD
        try:
            return datetime.strptime(val, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            pass
        
        # Try MM/DD/YYYY
        try:
            return datetime.strptime(val, '%m/%d/%Y').strftime('%Y-%m-%d')
        except ValueError:
            pass
        
        # Try DD-Mon-YYYY (e.g., 05-Mar-2024)
        try:
            return datetime.strptime(val, '%d-%b-%Y').strftime('%Y-%m-%d')
        except ValueError:
            pass
        
        # Try YYYY/MM/DD
        try:
            return datetime.strptime(val, '%Y/%m/%d').strftime('%Y-%m-%d')
        except ValueError:
            pass
        
        # Try 'Month D, YYYY' (e.g., March 5, 2024)
        try:
            return datetime.strptime(val, '%B %d, %Y').strftime('%Y-%m-%d')
        except ValueError:
            pass
        
        return None
    
    before_r3 = len(df)
    df['signup_date'] = df['signup_date'].apply(parse_signup_date)
    df = df[df['signup_date'].notna()]
    r3_removed = before_r3 - len(df)
    
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
    
    def map_plan(val):
        if pd.isna(val):
            return None
        val_lower = str(val).strip().lower()
        return plan_map.get(val_lower)
    
    before_r4 = len(df)
    df['plan'] = df['plan'].apply(map_plan)
    df = df[df['plan'].notna()]
    r4_removed = before_r4 - len(df)
    
    # R5: contract_type mapping
    contract_map = {
        'monthly': 'Monthly',
        'month-to-month': 'Monthly',
        'm2m': 'Monthly',
        'annual': 'Annual',
        'yearly': 'Annual',
        '1 year': 'Annual'
    }
    
    def map_contract(val):
        if pd.isna(val):
            return None
        val_lower = str(val).strip().lower()
        return contract_map.get(val_lower)
    
    before_r5 = len(df)
    df['contract_type'] = df['contract_type'].apply(map_contract)
    df = df[df['contract_type'].notna()]
    r5_removed = before_r5 - len(df)
    
    # R6: monthly_fee
    def parse_monthly_fee(val):
        if pd.isna(val):
            return None
        val = str(val)
        # Remove $, USD, commas and surrounding spaces
        val = re.sub(r'\$|USD|,', '', val, flags=re.IGNORECASE).strip()
        try:
            num = float(val)
            return num
        except ValueError:
            return None
    
    before_r6 = len(df)
    df['monthly_fee'] = df['monthly_fee'].apply(parse_monthly_fee)
    df = df[df['monthly_fee'].notna()]
    df = df[(df['monthly_fee'] > 0) & (df['monthly_fee'] <= 500)]
    r6_removed = before_r6 - len(df)
    
    # R7: tenure_months
    def parse_tenure(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        # Remove trailing 'months' or 'month' case-insensitive
        val = re.sub(r'\s*months?\s*$', '', val, flags=re.IGNORECASE).strip()
        try:
            num = float(val)
            if num == int(num):
                return int(num)
            return None
        except ValueError:
            return None
    
    before_r7 = len(df)
    df['tenure_months'] = df['tenure_months'].apply(parse_tenure)
    df = df[df['tenure_months'].notna()]
    df = df[(df['tenure_months'] >= 0) & (df['tenure_months'] <= 120)]
    r7_removed = before_r7 - len(df)
    
    # R8: support_tickets
    def parse_tickets(val):
        if pd.isna(val):
            return 0
        val = str(val).strip()
        try:
            num = float(val)
            if num == int(num):
                return int(num)
            return None
        except ValueError:
            return None
    
    before_r8 = len(df)
    df['support_tickets'] = df['support_tickets'].apply(parse_tickets)
    df = df[df['support_tickets'].notna()]
    df = df[(df['support_tickets'] >= 0) & (df['support_tickets'] <= 100)]
    r8_removed = before_r8 - len(df)
    
    # R9: satisfaction_score
    def parse_satisfaction(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip()
        try:
            num = float(val)
            if num == int(num):
                num_int = int(num)
                if 1 <= num_int <= 5:
                    return num_int
            return np.nan
        except ValueError:
            return np.nan
    
    df['satisfaction_score'] = df['satisfaction_score'].apply(parse_satisfaction)
    # No rows dropped for R9
    
    # R10: churned
    churn_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1, 'churned': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0, 'active': 0
    }
    
    def map_churned(val):
        if pd.isna(val):
            return None
        val_lower = str(val).strip().lower()
        return churn_map.get(val_lower)
    
    before_r10 = len(df)
    df['churned'] = df['churned'].apply(map_churned)
    df = df[df['churned'].notna()]
    r10_removed = before_r10 - len(df)
    
    # R11: lifetime_value
    df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)
    
    # R12: Sort and output
    df = df.sort_values(by='customer_id', ascending=True)
    
    # Select columns in order
    cols = ['customer_id', 'signup_date', 'plan', 'contract_type', 'monthly_fee', 
            'tenure_months', 'support_tickets', 'satisfaction_score', 'churned', 'lifetime_value']
    df = df[cols]
    
    cleaned_rows = len(df)
    
    # Write CSV
    df.to_csv(cleaned_path, index=False)
    
    # Write summary JSON
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'r2_duplicates_removed': r2_removed,
        'r3_signup_date_invalid': r3_removed,
        'r4_plan_invalid': r4_removed,
        'r5_contract_type_invalid': r5_removed,
        'r6_monthly_fee_invalid': r6_removed,
        'r7_tenure_months_invalid': r7_removed,
        'r8_support_tickets_invalid': r8_removed,
        'r10_churned_invalid': r10_removed
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()