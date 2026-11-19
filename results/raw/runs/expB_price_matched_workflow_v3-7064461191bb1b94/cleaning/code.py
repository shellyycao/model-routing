import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    # R1: Read raw CSV as text, strip whitespace, handle missing values
    df = pd.read_csv(
        os.path.join(input_dir, "raw.csv"),
        dtype=str,
        keep_default_na=False
    )
    
    raw_rows = len(df)
    
    # Strip leading/trailing whitespace from all values
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    
    # Define missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    # Replace missing values with NaN (case-insensitive)
    for col in df.columns:
        df[col] = df[col].apply(lambda x: np.nan if x in missing_vals else x)
    
    # R2: Remove duplicates based on customer_id, keep first occurrence
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
    
    df['signup_date'] = df['signup_date'].apply(parse_signup_date)
    before_r3 = len(df)
    df = df.dropna(subset=['signup_date'])
    r3_dropped = before_r3 - len(df)
    
    # R4: Map plan values
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
    
    df['plan'] = df['plan'].apply(map_plan)
    before_r4 = len(df)
    df = df.dropna(subset=['plan'])
    r4_dropped = before_r4 - len(df)
    
    # R5: Map contract_type values
    def map_contract_type(val):
        if pd.isna(val):
            return None
        val_lower = str(val).strip().lower()
        
        if val_lower in ['monthly', 'month-to-month', 'm2m']:
            return 'Monthly'
        elif val_lower in ['annual', 'yearly', '1 year']:
            return 'Annual'
        return None
    
    df['contract_type'] = df['contract_type'].apply(map_contract_type)
    before_r5 = len(df)
    df = df.dropna(subset=['contract_type'])
    r5_dropped = before_r5 - len(df)
    
    # R6: Parse monthly_fee
    def parse_monthly_fee(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        # Remove $, USD, and commas
        val = val.replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            num = float(val)
            if num <= 0 or num > 500:
                return None
            return num
        except ValueError:
            return None
    
    df['monthly_fee'] = df['monthly_fee'].apply(parse_monthly_fee)
    before_r6 = len(df)
    df = df.dropna(subset=['monthly_fee'])
    r6_dropped = before_r6 - len(df)
    
    # R7: Parse tenure_months
    def parse_tenure_months(val):
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
        except ValueError:
            return None
    
    df['tenure_months'] = df['tenure_months'].apply(parse_tenure_months)
    before_r7 = len(df)
    df = df.dropna(subset=['tenure_months'])
    r7_dropped = before_r7 - len(df)
    
    # R8: Parse support_tickets (missing = 0)
    def parse_support_tickets(val):
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
        except ValueError:
            return None
    
    df['support_tickets'] = df['support_tickets'].apply(parse_support_tickets)
    before_r8 = len(df)
    df = df.dropna(subset=['support_tickets'])
    r8_dropped = before_r8 - len(df)
    
    # R9: Parse satisfaction_score (keep row even if invalid, set to None)
    def parse_satisfaction_score(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        try:
            num = float(val)
            if num != int(num):
                return None
            num = int(num)
            if num < 1 or num > 5:
                return None
            return num
        except ValueError:
            return None
    
    df['satisfaction_score'] = df['satisfaction_score'].apply(parse_satisfaction_score)
    # Note: We don't drop rows for satisfaction_score
    
    # R10: Parse churned
    def parse_churned(val):
        if pd.isna(val):
            return None
        val_lower = str(val).strip().lower()
        
        if val_lower in ['yes', 'y', 'true', '1', 'churned']:
            return 1
        elif val_lower in ['no', 'n', 'false', '0', 'active']:
            return 0
        return None
    
    df['churned'] = df['churned'].apply(parse_churned)
    before_r10 = len(df)
    df = df.dropna(subset=['churned'])
    r10_dropped = before_r10 - len(df)
    
    # R11: Calculate lifetime_value
    df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)
    
    # R12: Select and order columns, sort by customer_id
    columns_order = [
        'customer_id', 'signup_date', 'plan', 'contract_type',
        'monthly_fee', 'tenure_months', 'support_tickets',
        'satisfaction_score', 'churned', 'lifetime_value'
    ]
    df = df[columns_order]
    df = df.sort_values('customer_id')
    
    # Convert types for output
    df['tenure_months'] = df['tenure_months'].astype(int)
    df['support_tickets'] = df['support_tickets'].astype(int)
    df['churned'] = df['churned'].astype(int)
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    df.to_csv(
        os.path.join(output_dir, "cleaned.csv"),
        index=False,
        na_rep=''
    )
    
    # Write cleaning summary JSON
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows,
        "duplicates_removed": duplicates_removed,
        "r3_signup_date_dropped": r3_dropped,
        "r4_plan_dropped": r4_dropped,
        "r5_contract_type_dropped": r5_dropped,
        "r6_monthly_fee_dropped": r6_dropped,
        "r7_tenure_months_dropped": r7_dropped,
        "r8_support_tickets_dropped": r8_dropped,
        "r10_churned_dropped": r10_dropped
    }
    
    with open(os.path.join(output_dir, "cleaning_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()