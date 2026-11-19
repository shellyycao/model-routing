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
    
    # Strip whitespace from all columns
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    
    # Define missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    df = df.replace(missing_vals, np.nan)
    
    # R2: Remove duplicates based on customer_id, keep first occurrence
    df = df.drop_duplicates(subset='customer_id', keep='first')
    
    # R3: Parse signup_date
    def parse_date(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip()
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
        return np.nan
    
    df['signup_date'] = df['signup_date'].apply(parse_date)
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
    df['plan'] = df['plan'].str.lower().str.strip().map(plan_map)
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
    df['contract_type'] = df['contract_type'].str.lower().str.strip().map(contract_map)
    df = df.dropna(subset=['contract_type'])
    
    # R6: Clean monthly_fee
    df['monthly_fee'] = df['monthly_fee'].str.replace('$', '', regex=False).str.replace('USD', '', regex=False).str.replace(',', '', regex=False).str.strip()
    df['monthly_fee'] = pd.to_numeric(df['monthly_fee'], errors='coerce')
    df = df.dropna(subset=['monthly_fee'])
    df = df[(df['monthly_fee'] > 0) & (df['monthly_fee'] <= 500)]
    
    # R7: Clean tenure_months
    df['tenure_months'] = df['tenure_months'].str.replace(r'\s*months?\s*$', '', case=False, regex=True).str.strip()
    df['tenure_months'] = pd.to_numeric(df['tenure_months'], errors='coerce')
    df = df.dropna(subset=['tenure_months'])
    df['tenure_months'] = df['tenure_months'].astype(float)
    df = df[(df['tenure_months'] >= 0) & (df['tenure_months'] <= 120) & (df['tenure_months'].mod(1) == 0)]
    df['tenure_months'] = df['tenure_months'].astype(int)
    
    # R8: Clean support_tickets
    df['support_tickets'] = pd.to_numeric(df['support_tickets'], errors='coerce').fillna(0)
    df['support_tickets'] = df['support_tickets'].astype(float)
    df = df[(df['support_tickets'] >= 0) & (df['support_tickets'] <= 100) & (df['support_tickets'].mod(1) == 0)]
    df['support_tickets'] = df['support_tickets'].astype(int)
    
    # R9: Clean satisfaction_score
    df['satisfaction_score'] = pd.to_numeric(df['satisfaction_score'], errors='coerce')
    df['satisfaction_score'] = df['satisfaction_score'].astype(float)
    mask = (
        df['satisfaction_score'].isna() |
        (df['satisfaction_score'] < 1) | (df['satisfaction_score'] > 5) |
        (df['satisfaction_score'].mod(1) != 0)
    )
    df.loc[mask, 'satisfaction_score'] = np.nan
    df['satisfaction_score'] = df['satisfaction_score'].astype('Int64')
    
    # R10: Clean churned
    churn_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1, 'churned': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0, 'active': 0
    }
    df['churned'] = df['churned'].str.lower().str.strip().map(churn_map)
    df = df.dropna(subset=['churned'])
    df['churned'] = df['churned'].astype(int)
    
    # R11: Calculate lifetime_value
    df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)
    
    # R12: Sort and select columns
    df = df.sort_values('customer_id')
    cols = ['customer_id', 'signup_date', 'plan', 'contract_type', 'monthly_fee', 
            'tenure_months', 'support_tickets', 'satisfaction_score', 'churned', 'lifetime_value']
    df = df[cols]
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    df.to_csv(os.path.join(output_dir, "cleaned.csv"), index=False, na_rep='')
    
    # Write cleaning summary
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows
    }
    with open(os.path.join(output_dir, "cleaning_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()