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

    # ---------- q1: overall metrics ----------
    customer_count = int(df.shape[0])
    churn_rate_pct = float(df["churned"].sum() / customer_count * 100)
    avg_monthly_fee = float(df["monthly_fee"].mean())

    # ---------- q2: churn by plan ----------
    def churn_rate_by_plan(plan):
        sub = df[df["plan"] == plan]
        if sub.empty:
            return 0.0
        return float(sub["churned"].sum() / len(sub) * 100)

    churn_rate_basic_pct = churn_rate_by_plan("Basic")
    churn_rate_standard_pct = churn_rate_by_plan("Standard")
    churn_rate_premium_pct = churn_rate_by_plan("Premium")

    # ---------- q3: churn by signup cohort (year) ----------
    df["signup_year"] = df["signup_date"].dt.year
    cohort_years = [2021, 2022, 2023, 2024]
    churn_rate_cohort = {}
    for yr in cohort_years:
        sub = df[df["signup_year"] == yr]
        if sub.empty:
            churn_rate = 0.0
        else:
            churn_rate = float(sub["churned"].sum() / len(sub) * 100)
        churn_rate_cohort[yr] = churn_rate

    churn_rate_cohort_2021_pct = churn_rate_cohort[2021]
    churn_rate_cohort_2022_pct = churn_rate_cohort[2022]
    churn_rate_cohort_2023_pct = churn_rate_cohort[2023]
    churn_rate_cohort_2024_pct = churn_rate_cohort[2024]

    # ---------- q4: contract effect ----------
    def churn_rate_by_contract(contract):
        sub = df[df["contract_type"] == contract]
        if sub.empty:
            return 0.0
        return float(sub["churned"].sum() / len(sub) * 100)

    churn_rate_monthly_pct = churn_rate_by_contract("Monthly")
    churn_rate_annual_pct = churn_rate_by_contract("Annual")
    if churn_rate_annual_pct == 0:
        churn_monthly_vs_annual_change_pct = 0.0
    else:
        churn_monthly_vs_annual_change_pct = float((churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct * 100)

    # ---------- q5: at‑risk segment ----------
    at_risk_mask = (df["support_tickets"] >= 5) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)
    at_risk_df = df[at_risk_mask]
    at_risk_customer_count = int(at_risk_df.shape[0])
    if at_risk_customer_count == 0:
        at_risk_churn_rate_pct = 0.0
    else:
        at_risk_churn_rate_pct = float(at_risk_df["churned"].sum() / at_risk_customer_count * 100)

    # ---------- q6: tenure and satisfaction summary ----------
    tenure_mean = float(df["tenure_months"].mean())
    tenure_median = float(df["tenure_months"].median())
    tenure_std = float(df["tenure_months"].std(ddof=1))
    satisfaction_mean = float(df["satisfaction_score"].mean(skipna=True))
    satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

    # ---------- q7: lifetime value by plan ----------
    def ltv_by_plan(plan):
        sub = df[df["plan"] == plan]
        if sub.empty:
            return 0.0
        return float(sub["lifetime_value"].mean())

    ltv_basic = ltv_by_plan("Basic")
    ltv_standard = ltv_by_plan("Standard")
    ltv_premium = ltv_by_plan("Premium")
    if ltv_basic == 0:
        premium_vs_basic_ltv_change_pct = 0.0
    else:
        premium_vs_basic_ltv_change_pct = float((ltv_premium - ltv_basic) / ltv_basic * 100)

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
