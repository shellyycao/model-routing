import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths from environment variables
    input_dir = os.getenv('INPUT_DIR')
    output_dir = os.getenv('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise EnvironmentError('INPUT_DIR and OUTPUT_DIR must be set')
    cleaned_path = os.path.join(input_dir, 'cleaned.csv')
    findings_path = os.path.join(output_dir, 'findings.json')

    # Load cleaned data
    df = pd.read_csv(
        cleaned_path,
        dtype={'customer_id': str},
        parse_dates=['signup_date'],
        keep_default_na=True,
        na_values=['']
    )

    # Ensure numeric columns are proper dtypes
    numeric_cols = ['monthly_fee', 'tenure_months', 'support_tickets', 'satisfaction_score', 'churned', 'lifetime_value']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # ---------- q1: overall metrics ----------
    customer_count = int(len(df))
    churn_rate_pct = (df['churned'].sum() / customer_count) * 100 if customer_count else 0.0
    avg_monthly_fee = df['monthly_fee'].mean()

    # ---------- q2: churn by plan ----------
    def churn_rate_by_plan(plan_name):
        subset = df[df['plan'] == plan_name]
        if len(subset) == 0:
            return 0.0
        return (subset['churned'].sum() / len(subset)) * 100

    churn_rate_basic_pct = churn_rate_by_plan('Basic')
    churn_rate_standard_pct = churn_rate_by_plan('Standard')
    churn_rate_premium_pct = churn_rate_by_plan('Premium')

    # ---------- q3: churn by signup cohort (year) ----------
    df['signup_year'] = df['signup_date'].dt.year
    def churn_rate_by_year(year):
        subset = df[df['signup_year'] == year]
        if len(subset) == 0:
            return 0.0
        return (subset['churned'].sum() / len(subset)) * 100

    churn_rate_cohort_2021_pct = churn_rate_by_year(2021)
    churn_rate_cohort_2022_pct = churn_rate_by_year(2022)
    churn_rate_cohort_2023_pct = churn_rate_by_year(2023)
    churn_rate_cohort_2024_pct = churn_rate_by_year(2024)

    # ---------- q4: contract effect ----------
    def churn_rate_by_contract(contract):
        subset = df[df['contract_type'] == contract]
        if len(subset) == 0:
            return 0.0
        return (subset['churned'].sum() / len(subset)) * 100

    churn_rate_monthly_pct = churn_rate_by_contract('Monthly')
    churn_rate_annual_pct = churn_rate_by_contract('Annual')
    if churn_rate_annual_pct != 0:
        churn_monthly_vs_annual_change_pct = ((churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct) * 100
    else:
        churn_monthly_vs_annual_change_pct = 0.0

    # ---------- q5: at‑risk segment ----------
    at_risk_mask = (
        (df['support_tickets'] >= 5) &
        (df['satisfaction_score'].notna()) &
        (df['satisfaction_score'] <= 2)
    )
    at_risk_df = df[at_risk_mask]
    at_risk_customer_count = int(len(at_risk_df))
    if at_risk_customer_count:
        at_risk_churn_rate_pct = (at_risk_df['churned'].sum() / at_risk_customer_count) * 100
    else:
        at_risk_churn_rate_pct = 0.0

    # ---------- q6: tenure & satisfaction summary ----------
    tenure_mean = df['tenure_months'].mean()
    tenure_median = df['tenure_months'].median()
    tenure_std = df['tenure_months'].std(ddof=1)  # sample std
    satisfaction_non_missing = df['satisfaction_score'].dropna()
    if len(satisfaction_non_missing):
        satisfaction_mean = satisfaction_non_missing.mean()
    else:
        satisfaction_mean = 0.0
    satisfaction_missing_count = int(df['satisfaction_score'].isna().sum())

    # ---------- q7: lifetime value by plan ----------
    def ltv_mean_by_plan(plan_name):
        subset = df[df['plan'] == plan_name]
        if len(subset) == 0:
            return 0.0
        return subset['lifetime_value'].mean()

    ltv_basic = ltv_mean_by_plan('Basic')
    ltv_standard = ltv_mean_by_plan('Standard')
    ltv_premium = ltv_mean_by_plan('Premium')
    if ltv_basic != 0:
        premium_vs_basic_ltv_change_pct = ((ltv_premium - ltv_basic) / ltv_basic) * 100
    else:
        premium_vs_basic_ltv_change_pct = 0.0

    # Assemble results
    results = {
        "customer_count": customer_count,
        "churn_rate_pct": churn_rate_pct,
        "avg_monthly_fee": avg_monthly_fee,
        "churn_rate_basic_pct": churn_rate_basic_pct,
        "churn_rate_standard_pct": churn_rate_standard_pct,
        "churn_rate_premium_pct": churn_rate_premium_pct,
        "churn_rate_cohort_2021_pct": churn_rate_cohort_2021_pct,
        "churn_rate_cohort_2022_pct": churn_rate_cohort_2022_pct,
        "churn_rate_cohort_2023_pct": churn_rate_cohort_2023_pct,
        "churn_rate_cohort_2024_pct": churn_rate_cohort_2024_pct,
        "churn_rate_monthly_pct": churn_rate_monthly_pct,
        "churn_rate_annual_pct": churn_rate_annual_pct,
        "churn_monthly_vs_annual_change_pct": churn_monthly_vs_annual_change_pct,
        "at_risk_customer_count": at_risk_customer_count,
        "at_risk_churn_rate_pct": at_risk_churn_rate_pct,
        "tenure_mean": tenure_mean,
        "tenure_median": tenure_median,
        "tenure_std": tenure_std,
        "satisfaction_mean": satisfaction_mean,
        "satisfaction_missing_count": satisfaction_missing_count,
        "ltv_basic": ltv_basic,
        "ltv_standard": ltv_standard,
        "ltv_premium": ltv_premium,
        "premium_vs_basic_ltv_change_pct": premium_vs_basic_ltv_change_pct
    }

    # Write findings.json
    with open(findings_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, allow_nan=False)

if __name__ == '__main__':
    main()
