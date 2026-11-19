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
    
    summary = {}
    
    # R1: Read as text, strip whitespace, handle missing values
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    summary['raw_rows'] = len(df)
    
    # Strip whitespace from all columns
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    
    # Define missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    df = df.replace(missing_vals, np.nan)
    
    # R2: Remove duplicates based on customer_id
    before_dedup = len(df)
    df = df.drop_duplicates(subset='customer_id', keep='first')
    summary['duplicates_removed'] = before_dedup - len(df)
    
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
    before_r3 = len(df)
    df = df.dropna(subset=['signup_date'])
    summary['r3_invalid_dates_dropped'] = before_r3 - len(df)
    
    # R4: Clean plan
    plan_map = {
        'basic': 'Basic', 'basic plan': 'Basic',
        'standard': 'Standard', 'std': 'Standard', 'standard plan': 'Standard',
        'premium': 'Premium', 'prem': 'Premium', 'premium plan': 'Premium'
    }
    df['plan'] = df['plan'].str.lower().str.strip().map(plan_map)
    before_r4 = len(df)
    df = df.dropna(subset=['plan'])
    summary['r4_invalid_plans_dropped'] = before_r4 - len(df)
    
    # R5: Clean contract_type
    contract_map = {
        'monthly': 'Monthly', 'month-to-month': 'Monthly', 'm2m': 'Monthly',
        'annual': 'Annual', 'yearly': 'Annual', '1 year': 'Annual'
    }
    df['contract_type'] = df['contract_type'].str.lower().str.strip().map(contract_map)
    before_r5 = len(df)
    df = df.dropna(subset=['contract_type'])
    summary['r5_invalid_contracts_dropped'] = before_r5 - len(df)
    
    # R6: Clean monthly_fee
    df['monthly_fee'] = df['monthly_fee'].astype(str).str.replace(r'[$,]', '', regex=True).str.replace('USD', '').str.strip()
    df['monthly_fee'] = pd.to_numeric(df['monthly_fee'], errors='coerce')
    before_r6 = len(df)
    df = df.dropna(subset=['monthly_fee'])
    df = df[df['monthly_fee'].between(0.01, 500)]
    summary['r6_invalid_fees_dropped'] = before_r6 - len(df)
    
    # R7: Clean tenure_months
    df['tenure_months'] = df['tenure_months'].astype(str).str.replace(r'\s*months?\s*$', '', case=False, regex=True).str.strip()
    df['tenure_months'] = pd.to_numeric(df['tenure_months'], errors='coerce')
    before_r7 = len(df)
    df = df.dropna(subset=['tenure_months'])
    # Check whole number
    df = df[df['tenure_months'] == df['tenure_months'].round()]
    df = df[df['tenure_months'].between(0, 120)]
    df['tenure_months'] = df['tenure_months'].astype(int)
    summary['r7_invalid_tenure_dropped'] = before_r7 - len(df)
    
    # R8: Clean support_tickets
    df['support_tickets'] = pd.to_numeric(df['support_tickets'], errors='coerce').fillna(0)
    before_r8 = len(df)
    # Check whole number
    df = df[df['support_tickets'] == df['support_tickets'].round()]
    df = df[df['support_tickets'].between(0, 100)]
    df['support_tickets'] = df['support_tickets'].astype(int)
    summary['r8_invalid_tickets_dropped'] = before_r8 - len(df)
    
    # R9: Clean satisfaction_score
    df['satisfaction_score'] = pd.to_numeric(df['satisfaction_score'], errors='coerce')
    # Check whole number and range
    mask = (df['satisfaction_score'] == df['satisfaction_score'].round()) & df['satisfaction_score'].between(1, 5)
    df['satisfaction_score'] = df['satisfaction_score'].where(mask, np.nan)
    df['satisfaction_score'] = df['satisfaction_score'].astype('Int64') # Nullable integer
    
    # R10: Clean churned
    churn_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1, 'churned': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0, 'active': 0
    }
    df['churned'] = df['churned'].astype(str).str.lower().str.strip().map(churn_map)
    before_r10 = len(df)
    df = df.dropna(subset=['churned'])
    df['churned'] = df['churned'].astype(int)
    summary['r10_invalid_churned_dropped'] = before_r10 - len(df)
    
    # R11: Calculate lifetime_value
    df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)
    
    # R12: Sort and select columns
    df = df.sort_values('customer_id')
    
    # Convert satisfaction_score to object to handle empty cells in CSV output
    df['satisfaction_score'] = df['satisfaction_score'].astype(object).where(df['satisfaction_score'].notna(), '')
    
    cols = ['customer_id', 'signup_date', 'plan', 'contract_type', 'monthly_fee', 
            'tenure_months', 'support_tickets', 'satisfaction_score', 'churned', 'lifetime_value']
    df = df[cols]
    
    summary['cleaned_rows'] = len(df)
    
    df.to_csv(cleaned_path, index=False)
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()