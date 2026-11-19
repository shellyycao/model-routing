import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]
PLAN_MAPPING = {'Basic Plan': 'Basic', 'Std': 'Standard', 'Standard Plan': 'Standard', 'Prem': 'Premium', 'Premium Plan': 'Premium'}
CONTRACT_MAPPING = {'Monthly': 'Monthly', 'Month-to-month': 'Monthly', 'M2M': 'Monthly', 'Annual': 'Annual', 'Yearly': 'Annual', '1 Year': 'Annual'}
CHURNED_MAPPING = {'Yes': 1, 'Y': 1, 'True': 1, '1': 1, 'Churned': 1, 'No': 0, 'N': 0, 'False': 0, '0': 0, 'Active': 0}

# Read input file
input_file = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
df = pd.read_csv(input_file, dtype=str)

# R1: Strip whitespace and treat specified values as missing
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
df.replace(MISSING_VALUES, np.nan, inplace=True)

# R2: Remove duplicate records
df.drop_duplicates(subset=['customer_id'], keep='first', inplace=True)

# R3: Parse signup_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
df['signup_date'] = df['signup_date'].apply(lambda x: pd.to_datetime(x, format=date_formats, errors='coerce'))
df.dropna(subset=['signup_date'], inplace=True)
df['signup_date'] = df['signup_date'].dt.strftime('%Y-%m-%d')

# R4: Map and clean plan
df['plan'] = df['plan'].str.lower().map(PLAN_MAPPING).str.capitalize()
df.dropna(subset=['plan'], inplace=True)

# R5: Map and clean contract_type
df['contract_type'] = df['contract_type'].str.lower().map(CONTRACT_MAPPING).str.capitalize()
df.dropna(subset=['contract_type'], inplace=True)

# R6: Clean monthly_fee
df['monthly_fee'] = df['monthly_fee'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).astype(float)
df = df[(df['monthly_fee'] > 0) & (df['monthly_fee'] <= 500)]

# R7: Clean tenure_months
df['tenure_months'] = df['tenure_months'].replace({' months': '', ' month': ''}, regex=True).astype(int)
df = df[(df['tenure_months'] >= 0) & (df['tenure_months'] <= 120)]

# R8: Clean support_tickets
df['support_tickets'] = df['support_tickets'].fillna(0).astype(int)
df = df[(df['support_tickets'] >= 0) & (df['support_tickets'] <= 100)]

# R9: Clean satisfaction_score
df['satisfaction_score'] = pd.to_numeric(df['satisfaction_score'], errors='coerce')
df.loc[(df['satisfaction_score'] < 1) | (df['satisfaction_score'] > 5),'satisfaction_score'] = np.nan
df['satisfaction_score'] = df['satisfaction_score'].astype('Int64')

# R10: Map and clean churned
df['churned'] = df['churned'].str.lower().map(CHURNED_MAPPING).astype(int)
df.dropna(subset=['churned'], inplace=True)

# R11: Add lifetime_value
df['lifetime_value'] = (df['monthly_fee'] * df['tenure_months']).round(2)

# R12: Select and order columns
output_columns = ['customer_id','signup_date', 'plan', 'contract_type','monthly_fee', 'tenure_months', 'support_tickets', 'satisfaction_score', 'churned', 'lifetime_value']
df = df[output_columns].sort_values(by='customer_id')

# Write cleaned CSV
output_file = os.path.join(os.environ["OUTPUT_DIR"], "cleaned.csv")
df.to_csv(output_file, index=False)

# Write cleaning summary
cleaning_summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'dropped_duplicates': len(df) - len(df.drop_duplicates(subset=['customer_id'], keep=False)),
    'invalid_signup_date': len(pd.read_csv(input_file)) - len(df.dropna(subset=['signup_date']))
}
with open(os.path.join(os.environ["OUTPUT_DIR"], "cleaning_summary.json"), 'w') as f:
    f.write(json.dumps(cleaning_summary, indent=2))

output_filename = "cleaned.csv"
cleaning_logic = "The script reads the raw CSV, strips whitespace, treats specified values as missing, removes duplicates, parses and cleans dates, maps and cleans categorical variables, cleans numerical variables, calculates lifetime value, selects and orders columns, and writes the cleaned CSV and a cleaning summary."