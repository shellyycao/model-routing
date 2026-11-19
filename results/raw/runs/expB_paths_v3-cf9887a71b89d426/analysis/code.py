import os
import pandas as pd
import numpy as np

# Read the cleaned data
input_file = os.path.join(os.environ['INPUT_DIR'], 'cleaned.csv')
df = pd.read_csv(input_file)

# Analysis
customer_count = len(df)
churn_rate_pct = df['churned'].mean() * 100
avg_monthly_fee = df['monthly_fee'].mean()
churn_rate_basic_pct = df[df['plan'] == 'Basic']['churned'].mean() * 100
churn_rate_standard_pct = df[df['plan'] == 'Standard']['churned'].mean() * 100
churn_rate_premium_pct = df[df['plan'] == 'Premium']['churned'].mean() * 100
churn_rate_cohort_2021_pct = df[df['signup_date'].str.startswith('2021')]['churned'].mean() * 100
churn_rate_cohort_2022_pct = df[df['signup_date'].str.startswith('2022')]['churned'].mean() * 100
churn_rate_cohort_2023_pct = df[df['signup_date'].str.startswith('2023')]['churned'].mean() * 100
churn_rate_cohort_2024_pct = df[df['signup_date'].str.startswith('2024')]['churned'].mean() * 100
churn_rate_monthly_pct = df[df['contract_type'] == 'Monthly']['churned'].mean() * 100
churn_rate_annual_pct = df[df['contract_type'] == 'Annual']['churned'].mean() * 100
churn_monthly_vs_annual_change_pct = (churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct * 100 if churn_rate_annual_pct!= 0 else np.nan
at_risk_df = df[(df['support_tickets'] >= 5) & (df['satisfaction_score'].notna()) & (df['satisfaction_score'] <= 2)]
at_risk_customer_count = len(at_risk_df)
at_risk_churn_rate_pct = at_risk_df['churned'].mean() * 100 if len(at_risk_df) > 0 else 0
tenure_mean = df['tenure_months'].mean()
tenure_median = df['tenure_months'].median()
tenure_std = df['tenure_months'].std()
satisfaction_mean = df['satisfaction_score'].mean()
satisfaction_missing_count = df['satisfaction_score'].isna().sum()
ltv_basic = df[df['plan'] == 'Basic']['lifetime_value'].mean()
ltv_standard = df[df['plan'] == 'Standard']['lifetime_value'].mean()
ltv_premium = df[df['plan'] == 'Premium']['lifetime_value'].mean()
premium_vs_basic_ltv_change_pct = (ltv_premium - ltv_basic) / ltv_basic * 100 if ltv_basic!= 0 else np.nan

# Prepare findings
findings = {
    'customer_count': customer_count,
    'churn_rate_pct': churn_rate_pct,
    'avg_monthly_fee': avg_monthly_fee,
    'churn_rate_basic_pct': churn_rate_basic_pct,
    'churn_rate_standard_pct': churn_rate_standard_pct,
    'churn_rate_premium_pct': churn_rate_premium_pct,
    'churn_rate_cohort_2021_pct': churn_rate_cohort_2021_pct,
    'churn_rate_cohort_2022_pct': churn_rate_cohort_2022_pct,
    'churn_rate_cohort_2023_pct': churn_rate_cohort_2023_pct,
    'churn_rate_cohort_2024_pct': churn_rate_cohort_2024_pct,
    'churn_rate_monthly_pct': churn_rate_monthly_pct,
    'churn_rate_annual_pct': churn_rate_annual_pct,
    'churn_monthly_vs_annual_change_pct': churn_monthly_vs_annual_change_pct,
    'at_risk_customer_count': at_risk_customer_count,
    'at_risk_churn_rate_pct': at_risk_churn_rate_pct,
    'tenure_mean': tenure_mean,
    'tenure_median': tenure_median,
    'tenure_std': tenure_std,
    'satisfaction_mean': satisfaction_mean,
   'satisfaction_missing_count': satisfaction_missing_count,
    'ltv_basic': ltv_basic,
    'ltv_standard': ltv_standard,
    'ltv_premium': ltv_premium,
    'premium_vs_basic_ltv_change_pct': premium_vs_basic_ltv_change_pct
}

# Write findings to JSON
output_file = os.path.join(os.environ['OUTPUT_DIR'], 'findings.json')
with open(output_file, 'w') as f:
    import json
    json.dump(findings, f)

# Expected artifacts
expected_artifacts = ['findings.json']

# Methods description
methods_description = 'This script performs the analysis on the cleaned customer churn data. It calculates various metrics such as overall churn rate, churn rate by plan, signup cohort, and contract type, identifies at-risk customers, summarizes tenure and satisfaction, and computes lifetime value by plan. The results are written to a JSON file named findings.json.'
