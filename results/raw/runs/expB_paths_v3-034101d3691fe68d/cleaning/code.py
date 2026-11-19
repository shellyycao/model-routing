import os
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

# ---------- Helper functions ----------

def normalize_missing(val):
    """Strip whitespace and convert defined missing tokens to NaN."""
    if isinstance(val, str):
        val = val.strip()
        if val.lower() in {"", "na", "n/a", "null", "none", "-"}:
            return np.nan
        return val
    return val

def parse_signup_date(val):
    if pd.isna(val):
        return None
    date_str = val.strip()
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return None

def map_plan(val):
    if pd.isna(val):
        return None
    key = val.strip().lower()
    mapping = {
        "basic": "Basic",
        "basic plan": "Basic",
        "standard": "Standard",
        "std": "Standard",
        "standard plan": "Standard",
        "premium": "Premium",
        "prem": "Premium",
        "premium plan": "Premium",
    }
    return mapping.get(key)

def map_contract(val):
    if pd.isna(val):
        return None
    key = val.strip().lower()
    mapping = {
        "monthly": "Monthly",
        "month-to-month": "Monthly",
        "m2m": "Monthly",
        "annual": "Annual",
        "yearly": "Annual",
        "1 year": "Annual",
    }
    return mapping.get(key)

def clean_monthly_fee(val):
    if pd.isna(val):
        return None
    # Remove $ , USD and surrounding spaces
    cleaned = re.sub(r"\$|USD", "", val, flags=re.IGNORECASE)
    cleaned = cleaned.replace(",", "")
    cleaned = cleaned.strip()
    if cleaned == "":
        return None
    try:
        num = float(cleaned)
        return num
    except Exception:
        return None

def clean_tenure(val):
    if pd.isna(val):
        return None
    # Remove trailing 'month' or 'months'
    cleaned = re.sub(r"(?i)\s*months?\s*$", "", val).strip()
    if cleaned == "":
        return None
    try:
        num = float(cleaned)
        if not num.is_integer():
            return None
        return int(num)
    except Exception:
        return None

def clean_support_tickets(val):
    if pd.isna(val):
        return 0
    try:
        num = float(val)
        if not num.is_integer():
            return None
        return int(num)
    except Exception:
        return None

def clean_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        num = float(val)
        if not num.is_integer():
            return np.nan
        iv = int(num)
        if 1 <= iv <= 5:
            return iv
        else:
            return np.nan
    except Exception:
        return np.nan

def map_churned(val):
    if pd.isna(val):
        return None
    key = val.strip().lower()
    mapping = {
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
    return mapping.get(key)

# ---------- Main cleaning workflow ----------

def main():
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("INPUT_DIR and OUTPUT_DIR environment variables must be set")

    raw_path = os.path.join(input_dir, "raw.csv")
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    summary = {}
    summary["raw_rows"] = len(df)

    # R1: strip whitespace and normalize missing values
    df = df.applymap(normalize_missing)

    # R2: remove duplicate customer_id, keep first
    before_dup = len(df)
    df = df.drop_duplicates(subset="customer_id", keep="first")
    summary["duplicates_removed"] = before_dup - len(df)
    summary["rows_after_R2"] = len(df)

    # R3: signup_date parsing
    before = len(df)
    df["signup_date_parsed"] = df["signup_date"].apply(parse_signup_date)
    df = df.dropna(subset=["signup_date_parsed"]).copy()
    df["signup_date"] = df["signup_date_parsed"]
    df = df.drop(columns=["signup_date_parsed"])  # keep original column name
    summary["rows_dropped_R3"] = before - len(df)

    # R4: plan mapping
    before = len(df)
    df["plan_mapped"] = df["plan"].apply(map_plan)
    df = df.dropna(subset=["plan_mapped"]).copy()
    df["plan"] = df["plan_mapped"]
    df = df.drop(columns=["plan_mapped"])
    summary["rows_dropped_R4"] = before - len(df)

    # R5: contract_type mapping
    before = len(df)
    df["contract_mapped"] = df["contract_type"].apply(map_contract)
    df = df.dropna(subset=["contract_mapped"]).copy()
    df["contract_type"] = df["contract_mapped"]
    df = df.drop(columns=["contract_mapped"])
    summary["rows_dropped_R5"] = before - len(df)

    # R6: monthly_fee cleaning and validation
    before = len(df)
    df["monthly_fee_clean"] = df["monthly_fee"].apply(clean_monthly_fee)
    df = df.dropna(subset=["monthly_fee_clean"]).copy()
    df = df[(df["monthly_fee_clean"] > 0) & (df["monthly_fee_clean"] <= 500)]
    summary["rows_dropped_R6"] = before - len(df)
    df["monthly_fee"] = df["monthly_fee_clean"]
    df = df.drop(columns=["monthly_fee_clean"])

    # R7: tenure_months cleaning and validation
    before = len(df)
    df["tenure_clean"] = df["tenure_months"].apply(clean_tenure)
    df = df.dropna(subset=["tenure_clean"]).copy()
    df = df[(df["tenure_clean"] >= 0) & (df["tenure_clean"] <= 120)]
    summary["rows_dropped_R7"] = before - len(df)
    df["tenure_months"] = df["tenure_clean"].astype(int)
    df = df.drop(columns=["tenure_clean"])

    # R8: support_tickets cleaning and validation
    before = len(df)
    df["support_clean"] = df["support_tickets"].apply(clean_support_tickets)
    df = df.dropna(subset=["support_clean"]).copy()
    df = df[(df["support_clean"] >= 0) & (df["support_clean"] <= 100)]
    summary["rows_dropped_R8"] = before - len(df)
    df["support_tickets"] = df["support_clean"].astype(int)
    df = df.drop(columns=["support_clean"])

    # R9: satisfaction_score – keep row, set to NaN if invalid
    df["satisfaction_score"] = df["satisfaction_score"].apply(clean_satisfaction)
    # No rows dropped, but we can note how many became missing
    summary["satisfaction_missing"] = int(df["satisfaction_score"].isna().sum())

    # R10: churned mapping
    before = len(df)
    df["churned_mapped"] = df["churned"].apply(map_churned)
    df = df.dropna(subset=["churned_mapped"]).copy()
    summary["rows_dropped_R10"] = before - len(df)
    df["churned"] = df["churned_mapped"].astype(int)
    df = df.drop(columns=["churned_mapped"])

    # R11: lifetime_value
    df["lifetime_value"] = (df["monthly_fee"] * df["tenure_months"]).round(2)

    # R12: final column order and sorting
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
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(cleaned_path, index=False, na_rep="")

    # Summary JSON
    summary["cleaned_rows"] = len(df)
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
