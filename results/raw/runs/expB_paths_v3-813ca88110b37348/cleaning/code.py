import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import re

# ---------- Helper functions ----------

def is_missing(val):
    """Return True if the stripped string value should be considered missing."""
    if pd.isna(val):
        return True
    if isinstance(val, str):
        return val.strip().lower() in {"", "na", "n/a", "null", "none", "-"}
    return False

def clean_cell(val):
    """Strip whitespace and convert defined missing tokens to np.nan."""
    if pd.isna(val):
        return np.nan
    if isinstance(val, str):
        v = val.strip()
        return np.nan if v.lower() in {"", "na", "n/a", "null", "none", "-"} else v
    return val

def parse_date(date_str):
    """Try the allowed date formats, return YYYY-MM-DD string or None."""
    if pd.isna(date_str):
        return None
    formats = [
        "%Y-%m-%d",          # 2021-01-01
        "%m/%d/%Y",          # 01/21/2021
        "%d-%b-%Y",          # 07-Jan-2021 (Mon abbreviation)
        "%Y/%m/%d",          # 2021/01/07
        "%B %d, %Y",         # March 5, 2024
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return None

# ---------- Main cleaning script ----------

def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # 1. Read raw CSV as text, no automatic NA conversion
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)

    # 2. Strip whitespace and normalise missing values for every cell
    df = df.applymap(clean_cell)

    summary = {
        "raw_rows": raw_rows,
        "duplicates_removed": 0,
        "rows_dropped_signup_date": 0,
        "rows_dropped_plan": 0,
        "rows_dropped_contract_type": 0,
        "rows_dropped_monthly_fee": 0,
        "rows_dropped_tenure_months": 0,
        "rows_dropped_support_tickets": 0,
        "rows_dropped_churned": 0,
        "satisfaction_score_invalid": 0,
        "cleaned_rows": 0
    }

    # R2 – Remove duplicate customer_id rows (keep first)
    before = len(df)
    df = df.drop_duplicates(subset="customer_id", keep="first")
    summary["duplicates_removed"] = before - len(df)

    # R3 – signup_date parsing
    before = len(df)
    df["signup_date_parsed"] = df["signup_date"].apply(parse_date)
    df = df[~df["signup_date_parsed"].isna()]
    summary["rows_dropped_signup_date"] = before - len(df)
    df = df.drop(columns=["signup_date"]).rename(columns={"signup_date_parsed": "signup_date"})

    # R4 – plan mapping
    plan_map = {
        "basic": "Basic",
        "basic plan": "Basic",
        "standard": "Standard",
        "std": "Standard",
        "standard plan": "Standard",
        "premium": "Premium",
        "prem": "Premium",
        "premium plan": "Premium"
    }
    before = len(df)
    df["plan_clean"] = df["plan"].str.lower().map(plan_map)
    df = df[~df["plan_clean"].isna()]
    summary["rows_dropped_plan"] = before - len(df)
    df = df.drop(columns=["plan"]).rename(columns={"plan_clean": "plan"})

    # R5 – contract_type mapping
    contract_map = {
        "monthly": "Monthly",
        "month-to-month": "Monthly",
        "m2m": "Monthly",
        "annual": "Annual",
        "yearly": "Annual",
        "1 year": "Annual"
    }
    before = len(df)
    df["contract_clean"] = df["contract_type"].str.lower().map(contract_map)
    df = df[~df["contract_clean"].isna()]
    summary["rows_dropped_contract_type"] = before - len(df)
    df = df.drop(columns=["contract_type"]).rename(columns={"contract_clean": "contract_type"})

    # R6 – monthly_fee cleaning and validation
    def clean_fee(val):
        if pd.isna(val):
            return np.nan
        v = re.sub(r"(?i)\$|USD|,", "", val)  # remove $, USD, commas
        v = v.strip()
        try:
            num = float(v)
            return num
        except Exception:
            return np.nan
    before = len(df)
    df["monthly_fee_num"] = df["monthly_fee"].apply(clean_fee)
    df = df[~df["monthly_fee_num"].isna()]
    df = df[(df["monthly_fee_num"] > 0) & (df["monthly_fee_num"] <= 500)]
    summary["rows_dropped_monthly_fee"] = before - len(df)
    df = df.drop(columns=["monthly_fee"]).rename(columns={"monthly_fee_num": "monthly_fee"})

    # R7 – tenure_months cleaning and validation
    def clean_tenure(val):
        if pd.isna(val):
            return np.nan
        v = re.sub(r"(?i)\s*months?\s*$", "", val).strip()
        try:
            num = float(v)
            return num
        except Exception:
            return np.nan
    before = len(df)
    df["tenure_num"] = df["tenure_months"].apply(clean_tenure)
    df = df[~df["tenure_num"].isna()]
    df = df[(df["tenure_num"] >= 0) & (df["tenure_num"] <= 120) & (df["tenure_num"] % 1 == 0)]
    summary["rows_dropped_tenure_months"] = before - len(df)
    df = df.drop(columns=["tenure_months"]).rename(columns={"tenure_num": "tenure_months"})
    df["tenure_months"] = df["tenure_months"].astype(int)

    # R8 – support_tickets cleaning and validation (missing -> 0)
    def clean_tickets(val):
        if pd.isna(val):
            return 0
        try:
            num = float(val)
            return int(num)
        except Exception:
            return np.nan
    before = len(df)
    df["support_tickets_num"] = df["support_tickets"].apply(clean_tickets)
    df = df[~df["support_tickets_num"].isna()]
    df = df[(df["support_tickets_num"] >= 0) & (df["support_tickets_num"] <= 100)]
    summary["rows_dropped_support_tickets"] = before - len(df)
    df = df.drop(columns=["support_tickets"]).rename(columns={"support_tickets_num": "support_tickets"})
    df["support_tickets"] = df["support_tickets"].astype(int)

    # R9 – satisfaction_score (invalid -> missing, keep row)
    def clean_sat(val):
        if pd.isna(val):
            return np.nan
        try:
            num = float(val)
            if num.is_integer() and 1 <= int(num) <= 5:
                return int(num)
            else:
                return np.nan
        except Exception:
            return np.nan
    df["satisfaction_clean"] = df["satisfaction_score"].apply(clean_sat)
    summary["satisfaction_score_invalid"] = df["satisfaction_score"].ne(df["satisfaction_clean"]).sum()
    df = df.drop(columns=["satisfaction_score"]).rename(columns={"satisfaction_clean": "satisfaction_score"})

    # R10 – churned mapping
    churn_map = {
        "yes": 1, "y": 1, "true": 1, "1": 1, "churned": 1,
        "no": 0, "n": 0, "false": 0, "0": 0, "active": 0
    }
    before = len(df)
    df["churned_clean"] = df["churned"].str.lower().map(churn_map)
    df = df[~df["churned_clean"].isna()]
    summary["rows_dropped_churned"] = before - len(df)
    df = df.drop(columns=["churned"]).rename(columns={"churned_clean": "churned"})
    df["churned"] = df["churned"].astype(int)

    # R11 – lifetime_value
    df["lifetime_value"] = (df["monthly_fee"] * df["tenure_months"]).round(2)

    # R12 – final column order and sorting
    final_cols = [
        "customer_id",
        "signup_date",
        "plan",
        "contract_type",
        "monthly_fee",
        "tenure_months",
        "support_tickets",
        "satisfaction_score",
        "churned",
        "lifetime_value"
    ]
    df = df[final_cols]
    df = df.sort_values(by="customer_id", ascending=True)

    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False, na_rep="")

    # Summary JSON
    summary["cleaned_rows"] = len(df)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
