import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths from environment variables
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Load cleaned data
    df = pd.read_csv(input_path)
    # Ensure proper dtypes where needed
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    # Overall metrics
    customer_count = int(len(df))
    churn_rate_pct = float(df["churned"].mean() * 100)
    avg_monthly_fee = float(df["monthly_fee"].mean())

    # Churn by plan
    plan_churn = df.groupby("plan")["churned"].mean() * 100
    churn_rate_basic_pct = float(plan_churn.get("Basic", 0.0))
    churn_rate_standard_pct = float(plan_churn.get("Standard", 0.0))
    churn_rate_premium_pct = float(plan_churn.get("Premium", 0.0))

    # Churn by signup cohort (year)
    df["signup_year"] = df["signup_date"].dt.year
    year_churn = df.groupby("signup_year")["churned"].mean() * 100
    churn_rate_cohort_2021_pct = float(year_churn.get(2021, 0.0))
    churn_rate_cohort_2022_pct = float(year_churn.get(2022, 0.0))
    churn_rate_cohort_2023_pct = float(year_churn.get(2023, 0.0))
    churn_rate_cohort_2024_pct = float(year_churn.get(2024, 0.0))

    # Contract effect
    monthly_rate = df[df["contract_type"] == "Monthly"]["churned"].mean() * 100
    annual_rate = df[df["contract_type"] == "Annual"]["churned"].mean() * 100
    churn_rate_monthly_pct = float(monthly_rate)
    churn_rate_annual_pct = float(annual_rate)
    if annual_rate != 0:
        churn_monthly_vs_annual_change_pct = float((monthly_rate - annual_rate) / annual_rate * 100)
    else:
        churn_monthly_vs_annual_change_pct = 0.0

    # At‑risk segment
    at_risk_mask = (
        (df["support_tickets"] >= 5) &
        df["satisfaction_score"].notna() &
        (df["satisfaction_score"] <= 2)
    )
    at_risk_df = df[at_risk_mask]
    at_risk_customer_count = int(len(at_risk_df))
    if at_risk_customer_count > 0:
        at_risk_churn_rate_pct = float(at_risk_df["churned"].mean() * 100)
    else:
        at_risk_churn_rate_pct = 0.0

    # Tenure and satisfaction summary
    tenure_mean = float(df["tenure_months"].mean())
    tenure_median = float(df["tenure_months"].median())
    tenure_std = float(df["tenure_months"].std(ddof=1))
    satisfaction_mean = float(df["satisfaction_score"].mean())
    satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

    # Lifetime value by plan
    ltv_means = df.groupby("plan")["lifetime_value"].mean()
    ltv_basic = float(ltv_means.get("Basic", np.nan))
    ltv_standard = float(ltv_means.get("Standard", np.nan))
    ltv_premium = float(ltv_means.get("Premium", np.nan))
    if ltv_basic != 0:
        premium_vs_basic_ltv_change_pct = float((ltv_premium - ltv_basic) / ltv_basic * 100)
    else:
        premium_vs_basic_ltv_change_pct = 0.0

    # Assemble findings
    findings = {
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

    # Write findings to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
