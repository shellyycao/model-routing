import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import re

# ---------------------------------------------------------------------------
# Helper functions for parsing and cleaning
# ---------------------------------------------------------------------------

def parse_date(value):
    """Try to parse a date string using the allowed formats.
    Returns the date formatted as YYYY-MM-DD or None if parsing fails.
    """
    if pd.isna(value):
        return None
    value = value.strip()
    formats = [
        "%Y-%m-%d",          # 2021-01-01
        "%m/%d/%Y",          # 01/21/2021
        "%d-%b-%Y",          # 07-Jan-2021 (abbr month)
        "%Y/%m/%d",          # 2021/01/07
        "%B %d, %Y",         # March 5, 2024
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def clean_monthly_fee(value):
    if pd.isna(value):
        return None
    # Remove $ , USD (case‑insensitive) and surrounding spaces
    cleaned = re.sub(r"(?i)\$|USD|,", "", value).strip()
    if cleaned == "":
        return None
    try:
        fee = float(cleaned)
        return fee
    except ValueError:
        return None

def clean_tenure(value):
    if pd.isna(value):
        return None
    # Remove trailing 'month' or 'months' (case‑insensitive)
    cleaned = re.sub(r"(?i)\s*months?\s*$", "", value).strip()
    if cleaned == "":
        return None
    try:
        num = float(cleaned)
        if not num.is_integer():
            return None
        return int(num)
    except ValueError:
        return None

def clean_support_tickets(value):
    if pd.isna(value):
        return 0
    value = str(value).strip()
    if value == "":
        return 0
    try:
        num = float(value)
        if not num.is_integer():
            return None
        return int(num)
    except ValueError:
        return None

def clean_satisfaction(value):
    if pd.isna(value):
        return np.nan
    value = str(value).strip()
    if value == "":
        return np.nan
    try:
        num = float(value)
        if not num.is_integer():
            return np.nan
        iv = int(num)
        if 1 <= iv <= 5:
            return iv
        else:
            return np.nan
    except ValueError:
        return np.nan

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("INPUT_DIR and OUTPUT_DIR environment variables must be set")

    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # R1 – read everything as text, strip whitespace, treat defined tokens as missing
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_values=[])
    raw_rows = len(df)
    # Strip whitespace from every cell
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    # Define missing tokens (case‑insensitive)
    missing_tokens = {"", "na", "n/a", "null", "none", "-"}
    df = df.replace(to_replace=missing_tokens, value=np.nan, regex=False)

    # Counters for summary
    summary = {
        "raw_rows": raw_rows,
        "duplicate_removed": 0,
        "signup_date_dropped": 0,
        "plan_dropped": 0,
        "contract_type_dropped": 0,
        "monthly_fee_dropped": 0,
        "tenure_months_dropped": 0,
        "support_tickets_invalid": 0,
        "satisfaction_invalid": 0,
        "churned_dropped": 0,
    }

    # R2 – remove duplicate customer_id, keep first
    before_dup = len(df)
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    summary["duplicate_removed"] = before_dup - len(df)

    # -----------------------------------------------------------------------
    # R3 – signup_date parsing
    # -----------------------------------------------------------------------
    df["signup_date_parsed"] = df["signup_date"].apply(parse_date)
    mask = df["signup_date_parsed"].notna()
    summary["signup_date_dropped"] = len(df) - mask.sum()
    df = df[mask].copy()
    df = df.drop(columns=["signup_date"]).rename(columns={"signup_date_parsed": "signup_date"})

    # -----------------------------------------------------------------------
    # R4 – plan mapping
    # -----------------------------------------------------------------------
    plan_map = {
        "basic": "Basic",
        "basic plan": "Basic",
        "standard": "Standard",
        "std": "Standard",
        "standard plan": "Standard",
        "premium": "Premium",
        "prem": "Premium",
        "premium plan": "Premium",
    }
    df["plan_mapped"] = df["plan"].str.lower().map(plan_map)
    mask = df["plan_mapped"].notna()
    summary["plan_dropped"] = len(df) - mask.sum()
    df = df[mask].copy()
    df = df.drop(columns=["plan"]).rename(columns={"plan_mapped": "plan"})

    # -----------------------------------------------------------------------
    # R5 – contract_type mapping
    # -----------------------------------------------------------------------
    contract_map = {
        "monthly": "Monthly",
        "month-to-month": "Monthly",
        "m2m": "Monthly",
        "annual": "Annual",
        "yearly": "Annual",
        "1 year": "Annual",
    }
    df["contract_mapped"] = df["contract_type"].str.lower().map(contract_map)
    mask = df["contract_mapped"].notna()
    summary["contract_type_dropped"] = len(df) - mask.sum()
    df = df[mask].copy()
    df = df.drop(columns=["contract_type"]).rename(columns={"contract_mapped": "contract_type"})

    # -----------------------------------------------------------------------
    # R6 – monthly_fee cleaning
    # -----------------------------------------------------------------------
    df["monthly_fee_clean"] = df["monthly_fee"].apply(clean_monthly_fee)
    mask = df["monthly_fee_clean"].notna() & (df["monthly_fee_clean"] > 0) & (df["monthly_fee_clean"] <= 500)
    summary["monthly_fee_dropped"] = len(df) - mask.sum()
    df = df[mask].copy()
    df = df.drop(columns=["monthly_fee"]).rename(columns={"monthly_fee_clean": "monthly_fee"})

    # -----------------------------------------------------------------------
    # R7 – tenure_months cleaning
    # -----------------------------------------------------------------------
    df["tenure_clean"] = df["tenure_months"].apply(clean_tenure)
    mask = df["tenure_clean"].notna() & (df["tenure_clean"] >= 0) & (df["tenure_clean"] <= 120)
    summary["tenure_months_dropped"] = len(df) - mask.sum()
    df = df[mask].copy()
    df = df.drop(columns=["tenure_months"]).rename(columns={"tenure_clean": "tenure_months"})

    # -----------------------------------------------------------------------
    # R8 – support_tickets cleaning (missing -> 0)
    # -----------------------------------------------------------------------
    df["support_clean"] = df["support_tickets"].apply(clean_support_tickets)
    mask = df["support_clean"].notna() & (df["support_clean"] >= 0) & (df["support_clean"] <= 100)
    summary["support_tickets_invalid"] = len(df) - mask.sum()
    df = df[mask].copy()
    df = df.drop(columns=["support_tickets"]).rename(columns={"support_clean": "support_tickets"})

    # -----------------------------------------------------------------------
    # R9 – satisfaction_score (invalid -> missing, keep row)
    # -----------------------------------------------------------------------
    df["satisfaction_clean"] = df["satisfaction_score"].apply(clean_satisfaction)
    summary["satisfaction_invalid"] = df["satisfaction_score"].notna().sum() - df["satisfaction_clean"].notna().sum()
    df = df.drop(columns=["satisfaction_score"]).rename(columns={"satisfaction_clean": "satisfaction_score"})

    # -----------------------------------------------------------------------
    # R10 – churned mapping
    # -----------------------------------------------------------------------
    churn_map = {
        "yes": 1,
        "y": 1,
        "true": 1,
        "1": 1,
        "churned": 1,
        "no": 0,
        "n": 0,
        "false": 0,
        "0": 0,
        "active": 0,
    }
    df["churned_mapped"] = df["churned"].str.lower().map(churn_map)
    mask = df["churned_mapped"].notna()
    summary["churned_dropped"] = len(df) - mask.sum()
    df = df[mask].copy()
    df = df.drop(columns=["churned"]).rename(columns={"churned_mapped": "churned"})

    # -----------------------------------------------------------------------
    # R11 – lifetime_value
    # -----------------------------------------------------------------------
    df["lifetime_value"] = (df["monthly_fee"] * df["tenure_months"]).round(2)

    # -----------------------------------------------------------------------
    # R12 – final column order, sorting, and output
    # -----------------------------------------------------------------------
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
        "lifetime_value",
    ]
    df = df[final_cols]
    df = df.sort_values(by="customer_id", ascending=True)

    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False, float_format='%.2f', na_rep='')

    # Prepare summary JSON
    summary["cleaned_rows"] = len(df)
    # Remove intermediate columns that are not needed in summary
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
