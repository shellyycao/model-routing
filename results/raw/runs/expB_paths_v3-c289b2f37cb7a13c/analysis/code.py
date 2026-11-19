import os
import json
import pandas as pd
import numpy as np

def safe_mean(series):
    if series.empty:
        return 0.0
    return series.mean()

def safe_std(series):
    if len(series) <= 1:
        return 0.0
    return series.std(ddof=1)

def safe_rate(churned_series, total):
    if total == 0:
        return 0.0
    return (churned_series.sum() / total) * 100.0

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
    churn_rate_pct = safe_rate(df["churned"], customer_count)
    avg_monthly_fee = safe_mean(df["monthly_fee"])

    # Churn by plan
    churn_rate_basic_pct = safe_rate(df.loc[df["plan"] == "Basic", "churned"],
                                      (df["plan"] == "Basic").sum())
    churn_rate_standard_pct = safe_rate(df.loc[df["plan"] == "Standard", "churned"],
                                         (df["plan"] == "Standard").sum())
    churn_rate_premium_pct = safe_rate(df.loc[df["plan"] == "Premium", "churned"],
                                        (df["plan"] == "Premium").sum())

    # Churn by signup cohort (year)
    df["signup_year"] = df["signup_date"].dt.year
    churn_rate_cohort_2021_pct = safe_rate(df.loc[df["signup_year"] == 2021, "churned"],
                                            (df["signup_year"] == 2021).sum())
    churn_rate_cohort_2022_pct = safe_rate(df.loc[df["signup_year"] == 2022, "churned"],
                                            (df["signup_year"] == 2022).sum())
    churn_rate_cohort_2023_pct = safe_rate(df.loc[df["signup_year"] == 2023, "churned"],
                                            (df["signup_year"] == 2023).sum())
    churn_rate_cohort_2024_pct = safe_rate(df.loc[df["signup_year"] == 2024, "churned"],
                                            (df["signup_year"] == 2024).sum())

    # Contract effect
    churn_rate_monthly_pct = safe_rate(df.loc[df["contract_type"] == "Monthly", "churned"],
                                        (df["contract_type"] == "Monthly").sum())
    churn_rate_annual_pct = safe_rate(df.loc[df["contract_type"] == "Annual", "churned"],
                                       (df["contract_type"] == "Annual").sum())
    if churn_rate_annual_pct == 0:
        churn_monthly_vs_annual_change_pct = 0.0
    else:
        churn_monthly_vs_annual_change_pct = ((churn_rate_monthly_pct - churn_rate_annual_pct) /
                                               churn_rate_annual_pct) * 100.0

    # At‑risk segment
    at_risk_mask = (df["support_tickets"] >= 5) & df["satisfaction_score"].notna() & (df["satisfaction_score"] <= 2)
    at_risk_customer_count = int(at_risk_mask.sum())
    if at_risk_customer_count == 0:
        at_risk_churn_rate_pct = 0.0
    else:
        at_risk_churn_rate_pct = safe_rate(df.loc[at_risk_mask, "churned"], at_risk_customer_count)

    # Tenure and satisfaction summary
    tenure_mean = safe_mean(df["tenure_months"])
    tenure_median = safe_mean(df["tenure_months"].sort_values().iloc[len(df)//2:len(df)//2+1]) if not df["tenure_months"].empty else 0.0
    # Simpler: use pandas median directly (handles empty)
    tenure_median = df["tenure_months"].median() if not df["tenure_months"].empty else 0.0
    tenure_std = safe_std(df["tenure_months"])
    satisfaction_mean = safe_mean(df.loc[df["satisfaction_score"].notna(), "satisfaction_score"])
    satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

    # Lifetime value by plan
    ltv_basic = safe_mean(df.loc[df["plan"] == "Basic", "lifetime_value"])
    ltv_standard = safe_mean(df.loc[df["plan"] == "Standard", "lifetime_value"])
    ltv_premium = safe_mean(df.loc[df["plan"] == "Premium", "lifetime_value"])
    if ltv_basic == 0:
        premium_vs_basic_ltv_change_pct = 0.0
    else:
        premium_vs_basic_ltv_change_pct = ((ltv_premium - ltv_basic) / ltv_basic) * 100.0

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

    # Ensure all values are plain Python floats/ints for JSON serialization
    findings = {k: float(v) if isinstance(v, (np.float64, np.int64)) else v for k, v in findings.items()}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False, separators=(',', ':'))

if __name__ == "__main__":
    main()
