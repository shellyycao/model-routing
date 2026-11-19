import os
import json
import pandas as pd
import numpy as np

def safe_mean(series):
    """Return mean of a pandas Series, or 0 if empty."""
    if series.empty:
        return 0.0
    return series.mean()

def safe_std(series):
    """Return sample standard deviation, or 0 if less than 2 values."""
    if len(series) < 2:
        return 0.0
    return series.std(ddof=1)

def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Load cleaned data
    df = pd.read_csv(input_path, parse_dates=["signup_date"], dtype={
        "customer_id": str,
        "plan": str,
        "contract_type": str,
        "monthly_fee": float,
        "tenure_months": int,
        "support_tickets": int,
        "satisfaction_score": float,
        "churned": int,
        "lifetime_value": float,
    })

    # Overall metrics
    customer_count = len(df)
    churn_rate_pct = (df["churned"].sum() / customer_count) * 100 if customer_count else 0.0
    avg_monthly_fee = safe_mean(df["monthly_fee"])

    # Churn by plan
    churn_rate_basic_pct = safe_mean(df.loc[df["plan"] == "Basic", "churned"]) * 100
    churn_rate_standard_pct = safe_mean(df.loc[df["plan"] == "Standard", "churned"]) * 100
    churn_rate_premium_pct = safe_mean(df.loc[df["plan"] == "Premium", "churned"]) * 100

    # Churn by signup cohort (year)
    df["signup_year"] = df["signup_date"].dt.year
    cohort_years = [2021, 2022, 2023, 2024]
    churn_rate_cohort = {}
    for yr in cohort_years:
        cohort = df[df["signup_year"] == yr]
        if not cohort.empty:
            churn_rate_cohort[yr] = cohort["churned"].mean() * 100
        else:
            churn_rate_cohort[yr] = 0.0

    # Contract effect
    churn_rate_monthly_pct = safe_mean(df.loc[df["contract_type"] == "Monthly", "churned"]) * 100
    churn_rate_annual_pct = safe_mean(df.loc[df["contract_type"] == "Annual", "churned"]) * 100
    if churn_rate_annual_pct != 0:
        churn_monthly_vs_annual_change_pct = ((churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct) * 100
    else:
        churn_monthly_vs_annual_change_pct = 0.0

    # At‑risk segment
    at_risk_mask = (
        (df["support_tickets"] >= 5) &
        df["satisfaction_score"].notna() &
        (df["satisfaction_score"] <= 2)
    )
    at_risk_customer_count = int(at_risk_mask.sum())
    if at_risk_customer_count:
        at_risk_churn_rate_pct = df.loc[at_risk_mask, "churned"].mean() * 100
    else:
        at_risk_churn_rate_pct = 0.0

    # Tenure and satisfaction summary
    tenure_mean = safe_mean(df["tenure_months"])
    tenure_median = df["tenure_months"].median() if not df["tenure_months"].empty else 0.0
    tenure_std = safe_std(df["tenure_months"])
    satisfaction_mean = safe_mean(df["satisfaction_score"].dropna())
    satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

    # Lifetime value by plan
    ltv_basic = safe_mean(df.loc[df["plan"] == "Basic", "lifetime_value"])
    ltv_standard = safe_mean(df.loc[df["plan"] == "Standard", "lifetime_value"])
    ltv_premium = safe_mean(df.loc[df["plan"] == "Premium", "lifetime_value"])
    if ltv_basic != 0:
        premium_vs_basic_ltv_change_pct = ((ltv_premium - ltv_basic) / ltv_basic) * 100
    else:
        premium_vs_basic_ltv_change_pct = 0.0

    # Assemble findings
    findings = {
        "customer_count": float(customer_count),
        "churn_rate_pct": churn_rate_pct,
        "avg_monthly_fee": avg_monthly_fee,
        "churn_rate_basic_pct": churn_rate_basic_pct,
        "churn_rate_standard_pct": churn_rate_standard_pct,
        "churn_rate_premium_pct": churn_rate_premium_pct,
        "churn_rate_cohort_2021_pct": churn_rate_cohort[2021],
        "churn_rate_cohort_2022_pct": churn_rate_cohort[2022],
        "churn_rate_cohort_2023_pct": churn_rate_cohort[2023],
        "churn_rate_cohort_2024_pct": churn_rate_cohort[2024],
        "churn_rate_monthly_pct": churn_rate_monthly_pct,
        "churn_rate_annual_pct": churn_rate_annual_pct,
        "churn_monthly_vs_annual_change_pct": churn_monthly_vs_annual_change_pct,
        "at_risk_customer_count": float(at_risk_customer_count),
        "at_risk_churn_rate_pct": at_risk_churn_rate_pct,
        "tenure_mean": tenure_mean,
        "tenure_median": tenure_median,
        "tenure_std": tenure_std,
        "satisfaction_mean": satisfaction_mean,
        "satisfaction_missing_count": float(satisfaction_missing_count),
        "ltv_basic": ltv_basic,
        "ltv_standard": ltv_standard,
        "ltv_premium": ltv_premium,
        "premium_vs_basic_ltv_change_pct": premium_vs_basic_ltv_change_pct,
    }

    # Write findings to JSON (ensure plain numbers, no NaN)
    # Replace any possible NaN with 0.0 to satisfy "finite number" requirement
    for k, v in findings.items():
        if pd.isna(v):
            findings[k] = 0.0

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False, separators=(',', ':'))

if __name__ == "__main__":
    main()
