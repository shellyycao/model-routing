import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Load cleaned data
    df = pd.read_csv(input_path, parse_dates=["signup_date"])

    # ---------- Q1: Overall metrics ----------
    customer_count = int(len(df))
    churn_rate_pct = float(df["churned"].mean() * 100)
    avg_monthly_fee = float(df["monthly_fee"].mean())

    # ---------- Q2: Churn by plan ----------
    plans = ["Basic", "Standard", "Premium"]
    churn_rate_basic_pct = churn_rate_standard_pct = churn_rate_premium_pct = 0.0
    for plan in plans:
        sub = df[df["plan"] == plan]
        rate = float(sub["churned"].mean() * 100) if len(sub) > 0 else 0.0
        if plan == "Basic":
            churn_rate_basic_pct = rate
        elif plan == "Standard":
            churn_rate_standard_pct = rate
        else:
            churn_rate_premium_pct = rate

    # ---------- Q3: Churn by signup cohort (year) ----------
    df["signup_year"] = df["signup_date"].dt.year
    cohort_years = [2021, 2022, 2023, 2024]
    churn_rate_cohort_2021_pct = churn_rate_cohort_2022_pct = churn_rate_cohort_2023_pct = churn_rate_cohort_2024_pct = 0.0
    for year in cohort_years:
        sub = df[df["signup_year"] == year]
        rate = float(sub["churned"].mean() * 100) if len(sub) > 0 else 0.0
        if year == 2021:
            churn_rate_cohort_2021_pct = rate
        elif year == 2022:
            churn_rate_cohort_2022_pct = rate
        elif year == 2023:
            churn_rate_cohort_2023_pct = rate
        else:
            churn_rate_cohort_2024_pct = rate

    # ---------- Q4: Contract effect ----------
    monthly_sub = df[df["contract_type"] == "Monthly"]
    annual_sub = df[df["contract_type"] == "Annual"]
    churn_rate_monthly_pct = float(monthly_sub["churned"].mean() * 100) if len(monthly_sub) > 0 else 0.0
    churn_rate_annual_pct = float(annual_sub["churned"].mean() * 100) if len(annual_sub) > 0 else 0.0
    if churn_rate_annual_pct != 0:
        churn_monthly_vs_annual_change_pct = (churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct * 100
    else:
        churn_monthly_vs_annual_change_pct = 0.0

    # ---------- Q5: At‑risk segment ----------
    at_risk_mask = (
        (df["support_tickets"] >= 5) &
        (df["satisfaction_score"].notna()) &
        (df["satisfaction_score"] <= 2)
    )
    at_risk_customer_count = int(at_risk_mask.sum())
    if at_risk_customer_count > 0:
        at_risk_churn_rate_pct = float(df.loc[at_risk_mask, "churned"].mean() * 100)
    else:
        at_risk_churn_rate_pct = 0.0

    # ---------- Q6: Tenure and satisfaction summary ----------
    tenure_mean = float(df["tenure_months"].mean())
    tenure_median = float(df["tenure_months"].median())
    tenure_std = float(df["tenure_months"].std(ddof=1))
    satisfaction_mean = float(df["satisfaction_score"].mean()) if df["satisfaction_score"].notna().any() else 0.0
    satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

    # ---------- Q7: Lifetime value by plan ----------
    ltv_basic = ltv_standard = ltv_premium = 0.0
    for plan in plans:
        sub = df[df["plan"] == plan]
        mean_ltv = float(sub["lifetime_value"].mean()) if len(sub) > 0 else 0.0
        if plan == "Basic":
            ltv_basic = mean_ltv
        elif plan == "Standard":
            ltv_standard = mean_ltv
        else:
            ltv_premium = mean_ltv
    if ltv_basic != 0:
        premium_vs_basic_ltv_change_pct = (ltv_premium - ltv_basic) / ltv_basic * 100
    else:
        premium_vs_basic_ltv_change_pct = 0.0

    # ---------- Assemble findings ----------
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

    # Write findings to JSON (flat, numeric values only)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
