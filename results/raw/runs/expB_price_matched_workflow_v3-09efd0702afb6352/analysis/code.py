import os
import json
import pandas as pd
import numpy as np

# Define paths
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Read cleaned data
df = pd.read_csv(input_path)

# Initialize results dictionary
results = {}

# --- q1: Overall aggregation ---
results['customer_count'] = len(df)
results['churn_rate_pct'] = (df['churned'].mean() * 100)
results['avg_monthly_fee'] = df['monthly_fee'].mean()

# --- q2: Churn by plan ---
plan_groups = df.groupby('plan')['churned'].mean() * 100
results['churn_rate_basic_pct'] = plan_groups.get('Basic', 0.0)
results['churn_rate_standard_pct'] = plan_groups.get('Standard', 0.0)
results['churn_rate_premium_pct'] = plan_groups.get('Premium', 0.0)

# --- q3: Churn by signup cohort ---
df['signup_year'] = pd.to_datetime(df['signup_date']).dt.year
cohort_groups = df.groupby('signup_year')['churned'].mean() * 100
for year in [2021, 2022, 2023, 2024]:
    results[f'churn_rate_cohort_{year}_pct'] = cohort_groups.get(year, 0.0)

# --- q4: Contract effect ---
contract_groups = df.groupby('contract_type')['churned'].mean() * 100
churn_monthly = contract_groups.get('Monthly', 0.0)
churn_annual = contract_groups.get('Annual', 0.0)
results['churn_rate_monthly_pct'] = churn_monthly
results['churn_rate_annual_pct'] = churn_annual
if churn_annual != 0:
    results['churn_monthly_vs_annual_change_pct'] = ((churn_monthly - churn_annual) / churn_annual) * 100
else:
    results['churn_monthly_vs_annual_change_pct'] = 0.0

# --- q5: At-risk segment ---
at_risk_filter = (df['support_tickets'] >= 5) & (df['satisfaction_score'].notna()) & (df['satisfaction_score'] <= 2)
at_risk_df = df[at_risk_filter]
results['at_risk_customer_count'] = len(at_risk_df)
if len(at_risk_df) > 0:
    results['at_risk_churn_rate_pct'] = at_risk_df['churned'].mean() * 100
else:
    results['at_risk_churn_rate_pct'] = 0.0

# --- q6: Tenure and satisfaction summary ---
results['tenure_mean'] = df['tenure_months'].mean()
results['tenure_median'] = df['tenure_months'].median()
results['tenure_std'] = df['tenure_months'].std(ddof=1)

satisfaction_valid = df['satisfaction_score'].dropna()
results['satisfaction_mean'] = satisfaction_valid.mean()
results['satisfaction_missing_count'] = df['satisfaction_score'].isna().sum()

# --- q7: Lifetime value by plan ---
ltv_groups = df.groupby('plan')['lifetime_value'].mean()
ltv_basic = ltv_groups.get('Basic', 0.0)
ltv_standard = ltv_groups.get('Standard', 0.0)
ltv_premium = ltv_groups.get('Premium', 0.0)
results['ltv_basic'] = ltv_basic
results['ltv_standard'] = ltv_standard
results['ltv_premium'] = ltv_premium

if ltv_basic != 0:
    results['premium_vs_basic_ltv_change_pct'] = ((ltv_premium - ltv_basic) / ltv_basic) * 100
else:
    results['premium_vs_basic_ltv_change_pct'] = 0.0

# Write results to JSON
with open(output_path, 'w') as f:
    json.dump(results, f)
