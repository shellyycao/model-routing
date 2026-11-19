import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Load cleaned data
    df = pd.read_csv(input_path)

    # Ensure proper dtypes for calculations
    # signup_date to datetime for cohort analysis
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    df["signup_year"] = df["signup_date"].dt.year

    # ---------------------------------------------------------------------
    # q1 – overall metrics
    # ---------------------------------------------------------------------
    customer_count = len(df)
    churn_rate_pct = df["churned"].mean() * 100  # mean of 0/1 gives proportion
    avg_monthly_fee = df["monthly_fee"].mean()

    # ---------------------------------------------------------------------
    # q2 – churn by plan
    # ---------------------------------------------------------------------
    def churn_rate_for_plan(plan_name):
        sub = df[df["plan"] == plan_name]
        if len(sub) == 0:
            return 0.0
        return sub["churned"].mean() * 100

    churn_rate_basic_pct = churn_rate_for_plan("Basic")
    churn_rate_standard_pct = churn_rate_for_plan("Standard")
    churn_rate_premium_pct = churn_rate_for_plan("Premium")

    # ---------------------------------------------------------------------
    # q3 – churn by signup cohort (year)
    # ---------------------------------------------------------------------
    def churn_rate_for_year(year):
        sub = df[df["signup_year"] == year]
        if len(sub) == 0:
            return 0.0
        return sub["churned"].mean() * 100

    churn_rate_cohort_2021_pct = churn_rate_for_year(2021)
    churn_rate_cohort_2022_pct = churn_rate_for_year(2022)
    churn_rate_cohort_2023_pct = churn_rate_for_year(2023)
    churn_rate_cohort_2024_pct = churn_rate_for_year(2024)

    # ---------------------------------------------------------------------
    # q4 – contract effect
    # ---------------------------------------------------------------------
    def churn_rate_for_contract(contract_type):
        sub = df[df["contract_type"] == contract_type]
        if len(sub) == 0:
            return 0.0
        return sub["churned"].mean() * 100

    churn_rate_monthly_pct = churn_rate_for_contract("Monthly")
    churn_rate_annual_pct = churn_rate_for_contract("Annual")
    if churn_rate_annual_pct == 0:
        churn_monthly_vs_annual_change_pct = 0.0
    else:
        churn_monthly_vs_annual_change_pct = (
            (churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct * 100
        )

    # ---------------------------------------------------------------------
    # q5 – at‑risk segment
    # ---------------------------------------------------------------------
    at_risk_mask = (
        (df["support_tickets"] >= 5)
        & (df["satisfaction_score"].notna())
        & (df["satisfaction_score"] <= 2)
    )
    df_at_risk = df[at_risk_mask]
    at_risk_customer_count = len(df_at_risk)
    if at_risk_customer_count == 0:
        at_risk_churn_rate_pct = 0.0
    else:
        at_risk_churn_rate_pct = df_at_risk["churned"].mean() * 100

    # ---------------------------------------------------------------------
    # q6 – tenure and satisfaction summary
    # ---------------------------------------------------------------------
    tenure_mean = df["tenure_months"].mean()
    tenure_median = df["tenure_months"].median()
    tenure_std = df["tenure_months"].std(ddof=1)  # sample standard deviation
    satisfaction_mean = df["satisfaction_score"].mean()
    satisfaction_missing_count = df["satisfaction_score"].isna().sum()

    # ---------------------------------------------------------------------
    # q7 – lifetime value by plan
    # ---------------------------------------------------------------------
    def ltv_mean_for_plan(plan_name):
        sub = df[df["plan"] == plan_name]
        if len(sub) == 0:
            return 0.0
        return sub["lifetime_value"].mean()

    ltv_basic = ltv_mean_for_plan("Basic")
    ltv_standard = ltv_mean_for_plan("Standard")
    ltv_premium = ltv_mean_for_plan("Premium")
    if ltv_basic == 0:
        premium_vs_basic_ltv_change_pct = 0.0
    else:
        premium_vs_basic_ltv_change_pct = (
            (ltv_premium - ltv_basic) / ltv_basic * 100
        )

    # ---------------------------------------------------------------------
    # Assemble findings dictionary – all values must be plain Python numbers
    # ---------------------------------------------------------------------
    findings = {
        "customer_count": int(customer_count),
        "churn_rate_pct": float(churn_rate_pct),
        "avg_monthly_fee": float(avg_monthly_fee),
        "churn_rate_basic_pct": float(churn_rate_basic_pct),
        "churn_rate_standard_pct": float(churn_rate_standard_pct),
        "churn_rate_premium_pct": float(churn_rate_premium_pct),
        "churn_rate_cohort_2021_pct": float(churn_rate_cohort_2021_pct),
        "churn_rate_cohort_2022_pct": float(churn_rate_cohort_2022_pct),
        "churn_rate_cohort_2023_pct": float(churn_rate_cohort_2023_pct),
        "churn_rate_cohort_2024_pct": float(churn_rate_cohort_2024_pct),
        "churn_rate_monthly_pct": float(churn_rate_monthly_pct),
        "churn_rate_annual_pct": float(churn_rate_annual_pct),
        "churn_monthly_vs_annual_change_pct": float(churn_monthly_vs_annual_change_pct),
        "at_risk_customer_count": int(at_risk_customer_count),
        "at_risk_churn_rate_pct": float(at_risk_churn_rate_pct),
        "tenure_mean": float(tenure_mean),
        "tenure_median": float(tenure_median),
        "tenure_std": float(tenure_std),
        "satisfaction_mean": float(satisfaction_mean) if not np.isnan(satisfaction_mean) else 0.0,
        "satisfaction_missing_count": int(satisfaction_missing_count),
        "ltv_basic": float(ltv_basic),
        "ltv_standard": float(ltv_standard),
        "ltv_premium": float(ltv_premium),
        "premium_vs_basic_ltv_change_pct": float(premium_vs_basic_ltv_change_pct)
    }

    # Write findings to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
