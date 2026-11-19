import os
import json
import pandas as pd
import numpy as np

def safe_float(x):
    """Convert a value to a plain Python float, handling NaN by returning 0.0."""
    if pd.isna(x):
        return 0.0
    return float(x)

def main():
    # Paths
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Load cleaned data
    df = pd.read_csv(input_path, parse_dates=["signup_date"])

    # ---------- q1: overall metrics ----------
    customer_count = int(len(df))
    churn_rate_pct = safe_float(df["churned"].sum() / customer_count * 100)
    avg_monthly_fee = safe_float(df["monthly_fee"].mean())

    # ---------- q2: churn by plan ----------
    churn_by_plan = df.groupby("plan")["churned"].agg(["sum", "count"]).reset_index()
    def plan_rate(plan_name):
        row = churn_by_plan[churn_by_plan["plan"] == plan_name]
        if row.empty:
            return 0.0
        return safe_float(row["sum"].iloc[0] / row["count"].iloc[0] * 100)
    churn_rate_basic_pct = plan_rate("Basic")
    churn_rate_standard_pct = plan_rate("Standard")
    churn_rate_premium_pct = plan_rate("Premium")

    # ---------- q3: churn by signup cohort (year) ----------
    df["signup_year"] = df["signup_date"].dt.year
    churn_by_year = df.groupby("signup_year")["churned"].agg(["sum", "count"]).reset_index()
    def year_rate(year):
        row = churn_by_year[churn_by_year["signup_year"] == year]
        if row.empty:
            return 0.0
        return safe_float(row["sum"].iloc[0] / row["count"].iloc[0] * 100)
    churn_rate_cohort_2021_pct = year_rate(2021)
    churn_rate_cohort_2022_pct = year_rate(2022)
    churn_rate_cohort_2023_pct = year_rate(2023)
    churn_rate_cohort_2024_pct = year_rate(2024)

    # ---------- q4: contract effect ----------
    churn_by_contract = df.groupby("contract_type")["churned"].agg(["sum", "count"]).reset_index()
    def contract_rate(contract):
        row = churn_by_contract[churn_by_contract["contract_type"] == contract]
        if row.empty:
            return 0.0
        return safe_float(row["sum"].iloc[0] / row["count"].iloc[0] * 100)
    churn_rate_monthly_pct = contract_rate("Monthly")
    churn_rate_annual_pct = contract_rate("Annual")
    if churn_rate_annual_pct == 0:
        churn_monthly_vs_annual_change_pct = 0.0
    else:
        churn_monthly_vs_annual_change_pct = safe_float((churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct * 100)

    # ---------- q5: at‑risk segment ----------
    at_risk_mask = (
        (df["support_tickets"] >= 5) &
        (df["satisfaction_score"].notna()) &
        (df["satisfaction_score"] <= 2)
    )
    at_risk_df = df[at_risk_mask]
    at_risk_customer_count = int(len(at_risk_df))
    if at_risk_customer_count == 0:
        at_risk_churn_rate_pct = 0.0
    else:
        at_risk_churn_rate_pct = safe_float(at_risk_df["churned"].sum() / at_risk_customer_count * 100)

    # ---------- q6: tenure and satisfaction summary ----------
    tenure_mean = safe_float(df["tenure_months"].mean())
    tenure_median = safe_float(df["tenure_months"].median())
    tenure_std = safe_float(df["tenure_months"].std(ddof=1))
    satisfaction_mean = safe_float(df["satisfaction_score"].mean())
    satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

    # ---------- q7: lifetime value by plan ----------
    ltv_by_plan = df.groupby("plan")["lifetime_value"].mean().reset_index()
    def ltv_plan(plan_name):
        row = ltv_by_plan[ltv_by_plan["plan"] == plan_name]
        if row.empty:
            return 0.0
        return safe_float(row["lifetime_value"].iloc[0])
    ltv_basic = ltv_plan("Basic")
    ltv_standard = ltv_plan("Standard")
    ltv_premium = ltv_plan("Premium")
    if ltv_basic == 0:
        premium_vs_basic_ltv_change_pct = 0.0
    else:
        premium_vs_basic_ltv_change_pct = safe_float((ltv_premium - ltv_basic) / ltv_basic * 100)

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

    # Write findings to JSON (flat, no NaN/Inf)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
