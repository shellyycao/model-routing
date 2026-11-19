import os
import json
import pandas as pd
import numpy as np

def safe_mean(series):
    """Return mean of a series or 0.0 if empty."""
    return float(series.mean()) if len(series) > 0 else 0.0

def safe_percent(series):
    """Return percentage (mean*100) of a binary series or 0.0 if empty."""
    return float(series.mean() * 100) if len(series) > 0 else 0.0

def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Load cleaned data
    df = pd.read_csv(input_path)

    # Ensure correct dtypes (pandas may read numeric columns as float already)
    numeric_cols = [
        "monthly_fee",
        "tenure_months",
        "support_tickets",
        "satisfaction_score",
        "churned",
        "lifetime_value",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ---------------------------------------------------------------------
    # q1 – overall metrics
    # ---------------------------------------------------------------------
    customer_count = int(len(df))
    churn_rate_pct = safe_percent(df["churned"])
    avg_monthly_fee = safe_mean(df["monthly_fee"])

    # ---------------------------------------------------------------------
    # q2 – churn by plan
    # ---------------------------------------------------------------------
    plan_churn = df.groupby("plan")["churned"].mean() * 100
    churn_rate_basic_pct = float(plan_churn.get("Basic", 0.0))
    churn_rate_standard_pct = float(plan_churn.get("Standard", 0.0))
    churn_rate_premium_pct = float(plan_churn.get("Premium", 0.0))

    # ---------------------------------------------------------------------
    # q3 – churn by signup cohort (year)
    # ---------------------------------------------------------------------
    df["signup_year"] = pd.to_datetime(df["signup_date"]).dt.year
    cohort_churn = df.groupby("signup_year")["churned"].mean() * 100
    churn_rate_cohort_2021_pct = float(cohort_churn.get(2021, 0.0))
    churn_rate_cohort_2022_pct = float(cohort_churn.get(2022, 0.0))
    churn_rate_cohort_2023_pct = float(cohort_churn.get(2023, 0.0))
    churn_rate_cohort_2024_pct = float(cohort_churn.get(2024, 0.0))

    # ---------------------------------------------------------------------
    # q4 – contract effect
    # ---------------------------------------------------------------------
    monthly_rate = safe_percent(df[df["contract_type"] == "Monthly"]["churned"])
    annual_rate = safe_percent(df[df["contract_type"] == "Annual"]["churned"])
    if annual_rate != 0:
        churn_monthly_vs_annual_change_pct = (monthly_rate - annual_rate) / annual_rate * 100
    else:
        churn_monthly_vs_annual_change_pct = 0.0

    # ---------------------------------------------------------------------
    # q5 – at‑risk segment
    # ---------------------------------------------------------------------
    at_risk_mask = (
        (df["support_tickets"] >= 5)
        & df["satisfaction_score"].notna()
        & (df["satisfaction_score"] <= 2)
    )
    at_risk_df = df[at_risk_mask]
    at_risk_customer_count = int(len(at_risk_df))
    at_risk_churn_rate_pct = safe_percent(at_risk_df["churned"]) if at_risk_customer_count > 0 else 0.0

    # ---------------------------------------------------------------------
    # q6 – tenure & satisfaction summary
    # ---------------------------------------------------------------------
    tenure_mean = safe_mean(df["tenure_months"])
    tenure_median = float(df["tenure_months"].median()) if len(df) > 0 else 0.0
    tenure_std = float(df["tenure_months"].std(ddof=1)) if len(df) > 1 else 0.0
    satisfaction_mean = safe_mean(df["satisfaction_score"].dropna())
    satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

    # ---------------------------------------------------------------------
    # q7 – lifetime value by plan
    # ---------------------------------------------------------------------
    ltv_by_plan = df.groupby("plan")["lifetime_value"].mean()
    ltv_basic = float(ltv_by_plan.get("Basic", 0.0))
    ltv_standard = float(ltv_by_plan.get("Standard", 0.0))
    ltv_premium = float(ltv_by_plan.get("Premium", 0.0))
    if ltv_basic != 0:
        premium_vs_basic_ltv_change_pct = (ltv_premium - ltv_basic) / ltv_basic * 100
    else:
        premium_vs_basic_ltv_change_pct = 0.0

    # ---------------------------------------------------------------------
    # Assemble findings
    # ---------------------------------------------------------------------
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
        "churn_rate_monthly_pct": monthly_rate,
        "churn_rate_annual_pct": annual_rate,
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
        "premium_vs_basic_ltv_change_pct": premium_vs_basic_ltv_change_pct,
    }

    # Write findings to JSON (flat, numeric values only)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
