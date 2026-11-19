# SYNTHETIC_FIXTURE - test solution, not a model output and not a result.
"""pandas analysis for customer_churn written ONLY from project.json analysis_questions.
Bugs: rate_as_fraction, missing_sat_as_zero, at_risk_includes_missing_sat"""

import json
import os
import sys

import pandas as pd


def analyze(df: pd.DataFrame, bug: str | None = None) -> dict:
    scale = 1 if bug == "rate_as_fraction" else 100

    def rate(d):
        return d["churned"].mean() * scale

    m = {"customer_count": len(df), "churn_rate_pct": rate(df), "avg_monthly_fee": df["monthly_fee"].mean()}
    for p in ["Basic", "Standard", "Premium"]:
        m[f"churn_rate_{p.lower()}_pct"] = rate(df[df["plan"] == p])
    year = pd.to_datetime(df["signup_date"]).dt.year
    for y in [2021, 2022, 2023, 2024]:
        m[f"churn_rate_cohort_{y}_pct"] = rate(df[year == y])
    m["churn_rate_monthly_pct"] = rate(df[df["contract_type"] == "Monthly"])
    m["churn_rate_annual_pct"] = rate(df[df["contract_type"] == "Annual"])
    m["churn_monthly_vs_annual_change_pct"] = (m["churn_rate_monthly_pct"] - m["churn_rate_annual_pct"]) / m["churn_rate_annual_pct"] * 100
    sat = df["satisfaction_score"].fillna(0) if bug in ("missing_sat_as_zero", "at_risk_includes_missing_sat") else df["satisfaction_score"]
    risk = df[(df["support_tickets"] >= 5) & (sat <= 2)]
    m["at_risk_customer_count"] = len(risk)
    m["at_risk_churn_rate_pct"] = rate(risk)
    m["tenure_mean"] = df["tenure_months"].mean()
    m["tenure_median"] = df["tenure_months"].median()
    m["tenure_std"] = df["tenure_months"].std()
    m["satisfaction_mean"] = (sat if bug == "missing_sat_as_zero" else df["satisfaction_score"]).mean()
    m["satisfaction_missing_count"] = int(df["satisfaction_score"].isna().sum())
    by_plan = df.groupby("plan")["lifetime_value"].mean()
    for p in ["Basic", "Standard", "Premium"]:
        m[f"ltv_{p.lower()}"] = by_plan[p]
    m["premium_vs_basic_ltv_change_pct"] = (m["ltv_premium"] - m["ltv_basic"]) / m["ltv_basic"] * 100
    return {k: float(v) for k, v in m.items()}


def main():
    df = pd.read_csv(os.path.join(os.environ["INPUT_DIR"], "cleaned.csv"))
    with open(os.path.join(os.environ["OUTPUT_DIR"], "findings.json"), "w") as fh:
        json.dump(analyze(df, sys.argv[1] if len(sys.argv) > 1 else None), fh, indent=2)


if __name__ == "__main__":
    main()
