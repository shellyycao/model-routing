import os
import json
import pandas as pd
import numpy as np

def safe_pct(numer, denom):
    """Return percentage (numer/denom*100) handling zero denominator."""
    return (numer / denom * 100) if denom else 0.0

def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    df = pd.read_csv(
        input_path,
        dtype={"customer_id": str},
        parse_dates=["signup_date"],
        keep_default_na=True,
        na_values=[""],
    )

    # ---------------------------------------------------------------------
    # q1: overall metrics
    # ---------------------------------------------------------------------
    customer_count = len(df)
    churn_rate_pct = safe_pct(df["churned"].sum(), customer_count)
    avg_monthly_fee = df["monthly_fee"].mean()

    # ---------------------------------------------------------------------
    # q2: churn by plan
    # ---------------------------------------------------------------------
    churn_rate_basic_pct = safe_pct(
        df.loc[df["plan"] == "Basic", "churned"].sum(),
        len(df.loc[df["plan"] == "Basic"]),
    )
    churn_rate_standard_pct = safe_pct(
        df.loc[df["plan"] == "Standard", "churned"].sum(),
        len(df.loc[df["plan"] == "Standard"]),
    )
    churn_rate_premium_pct = safe_pct(
        df.loc[df["plan"] == "Premium", "churned"].sum(),
        len(df.loc[df["plan"] == "Premium"]),
    )

    # ---------------------------------------------------------------------
    # q3: churn by signup cohort (year)
    # ---------------------------------------------------------------------
    df["signup_year"] = df["signup_date"].dt.year
    cohort_years = [2021, 2022, 2023, 2024]
    cohort_rates = {}
    for yr in cohort_years:
        sub = df[df["signup_year"] == yr]
        key = f"churn_rate_cohort_{yr}_pct"
        cohort_rates[key] = safe_pct(sub["churned"].sum(), len(sub))

    # ---------------------------------------------------------------------
    # q4: contract effect
    # ---------------------------------------------------------------------
    monthly = df[df["contract_type"] == "Monthly"]
    annual = df[df["contract_type"] == "Annual"]
    churn_rate_monthly_pct = safe_pct(monthly["churned"].sum(), len(monthly))
    churn_rate_annual_pct = safe_pct(annual["churned"].sum(), len(annual))
    churn_monthly_vs_annual_change_pct = (
        (churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct * 100
        if churn_rate_annual_pct else 0.0
    )

    # ---------------------------------------------------------------------
    # q5: at‑risk segment
    # ---------------------------------------------------------------------
    at_risk = df[(df["support_tickets"] >= 5) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)]
    at_risk_customer_count = len(at_risk)
    at_risk_churn_rate_pct = (
        safe_pct(at_risk["churned"].sum(), at_risk_customer_count)
        if at_risk_customer_count else 0.0
    )

    # ---------------------------------------------------------------------
    # q6: tenure and satisfaction summary
    # ---------------------------------------------------------------------
    tenure_mean = df["tenure_months"].mean()
    tenure_median = df["tenure_months"].median()
    tenure_std = df["tenure_months"].std(ddof=1)
    satisfaction_mean = df["satisfaction_score"].mean()
    satisfaction_missing_count = df["satisfaction_score"].isna().sum()

    # ---------------------------------------------------------------------
    # q7: lifetime value by plan
    # ---------------------------------------------------------------------
    ltv_basic = df.loc[df["plan"] == "Basic", "lifetime_value"].mean()
    ltv_standard = df.loc[df["plan"] == "Standard", "lifetime_value"].mean()
    ltv_premium = df.loc[df["plan"] == "Premium", "lifetime_value"].mean()
    premium_vs_basic_ltv_change_pct = (
        (ltv_premium - ltv_basic) / ltv_basic * 100 if ltv_basic else 0.0
    )

    # ---------------------------------------------------------------------
    # Assemble findings
    # ---------------------------------------------------------------------
    findings = {
        "customer_count": int(customer_count),
        "churn_rate_pct": float(churn_rate_pct),
        "avg_monthly_fee": float(avg_monthly_fee),
        "churn_rate_basic_pct": float(churn_rate_basic_pct),
        "churn_rate_standard_pct": float(churn_rate_standard_pct),
        "churn_rate_premium_pct": float(churn_rate_premium_pct),
        "churn_rate_cohort_2021_pct": float(cohort_rates["churn_rate_cohort_2021_pct"]),
        "churn_rate_cohort_2022_pct": float(cohort_rates["churn_rate_cohort_2022_pct"]),
        "churn_rate_cohort_2023_pct": float(cohort_rates["churn_rate_cohort_2023_pct"]),
        "churn_rate_cohort_2024_pct": float(cohort_rates["churn_rate_cohort_2024_pct"]),
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
        "premium_vs_basic_ltv_change_pct": float(premium_vs_basic_ltv_change_pct),
    }

    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
