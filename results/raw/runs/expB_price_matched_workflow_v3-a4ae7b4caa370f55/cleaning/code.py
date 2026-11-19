import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def clean_data():
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    
    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    
    # R1: Read as text, strip whitespace, standardize missing values
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # Strip whitespace from all columns
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    
    # Define missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    def is_missing(val):
        if pd.isna(val):
            return True
        if isinstance(val, str):
            return val.strip().lower() in [m.lower() for m in missing_vals]
        return False
    
    # Apply missing value standardization
    for col in df.columns:
        df[col] = df[col].apply(lambda x: np.nan if is_missing(x) else x)
    
    # R2: Remove duplicates based on customer_id
    rows_before_r2 = len(df)
    df = df.drop_duplicates(subset='customer_id', keep='first')
    r2_removed = rows_before_r2 - len(df)
    
    # R3: signup_date parsing
    month_map = {
        'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
        'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
        'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
        'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
    }
    
    def parse_signup_date(val):
        if pd.isna(val) or val == '':
            return np.nan
        val = str(val).strip()
        
        # YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', val):
            try:
                return datetime.strptime(val, '%Y-%m-%d').strftime('%Y-%m-%d')
            except:
                pass
        
        # MM/DD/YYYY
        if re.match(r'^\d{2}/\d{2}/\d{4}$', val):
            try:
                return datetime.strptime(val, '%m/%d/%Y').strftime('%Y-%m-%d')
            except:
                pass
        
        # DD-Mon-YYYY
        match = re.match(r'^(\d{1,2})-([A-Za-z]{3})-(\d{4})$', val)
        if match:
            day, mon, year = match.groups()
            mon_lower = mon.lower()
            if mon_lower in month_map:
                try:
                    return f"{year}-{month_map[mon_lower]:02d}-{int(day):02d}"
                except:
                    pass
        
        # YYYY/MM/DD
        if re.match(r'^\d{4}/\d{2}/\d{2}$', val):
            try:
                return datetime.strptime(val, '%Y/%m/%d').strftime('%Y-%m-%d')
            except:
                pass
        
        # Month D, YYYY
        match = re.match(r'^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})$', val)
        if match:
            mon, day, year = match.groups()
            mon_lower = mon.lower()
            if mon_lower in month_map:
                try:
                    return f"{year}-{month_map[mon_lower]:02d}-{int(day):02d}"
                except:
                    pass
        
        return np.nan
    
    rows_before_r3 = len(df)
    df['signup_date'] = df['signup_date'].apply(parse_signup_date)
    df = df[df['signup_date'].notna()]
    r3_removed = rows_before_r3 - len(df)
    
    # R4: plan mapping
    def map_plan(val):
        if pd.isna(val) or val == '':
            return np.nan
        val_lower = str(val).strip().lower()
        if val_lower in ['basic', 'basic plan']:
            return 'Basic'
        if val_lower in ['std', 'standard', 'standard plan']:
            return 'Standard'
        if val_lower in ['prem', 'premium', 'premium plan']:
            return 'Premium'
        return np.nan
    
    rows_before_r4 = len(df)
    df['plan'] = df['plan'].apply(map_plan)
    df = df[df['plan'].notna()]
    r4_removed = rows_before_r4 - len(df)
    
    # R5: contract_type mapping
    def map_contract(val):
        if pd.isna(val) or val == '':
            return np.nan
        val_lower = str(val).strip().lower()
        if val_lower in ['monthly', 'month-to-month', 'm2m']:
            return 'Monthly'
        if val_lower in ['annual', 'yearly', '1 year']:
            return 'Annual'
        return np.nan
    
    rows_before_r5 = len(df)
    df['contract_type'] = df['contract_type'].apply(map_contract)
    df = df[df['contract_type'].notna()]
    r5_removed = rows_before_r5 - len(df)
    
    # R6: monthly_fee
    def parse_monthly_fee(val):
        if pd.isna(val) or val == '':
            return np.nan
        val = str(val).strip()
        val = val.replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            num = float(val)
            if num <= 0 or num > 500:
                return np.nan
            return num
        except:
            return np.nan
    
    rows_before_r6 = len(df)
    df['monthly_fee'] = df['monthly_fee'].apply(parse_monthly_fee)
    df = df[df['monthly_fee'].notna()]
    r6_removed = rows_before_r6 - len(df)
    
    # R7: tenure_months
    def parse_tenure(val):
        if pd.isna(val) or val == '':
            return np.nan
        val = str(val).strip()
        val = re.sub(r'\s*months?\s*$', '', val, flags=re.IGNORECASE).strip()
        try:
            num = float(val)
            if not num.is_integer() or num < 0 or num > 120:
                return np.nan
            return int(num)
        except:
            return np.nan
    
    rows_before_r7 = len(df)
    df['tenure_months'] = df['tenure_months'].apply(parse_tenure)
    df = df[df['tenure_months'].notna()]
    r7_removed = rows_before_r7 - len(df)
    
    # R8: support_tickets
    def parse_tickets(val):
        if pd.isna(val) or val == '':
            return 0
        val = str(val).strip()
        try:
            num = float(val)
            if not num.is_integer() or num < 0 or num > 100:
                return np.nan
            return int(num)
        except:
            return np.nan
    
    rows_before_r8 = len(df)
    df['support_tickets'] = df['support_tickets'].apply(parse_tickets)
    df = df[df['support_tickets'].notna()]
    r8_removed = rows_before_r8 - len(df)
    
    # R9: satisfaction_score
    def parse_satisfaction(val):
        if pd.isna(val) or val == '':
            return np.nan
        val = str(val).strip()
        try:
            num = float(val)
            if not num.is_integer() or num < 1 or num > 5:
                return np.nan
            return int(num)
        except:
            return np.nan
    
    df['satisfaction_score'] = df['satisfaction_score'].apply(parse_satisfaction)
    
    # R10: churned
    def map_churned(val):
        if pd.isna(val) or val == '':
            return np.nan
        val_lower = str(val).strip().lower()
        if val_lower in ['yes', 'y', 'true', '1', 'churned']:
            return 1
        if val_lower in ['no', 'n', 'false', '0', 'active']:
            return 0
        return np.nan
    
    rows_before_r10 = len(df)
    df['churned'] = df['churned'].apply(map_churned)
    df = df[df['churned'].notna()]
    r10_removed = rows_before_r10 - len(df)
    
    # R11: lifetime_value
    df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)
    
    # R12: Sort and output
    df = df.sort_values('customer_id')
    
    # Convert churned to int
    df['churned'] = df['churned'].astype(int)
    
    # Select columns in order
    cols = ['customer_id', 'signup_date', 'plan', 'contract_type', 'monthly_fee', 
            'tenure_months', 'support_tickets', 'satisfaction_score', 'churned', 'lifetime_value']
    df = df[cols]
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False)
    
    # Write summary
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed': r2_removed,
        'invalid_signup_date': r3_removed,
        'invalid_plan': r4_removed,
        'invalid_contract_type': r5_removed,
        'invalid_monthly_fee': r6_removed,
        'invalid_tenure_months': r7_removed,
        'invalid_support_tickets': r8_removed,
        'invalid_churned': r10_removed
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()
