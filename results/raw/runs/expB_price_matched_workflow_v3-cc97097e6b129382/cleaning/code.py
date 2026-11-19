import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    
    # R1: Read as text, strip whitespace, handle missing values
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # Strip whitespace from all columns
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    
    # Define missing values
    missing_vals = ['', 'na', 'n/a', 'null', 'none', '-']
    
    def is_missing(val):
        if pd.isna(val):
            return True
        return str(val).strip().lower() in missing_vals
    
    # Replace missing values with NaN for easier handling
    for col in df.columns:
        df[col] = df[col].apply(lambda x: np.nan if is_missing(x) else x)
    
    # R2: Remove duplicates by customer_id, keep first
    before_dedup = len(df)
    df = df.drop_duplicates(subset='customer_id', keep='first')
    duplicates_removed = before_dedup - len(df)
    
    # R3: Parse signup_date
    def parse_date(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        
        # Try YYYY-MM-DD
        try:
            dt = datetime.strptime(val, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
        except:
            pass
        
        # Try MM/DD/YYYY
        try:
            dt = datetime.strptime(val, '%m/%d/%Y')
            return dt.strftime('%Y-%m-%d')
        except:
            pass
        
        # Try DD-Mon-YYYY (e.g., 05-Mar-2024)
        try:
            dt = datetime.strptime(val, '%d-%b-%Y')
            return dt.strftime('%Y-%m-%d')
        except:
            pass
        
        # Try YYYY/MM/DD
        try:
            dt = datetime.strptime(val, '%Y/%m/%d')
            return dt.strftime('%Y-%m-%d')
        except:
            pass
        
        # Try 'Month D, YYYY' (e.g., March 5, 2024)
        try:
            dt = datetime.strptime(val, '%B %d, %Y')
            return dt.strftime('%Y-%m-%d')
        except:
            pass
        
        return None
    
    before_r3 = len(df)
    df['signup_date'] = df['signup_date'].apply(parse_date)
    df = df[df['signup_date'].notna()]
    dropped_r3 = before_r3 - len(df)
    
    # R4: Map plan
    def map_plan(val):
        if pd.isna(val):
            return None
        val_lower = str(val).strip().lower()
        
        if val_lower in ['basic', 'basic plan']:
            return 'Basic'
        elif val_lower in ['standard', 'std', 'standard plan']:
            return 'Standard'
        elif val_lower in ['premium', 'prem', 'premium plan']:
            return 'Premium'
        return None
    
    before_r4 = len(df)
    df['plan'] = df['plan'].apply(map_plan)
    df = df[df['plan'].notna()]
    dropped_r4 = before_r4 - len(df)
    
    # R5: Map contract_type
    def map_contract(val):
        if pd.isna(val):
            return None
        val_lower = str(val).strip().lower()
        
        if val_lower in ['monthly', 'month-to-month', 'm2m']:
            return 'Monthly'
        elif val_lower in ['annual', 'yearly', '1 year']:
            return 'Annual'
        return None
    
    before_r5 = len(df)
    df['contract_type'] = df['contract_type'].apply(map_contract)
    df = df[df['contract_type'].notna()]
    dropped_r5 = before_r5 - len(df)
    
    # R6: Parse monthly_fee
    def parse_fee(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        # Remove $, USD, commas and surrounding spaces
        val = val.replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            num = float(val)
            if num <= 0 or num > 500:
                return None
            return num
        except:
            return None
    
    before_r6 = len(df)
    df['monthly_fee'] = df['monthly_fee'].apply(parse_fee)
    df = df[df['monthly_fee'].notna()]
    dropped_r6 = before_r6 - len(df)
    
    # R7: Parse tenure_months
    def parse_tenure(val):
        if pd.isna(val):
            return None
        val = str(val).strip().lower()
        # Remove trailing 'months' or 'month'
        if val.endswith('months'):
            val = val[:-6].strip()
        elif val.endswith('month'):
            val = val[:-5].strip()
        
        try:
            num = float(val)
            if num != int(num):
                return None
            num = int(num)
            if num < 0 or num > 120:
                return None
            return num
        except:
            return None
    
    before_r7 = len(df)
    df['tenure_months'] = df['tenure_months'].apply(parse_tenure)
    df = df[df['tenure_months'].notna()]
    dropped_r7 = before_r7 - len(df)
    
    # R8: Parse support_tickets (missing = 0)
    def parse_tickets(val):
        if pd.isna(val):
            return 0
        val = str(val).strip()
        try:
            num = float(val)
            if num != int(num):
                return None
            num = int(num)
            if num < 0 or num > 100:
                return None
            return num
        except:
            return None
    
    before_r8 = len(df)
    df['support_tickets'] = df['support_tickets'].apply(parse_tickets)
    df = df[df['support_tickets'].notna()]
    dropped_r8 = before_r8 - len(df)
    
    # R9: Parse satisfaction_score (missing -> keep row, set to empty)
    def parse_satisfaction(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip()
        try:
            num = float(val)
            if num != int(num):
                return np.nan
            num = int(num)
            if num < 1 or num > 5:
                return np.nan
            return num
        except:
            return np.nan
    
    df['satisfaction_score'] = df['satisfaction_score'].apply(parse_satisfaction)
    # No row dropping for R9
    
    # R10: Parse churned
    def map_churned(val):
        if pd.isna(val):
            return None
        val_lower = str(val).strip().lower()
        
        if val_lower in ['yes', 'y', 'true', '1', 'churned']:
            return 1
        elif val_lower in ['no', 'n', 'false', '0', 'active']:
            return 0
        return None
    
    before_r10 = len(df)
    df['churned'] = df['churned'].apply(map_churned)
    df = df[df['churned'].notna()]
    dropped_r10 = before_r10 - len(df)
    
    # R11: Calculate lifetime_value
    df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)
    
    # R12: Sort by customer_id and select columns
    df = df.sort_values('customer_id')
    
    # Convert satisfaction_score to nullable int for output
    # Write empty string for missing values
    
    columns_order = ['customer_id', 'signup_date', 'plan', 'contract_type', 
                     'monthly_fee', 'tenure_months', 'support_tickets', 
                     'satisfaction_score', 'churned', 'lifetime_value']
    
    df = df[columns_order]
    
    # Write cleaned CSV
    # For satisfaction_score, convert NaN to empty string for proper CSV output
    df['satisfaction_score'] = df['satisfaction_score'].apply(lambda x: '' if pd.isna(x) else int(x))
    
    # Convert integers properly
    df['tenure_months'] = df['tenure_months'].astype(int)
    df['support_tickets'] = df['support_tickets'].astype(int)
    df['churned'] = df['churned'].astype(int)
    
    df.to_csv(cleaned_path, index=False)
    
    cleaned_rows = len(df)
    
    # Write cleaning summary
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows,
        "duplicates_removed": duplicates_removed,
        "dropped_invalid_signup_date": dropped_r3,
        "dropped_invalid_plan": dropped_r4,
        "dropped_invalid_contract_type": dropped_r5,
        "dropped_invalid_monthly_fee": dropped_r6,
        "dropped_invalid_tenure_months": dropped_r7,
        "dropped_invalid_support_tickets": dropped_r8,
        "dropped_invalid_churned": dropped_r10
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()