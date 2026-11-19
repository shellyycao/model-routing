import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    # R1: Read raw CSV as text, strip whitespace, handle missing values
    df = pd.read_csv(os.path.join(input_dir, "raw.csv"), dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # Strip leading/trailing whitespace from all values
    for col in df.columns:
        df[col] = df[col].str.strip()
    
    # Define missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    # Replace missing values with NaN (case-insensitive)
    for col in df.columns:
        df[col] = df[col].apply(lambda x: np.nan if str(x).lower() in [v.lower() for v in missing_vals] else x)
    
    # R2: Remove duplicates (keep first occurrence)
    before_dedup = len(df)
    df = df.drop_duplicates(subset='customer_id', keep='first')
    duplicates_removed = before_dedup - len(df)
    
    # R3: Parse signup_date
    def parse_signup_date(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        
        # Try YYYY-MM-DD
        try:
            return datetime.strptime(val, '%Y-%m-%d').strftime('%Y-%m-%d')
        except:
            pass
        
        # Try MM/DD/YYYY
        try:
            return datetime.strptime(val, '%m/%d/%Y').strftime('%Y-%m-%d')
        except:
            pass
        
        # Try DD-Mon-YYYY
        try:
            return datetime.strptime(val, '%d-%b-%Y').strftime('%Y-%m-%d')
        except:
            pass
        
        # Try YYYY/MM/DD
        try:
            return datetime.strptime(val, '%Y/%m/%d').strftime('%Y-%m-%d')
        except:
            pass
        
        # Try 'Month D, YYYY'
        try:
            return datetime.strptime(val, '%B %d, %Y').strftime('%Y-%m-%d')
        except:
            pass
        
        return None
    
    df['signup_date'] = df['signup_date'].apply(parse_signup_date)
    df = df.dropna(subset=['signup_date'])
    
    # R4: Map plan
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
        return plan_map.get(val_lower, None)
    
    df['plan'] = df['plan'].apply(map_plan)
    df = df.dropna(subset=['plan'])
    
    # R5: Map contract_type
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
        return contract_map.get(val_lower, None)
    
    df['contract_type'] = df['contract_type'].apply(map_contract)
    df = df.dropna(subset=['contract_type'])
    
    # R6: Parse monthly_fee
    def parse_monthly_fee(val):
        if pd.isna(val):
            return None
        val = str(val).replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            num = float(val)
            if num <= 0 or num > 500:
                return None
            return num
        except:
            return None
    
    df['monthly_fee'] = df['monthly_fee'].apply(parse_monthly_fee)
    df = df.dropna(subset=['monthly_fee'])
    
    # R7: Parse tenure_months
    def parse_tenure(val):
        if pd.isna(val):
            return None
        val = str(val).lower().replace('months', '').replace('month', '').strip()
        try:
            num = float(val)
            if num != int(num) or num < 0 or num > 120:
                return None
            return int(num)
        except:
            return None
    
    df['tenure_months'] = df['tenure_months'].apply(parse_tenure)
    df = df.dropna(subset=['tenure_months'])
    
    # R8: Parse support_tickets
    def parse_tickets(val):
        if pd.isna(val):
            return 0
        try:
            num = float(val)
            if num != int(num) or num < 0 or num > 100:
                return None
            return int(num)
        except:
            return None
    
    df['support_tickets'] = df['support_tickets'].apply(parse_tickets)
    df = df.dropna(subset=['support_tickets'])
    
    # R9: Parse satisfaction_score
    def parse_satisfaction(val):
        if pd.isna(val):
            return np.nan
        try:
            num = float(val)
            if num != int(num) or num < 1 or num > 5:
                return np.nan
            return int(num)
        except:
            return np.nan
    
    df['satisfaction_score'] = df['satisfaction_score'].apply(parse_satisfaction)
    # Keep rows even if satisfaction_score is missing
    
    # R10: Map churned
    churned_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1, 'churned': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0, 'active': 0
    }
    
    def map_churned(val):
        if pd.isna(val):
            return None
        val_lower = str(val).strip().lower()
        return churned_map.get(val_lower, None)
    
    df['churned'] = df['churned'].apply(map_churned)
    df = df.dropna(subset=['churned'])
    df['churned'] = df['churned'].astype(int)
    
    # R11: Calculate lifetime_value
    df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)
    
    # R12: Sort by customer_id and select columns
    df = df.sort_values('customer_id')
    
    # Convert satisfaction_score to nullable Int64 for proper CSV output
    df['satisfaction_score'] = df['satisfaction_score'].astype('Int64')
    
    # Select columns in order
    columns = ['customer_id', 'signup_date', 'plan', 'contract_type', 'monthly_fee', 
               'tenure_months', 'support_tickets', 'satisfaction_score', 'churned', 'lifetime_value']
    df = df[columns]
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    df.to_csv(os.path.join(output_dir, 'cleaned.csv'), index=False)
    
    # Write cleaning summary
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed': duplicates_removed
    }
    
    with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()
