# SYNTHETIC_FIXTURE - test solution, not a model output and not a result.
"""pandas cleaning script for customer_churn written ONLY from project.json cleaning_requirements.
Independent of datasets/customer_churn.py. Bugs for negative tests:
  no_dedup, drop_missing_satisfaction, tickets_missing_dropped, churn_strings_unmapped
"""

import os
import re
import sys

import pandas as pd

MISSING = {"", "na", "n/a", "null", "none", "-"}
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december"]


def _date(s):
    if not isinstance(s, str):
        return None
    for pat, order in [(r"(\d{4})-(\d{2})-(\d{2})", "ymd"), (r"(\d{4})/(\d{2})/(\d{2})", "ymd"),
                       (r"(\d{2})/(\d{2})/(\d{4})", "mdy")]:
        if m := re.fullmatch(pat, s):
            y, mo, d = (m[1], m[2], m[3]) if order == "ymd" else (m[3], m[1], m[2])
            try:
                return pd.Timestamp(int(y), int(mo), int(d))
            except ValueError:
                return None
    if m := re.fullmatch(r"(\d{2})-([A-Za-z]{3})-(\d{4})", s):
        return pd.Timestamp(int(m[3]), [x[:3] for x in MONTHS].index(m[2].lower()) + 1, int(m[1]))
    if m := re.fullmatch(r"([A-Za-z]+) (\d{1,2}), (\d{4})", s):
        return pd.Timestamp(int(m[3]), MONTHS.index(m[1].lower()) + 1, int(m[2]))
    return None


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _whole(x, lo, hi):
    return x is not None and x == int(x) and lo <= x <= hi


def clean(raw: pd.DataFrame, bug: str | None = None) -> pd.DataFrame:
    df = raw.copy()
    for c in df.columns:
        df[c] = df[c].map(lambda v: None if str(v).strip().lower() in MISSING else str(v).strip())
    if bug != "no_dedup":
        df = df.drop_duplicates("customer_id", keep="first")
    df["signup_date"] = df["signup_date"].map(_date)
    df = df[df["signup_date"].notna()]
    plans = {"basic": "Basic", "standard": "Standard", "premium": "Premium", "basic plan": "Basic",
             "std": "Standard", "standard plan": "Standard", "prem": "Premium", "premium plan": "Premium"}
    df["plan"] = df["plan"].map(lambda s: plans.get(s.lower()) if isinstance(s, str) else None)
    df = df[df["plan"].notna()]
    contracts = {"monthly": "Monthly", "month-to-month": "Monthly", "m2m": "Monthly",
                 "annual": "Annual", "yearly": "Annual", "1 year": "Annual"}
    df["contract_type"] = df["contract_type"].map(lambda s: contracts.get(s.lower()) if isinstance(s, str) else None)
    df = df[df["contract_type"].notna()]
    df["monthly_fee"] = df["monthly_fee"].map(
        lambda s: _num(s.replace("$", "").replace("USD", "").replace(",", "").strip()) if isinstance(s, str) else None)
    df = df[df["monthly_fee"].notna() & (df["monthly_fee"] > 0) & (df["monthly_fee"] <= 500)]
    df["tenure_months"] = df["tenure_months"].map(
        lambda s: _num(re.sub(r"\s*months?$", "", s, flags=re.I)) if isinstance(s, str) else None)
    df = df[df["tenure_months"].map(lambda x: _whole(x, 0, 120))]
    if bug == "tickets_missing_dropped":
        df = df[df["support_tickets"].notna()]
    df["support_tickets"] = df["support_tickets"].map(lambda s: _num(s) if isinstance(s, str) else 0.0)
    df = df[df["support_tickets"].map(lambda x: _whole(x, 0, 100))]
    df["satisfaction_score"] = df["satisfaction_score"].map(
        lambda s: _num(s) if isinstance(s, str) and _whole(_num(s), 1, 5) else None)
    if bug == "drop_missing_satisfaction":
        df = df[df["satisfaction_score"].notna()]
    yes = {"yes", "y", "true", "1", "churned"}
    no = {"no", "n", "false", "0", "active"}
    if bug == "churn_strings_unmapped":
        yes, no = {"yes", "1"}, {"no", "0"}
    df["churned"] = df["churned"].map(
        lambda s: 1 if isinstance(s, str) and s.lower() in yes else (0 if isinstance(s, str) and s.lower() in no else None))
    df = df[df["churned"].notna()]
    df["tenure_months"] = df["tenure_months"].astype(int)
    df["support_tickets"] = df["support_tickets"].astype(int)
    df["churned"] = df["churned"].astype(int)
    df["satisfaction_score"] = df["satisfaction_score"].astype("Int64")
    df["lifetime_value"] = (df["monthly_fee"] * df["tenure_months"]).round(2)
    df["signup_date"] = df["signup_date"].map(lambda t: t.strftime("%Y-%m-%d"))
    cols = ["customer_id", "signup_date", "plan", "contract_type", "monthly_fee", "tenure_months",
            "support_tickets", "satisfaction_score", "churned", "lifetime_value"]
    return df[cols].sort_values("customer_id").reset_index(drop=True)


def main():
    raw = pd.read_csv(os.path.join(os.environ["INPUT_DIR"], "raw.csv"), dtype=str, keep_default_na=False)
    clean(raw, sys.argv[1] if len(sys.argv) > 1 else None).to_csv(
        os.path.join(os.environ["OUTPUT_DIR"], "cleaned.csv"), index=False, float_format="%.2f")


if __name__ == "__main__":
    main()
