import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ['NA', 'N/A', 'null', 'None', '-']
DATE_FORMATS = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
PLAN_MAPPING = {'Basic Plan': 'Basic', 'Std': 'Standard', 'Standard Plan': 'Standard', 'Prem': 'Premium', 'Premium Plan': 'Premium'}
CONTRACT_MAPPING = {'Monthly': 'Monthly', 'Month-to-month': 'Monthly', 'M2M': 'Monthly', 'Annual': 'Annual', 'Yearly': 'Annual', '1 Year': 'Annual'}

# Read input file
input_file = os.path.join(os.environ['INPUT_DIR'], 'raw.csv')
df = pd.read_csv(input_file, dtype=str)

# R1: Strip whitespace and treat specified values as missing
df = df.applymap(lambda x: x.strip() if pd.notna(x) else x)
df.replace(to_replace=MISSING_VALUES, value=np.nan, inplace=True, regex=True)

# R2: Remove duplicate records
df.drop_duplicates(subset=['customer_id'], keep='first', inplace=True)

# R3: Parse signup_date
def parse_date(date_str):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return np.nan
df['signup_date'] = df['signup_date'].apply(parse_date)
df.dropna(subset=['signup_date'], inplace=True)

# R4: Map and filter plan
df['plan'] = df['plan'].str.strip().str.lower().map(lambda x: PLAN_MAPPING.get(x, x)).str.capitalize()
df = df[df['plan'].isin(['Basic', 'Standard', 'Premium']) & df['plan'].notna()]

# R5: Map and filter contract_type
df['contract_type'] = df['contract_type'].str.strip().str.lower().map(lambda x: CONTRACT_MAPPING.get(x, x)).str.capitalize()
df = df[df['contract_type'].isin(['Monthly', 'Annual']) & df['contract_type'].notna()]

# R6: Clean and filter monthly_fee
df['monthly_fee'] = df['monthly_fee'].str.replace('[$,]', '', regex=True).str.strip().astype(float)
df = df[(df['monthly_fee'] > 0) & (df['monthly_fee'] <= 500)]

# R7: Clean and filter tenure_months
df['tenure_months'] = df['tenure_months'].str.replace(r'(?i)\s*(months?)$', '', regex=True).str.strip().astype(int)
df = df[(df['tenure_months'] >= 0) & (df['tenure_months'] <= 120)]

# R8: Clean and filter support_tickets
df['support_tickets'] = df['support_tickets'].fillna(0).astype(int)
df = df[(df['support_tickets'] >= 0) & (df['support_tickets'] <= 100)]

# R9: Clean and filter satisfaction_score
df['satisfaction_score'] = pd.to_numeric(df['satisfaction_score'], errors='coerce')
df.loc[(df['satisfaction_score'] < 1) | (df['satisfaction_score'] > 5),'satisfaction_score'] = np.nan
df['satisfaction_score'] = df['satisfaction_score'].astype('Int64')

# R10: Map and filter churned
churn_mapping = {'Yes': 1, 'Y': 1, 'True': 1, '1': 1, 'Churned': 1, 'No': 0, 'N': 0, 'False': 0, '0': 0, 'Active': 0}
df['churned'] = df['churned'].str.strip().str.lower().map(churn_mapping)
df = df[df['churned'].notna()]

# R11: Add lifetime_value
df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)

# R12: Select and order columns, sort by customer_id
df = df[['customer_id','signup_date', 'plan', 'contract_type','monthly_fee', 'tenure_months', 'support_tickets', 'satisfaction_score', 'churned', 'lifetime_value']]
df.sort_values(by='customer_id', inplace=True)

# Write cleaned data to CSV
output_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaned.csv')
df.to_csv(output_file, index=False)

# Write cleaning summary
cleaning_summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df)
}
with open(os.path.join(os.environ['OUTPUT_DIR'], 'cleaning_summary.json'), 'w') as f:
    import json
    json.dump(cleaning_summary, f)

# Output filename
output_filename = 'cleaned.csv'

# Cleaning logic explanation
cleaning_logic = 'The script performs the following cleaning steps: 1) Reads the raw CSV and strips whitespace from all values. 2) Treats specified values as missing. 3) Removes duplicate records based on customer_id. 4) Parses signup_date using specified formats and drops rows with invalid dates. 5) Maps and filters plan and contract_type. 6) Cleans and filters monthly_fee, tenure_months, support_tickets, and satisfaction_score. 7) Maps and filters churned. 8) Adds lifetime_value as the product of monthly_fee and tenure_months. 9) Selects and orders columns, sorts by customer_id, and writes the cleaned data to a CSV file. 10) Writes a cleaning summary JSON file with the number of raw and cleaned rows.'