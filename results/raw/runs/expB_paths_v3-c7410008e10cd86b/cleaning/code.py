import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def clean_missing(val):
    """Strip whitespace and convert defined missing tokens to NaN."""
    if isinstance(val, str):
        val = val.strip()
        if val.lower() in {'', 'na', 'n/a', 'null', 'none', '-'}:
            return np.nan
        return val
    return val

def parse_date(val):
    """Try the allowed date formats, return ISO string or None."""
    if pd.isna(val):
        return None
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return None

def map_value(val, mapping):
    if pd.isna(val):
        return None
    return mapping.get(val.strip().lower())

def parse_number(val, allow_float=True):
    if pd.isna(val):
        return None
    try:
        if allow_float:
            num = float(val)
        else:
            if '.' in val:
                return None
            num = int(val)
        return num
    except Exception:
        return None

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

    # Read everything as text, no automatic NA handling
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_values=[])
    raw_rows = len(df)

    # ---------------------------------------------------------------------
    # R1 – strip whitespace and normalise missing values
    # ---------------------------------------------------------------------
    df = df.applymap(clean_missing)

    # ---------------------------------------------------------------------
    # R2 – deduplicate on customer_id (keep first)
    # ---------------------------------------------------------------------
    before_dup = len(df)
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    dup_removed = before_dup - len(df)

    # Prepare summary dict
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": None,
        "duplicates_removed": dup_removed,
        "rows_dropped_signup_date": 0,
        "rows_dropped_plan": 0,
        "rows_dropped_contract_type": 0,
        "rows_dropped_monthly_fee": 0,
        "rows_dropped_tenure_months": 0,
        "rows_dropped_support_tickets": 0,
        "rows_dropped_churned": 0
    }

    # ---------------------------------------------------------------------
    # R3 – signup_date parsing
    # ---------------------------------------------------------------------
    df["signup_date_parsed"] = df["signup_date"].apply(parse_date)
    before = len(df)
    df = df[~df["signup_date_parsed"].isna()]
    summary["rows_dropped_signup_date"] = before - len(df)
    df = df.drop(columns=["signup_date"]).rename(columns={"signup_date_parsed": "signup_date"})

    # ---------------------------------------------------------------------
    # R4 – plan mapping
    # ---------------------------------------------------------------------
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
    df["plan_mapped"] = df["plan"].apply(lambda v: map_value(v, plan_map))
    before = len(df)
    df = df[~df["plan_mapped"].isna()]
    summary["rows_dropped_plan"] = before - len(df)
    df = df.drop(columns=["plan"]).rename(columns={"plan_mapped": "plan"})

    # ---------------------------------------------------------------------
    # R5 – contract_type mapping
    # ---------------------------------------------------------------------
    contract_map = {
        "monthly": "Monthly",
        "month-to-month": "Monthly",
        "m2m": "Monthly",
        "annual": "Annual",
        "yearly": "Annual",
        "1 year": "Annual"
    }
    df["contract_mapped"] = df["contract_type"].apply(lambda v: map_value(v, contract_map))
    before = len(df)
    df = df[~df["contract_mapped"].isna()]
    summary["rows_dropped_contract_type"] = before - len(df)
    df = df.drop(columns=["contract_type"]).rename(columns={"contract_mapped": "contract_type"})

    # ---------------------------------------------------------------------
    # R6 – monthly_fee cleaning
    # ---------------------------------------------------------------------
    def clean_fee(val):
        if pd.isna(val):
            return None
        # remove $ , USD and spaces
        cleaned = val.replace('$', '').replace('USD', '').replace(',', '').strip()
        return parse_number(cleaned, allow_float=True)
    df["monthly_fee_num"] = df["monthly_fee"].apply(clean_fee)
    before = len(df)
    df = df[~df["monthly_fee_num"].isna()]
    df = df[(df["monthly_fee_num"] > 0) & (df["monthly_fee_num"] <= 500)]
    summary["rows_dropped_monthly_fee"] = before - len(df)
    df = df.drop(columns=["monthly_fee"]).rename(columns={"monthly_fee_num": "monthly_fee"})

    # ---------------------------------------------------------------------
    # R7 – tenure_months cleaning
    # ---------------------------------------------------------------------
    def clean_tenure(val):
        if pd.isna(val):
            return None
        lowered = val.lower().replace('months', '').replace('month', '').strip()
        return parse_number(lowered, allow_float=False)
    df["tenure_num"] = df["tenure_months"].apply(clean_tenure)
    before = len(df)
    df = df[~df["tenure_num"].isna()]
    df = df[(df["tenure_num"] >= 0) & (df["tenure_num"] <= 120)]
    summary["rows_dropped_tenure_months"] = before - len(df)
    df = df.drop(columns=["tenure_months"]).rename(columns={"tenure_num": "tenure_months"})
    df["tenure_months"] = df["tenure_months"].astype(int)

    # ---------------------------------------------------------------------
    # R8 – support_tickets cleaning (missing -> 0)
    # ---------------------------------------------------------------------
    def clean_tickets(val):
        if pd.isna(val):
            return 0
        num = parse_number(val, allow_float=False)
        if num is None:
            return None
        return num
    df["tickets_num"] = df["support_tickets"].apply(clean_tickets)
    before = len(df)
    df = df[~df["tickets_num"].isna()]
    df = df[(df["tickets_num"] >= 0) & (df["tickets_num"] <= 100)]
    summary["rows_dropped_support_tickets"] = before - len(df)
    df = df.drop(columns=["support_tickets"]).rename(columns={"tickets_num": "support_tickets"})
    df["support_tickets"] = df["support_tickets"].astype(int)

    # ---------------------------------------------------------------------
    # R9 – satisfaction_score (invalid -> missing, keep row)
    # ---------------------------------------------------------------------
    def clean_sat(val):
        if pd.isna(val):
            return np.nan
        num = parse_number(val, allow_float=False)
        if num is None or not (1 <= num <= 5):
            return np.nan
        return int(num)
    df["satisfaction_score"] = df["satisfaction_score"].apply(clean_sat)

    # ---------------------------------------------------------------------
    # R10 – churned mapping
    # ---------------------------------------------------------------------
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
        "active": 0
    }
    df["churned_mapped"] = df["churned"].apply(lambda v: map_value(v, churn_map))
    before = len(df)
    df = df[~df["churned_mapped"].isna()]
    summary["rows_dropped_churned"] = before - len(df)
    df = df.drop(columns=["churned"]).rename(columns={"churned_mapped": "churned"})
    df["churned"] = df["churned"].astype(int)

    # ---------------------------------------------------------------------
    # R11 – lifetime_value
    # ---------------------------------------------------------------------
    df["lifetime_value"] = (df["monthly_fee"] * df["tenure_months"]).round(2)

    # ---------------------------------------------------------------------
    # R12 – final column order, sort, write CSV
    # ---------------------------------------------------------------------
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

    # Ensure correct dtypes for output (float without thousands separators)
    df["monthly_fee"] = df["monthly_fee"].astype(float)
    df["lifetime_value"] = df["lifetime_value"].astype(float)

    df.to_csv(cleaned_path, index=False, float_format='%.2f', na_rep='')

    summary["cleaned_rows"] = len(df)
    # write summary JSON
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
