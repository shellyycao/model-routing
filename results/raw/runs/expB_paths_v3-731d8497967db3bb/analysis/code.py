import os
import json
import pandas as pd
import numpy as np

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
        "satisfaction_score": float,  # keep as float to allow NaN
        "churned": int,
        "lifetime_value": float,
    })

    # Helper to safely compute percentage (avoid division by zero)
    def pct(series):
        return 100.0 * series.mean() if len(series) > 0 else 0.0

    # q1 overall metrics
    customer_count = int(len(df))
    churn_rate_pct = pct(df["churned"])
    avg_monthly_fee = float(df["monthly_fee"].mean())

    # q2 churn by plan
    churn_rate_basic_pct = pct(df.loc[df["plan"] == "Basic", "churned"])
    churn_rate_standard_pct = pct(df.loc[df["plan"] == "Standard", "churned"])
    churn_rate_premium_pct = pct(df.loc[df["plan"] == "Premium", "churned"])

    # q3 churn by signup cohort (year)
    df["signup_year"] = df["signup_date"].dt.year
    cohort_years = [2021, 2022, 2023, 2024]
    churn_rate_cohort_2021_pct = pct(df.loc[df["signup_year"] == 2021, "churned"])
    churn_rate_cohort_2022_pct = pct(df.loc[df["signup_year"] == 2022, "churned"])
    churn_rate_cohort_2023_pct = pct(df.loc[df["signup_year"] == 2023, "churned"])
    churn_rate_cohort_2024_pct = pct(df.loc[df["signup_year"] == 2024, "churned"])

    # q4 contract effect
    churn_rate_monthly_pct = pct(df.loc[df["contract_type"] == "Monthly", "churned"])
    churn_rate_annual_pct = pct(df.loc[df["contract_type"] == "Annual", "churned"])
    if churn_rate_annual_pct != 0:
        churn_monthly_vs_annual_change_pct = (churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct * 100.0
    else:
        churn_monthly_vs_annual_change_pct = 0.0

    # q5 at‑risk segment
    at_risk_mask = (
        (df["support_tickets"] >= 5) &
        (df["satisfaction_score"].notna()) &
        (df["satisfaction_score"] <= 2)
    )
    at_risk_df = df[at_risk_mask]
    at_risk_customer_count = int(len(at_risk_df))
    at_risk_churn_rate_pct = pct(at_risk_df["churned"]) if at_risk_customer_count > 0 else 0.0

    # q6 tenure & satisfaction summary
    tenure_mean = float(df["tenure_months"].mean())
    tenure_median = float(df["tenure_months"].median())
    tenure_std = float(df["tenure_months"].std(ddof=1))
    satisfaction_non_missing = df["satisfaction_score"].dropna()
    satisfaction_mean = float(satisfaction_non_missing.mean()) if len(satisfaction_non_missing) > 0 else 0.0
    satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

    # q7 lifetime value by plan
    ltv_basic = float(df.loc[df["plan"] == "Basic", "lifetime_value"].mean())
    ltv_standard = float(df.loc[df["plan"] == "Standard", "lifetime_value"].mean())
    ltv_premium = float(df.loc[df["plan"] == "Premium", "lifetime_value"].mean())
    if ltv_basic != 0:
        premium_vs_basic_ltv_change_pct = (ltv_premium - ltv_basic) / ltv_basic * 100.0
    else:
        premium_vs_basic_ltv_change_pct = 0.0

    # Assemble findings dict (flat JSON)
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
        "premium_vs_basic_ltv_change_pct": premium_vs_basic_ltv_change_pct,
    }

    # Ensure all values are plain Python floats/ints (no numpy types)
    for k, v in findings.items():
        if isinstance(v, (np.generic, np.ndarray)):
            findings[k] = float(v)
        # ints are fine, but ensure they are Python int
        if isinstance(findings[k], np.integer):
            findings[k] = int(findings[k])

    # Write findings.json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
