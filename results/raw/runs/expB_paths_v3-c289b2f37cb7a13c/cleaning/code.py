import os
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions for parsing and validation
# ---------------------------------------------------------------------------

def parse_date(value):
    """Parse date according to the allowed formats. Return string YYYY-MM-DD or None."""
    if pd.isna(value):
        return None
    value = value.strip()
    date_formats = [
        "%Y-%m-%d",          # 2021-01-01
        "%m/%d/%Y",          # 01/21/2021
        "%d-%b-%Y",          # 07-Jan-2021 (abbr month)
        "%Y/%m/%d",          # 2021/01/07
        "%B %d, %Y"          # March 5, 2024
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def map_plan(value):
    if pd.isna(value):
        return None
    v = value.strip().lower()
    mapping = {
        "basic": "Basic",
        "basic plan": "Basic",
        "standard": "Standard",
        "std": "Standard",
        "standard plan": "Standard",
        "premium": "Premium",
        "prem": "Premium",
        "premium plan": "Premium"
    }
    return mapping.get(v)

def map_contract(value):
    if pd.isna(value):
        return None
    v = value.strip().lower()
    mapping = {
        "monthly": "Monthly",
        "month-to-month": "Monthly",
        "m2m": "Monthly",
        "annual": "Annual",
        "yearly": "Annual",
        "1 year": "Annual"
    }
    return mapping.get(v)

def parse_monthly_fee(value):
    if pd.isna(value):
        return None
    v = value.strip()
    # Remove $ , USD (case‑insensitive) and commas
    v = re.sub(r"\$", "", v)
    v = re.sub(r"USD", "", v, flags=re.IGNORECASE)
    v = v.replace(",", "")
    v = v.strip()
    try:
        num = float(v)
        if num <= 0 or num > 500:
            return None
        return round(num, 2)
    except ValueError:
        return None

def parse_tenure(value):
    if pd.isna(value):
        return None
    v = value.strip()
    # Remove trailing "month" or "months" (case‑insensitive)
    v = re.sub(r"(?i)\s*months?$", "", v).strip()
    if not v.isdigit():
        return None
    num = int(v)
    if num < 0 or num > 120:
        return None
    return num

def parse_support_tickets(value):
    if pd.isna(value):
        return 0
    v = str(value).strip()
    if not v.isdigit():
        return None
    num = int(v)
    if num < 0 or num > 100:
        return None
    return num

def parse_satisfaction(value):
    if pd.isna(value):
        return np.nan
    v = str(value).strip()
    if not v.isdigit():
        return np.nan
    num = int(v)
    if 1 <= num <= 5:
        return num
    return np.nan

def map_churned(value):
    if pd.isna(value):
        return None
    v = value.strip().lower()
    yes_set = {"yes", "y", "true", "1", "churned"}
    no_set = {"no", "n", "false", "0", "active"}
    if v in yes_set:
        return 1
    if v in no_set:
        return 0
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

    # R1 – read everything as text, strip whitespace, treat defined tokens as missing
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_values=[])
    raw_rows = len(df)

    # Strip whitespace from every cell
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # Define missing tokens (case‑insensitive)
    missing_tokens = {"", "na", "n/a", "null", "none", "-"}
    df = df.replace(to_replace=missing_tokens, value=np.nan)

    # R2 – drop duplicate customer_id, keep first
    before_dup = len(df)
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    dup_removed = before_dup - len(df)

    # Counters for each rule that leads to row removal
    counters = {
        "signup_date_invalid": 0,
        "plan_invalid": 0,
        "contract_type_invalid": 0,
        "monthly_fee_invalid": 0,
        "tenure_months_invalid": 0,
        "support_tickets_invalid": 0,
        "churned_invalid": 0
    }

    cleaned_rows = []
    for _, row in df.iterrows():
        # ---- R3 signup_date ----
        signup = parse_date(row.get("signup_date"))
        if signup is None:
            counters["signup_date_invalid"] += 1
            continue

        # ---- R4 plan ----
        plan = map_plan(row.get("plan"))
        if plan is None:
            counters["plan_invalid"] += 1
            continue

        # ---- R5 contract_type ----
        contract = map_contract(row.get("contract_type"))
        if contract is None:
            counters["contract_type_invalid"] += 1
            continue

        # ---- R6 monthly_fee ----
        fee = parse_monthly_fee(row.get("monthly_fee"))
        if fee is None:
            counters["monthly_fee_invalid"] += 1
            continue

        # ---- R7 tenure_months ----
        tenure = parse_tenure(row.get("tenure_months"))
        if tenure is None:
            counters["tenure_months_invalid"] += 1
            continue

        # ---- R8 support_tickets ----
        tickets = parse_support_tickets(row.get("support_tickets"))
        if tickets is None:
            counters["support_tickets_invalid"] += 1
            continue

        # ---- R9 satisfaction_score ----
        satisfaction = parse_satisfaction(row.get("satisfaction_score"))
        # keep row even if satisfaction is NaN (empty cell)

        # ---- R10 churned ----
        churn = map_churned(row.get("churned"))
        if churn is None:
            counters["churned_invalid"] += 1
            continue

        # ---- R11 lifetime_value ----
        lifetime = round(fee * tenure, 2)

        cleaned_rows.append({
            "customer_id": row.get("customer_id"),
            "signup_date": signup,
            "plan": plan,
            "contract_type": contract,
            "monthly_fee": fee,
            "tenure_months": tenure,
            "support_tickets": tickets,
            "satisfaction_score": satisfaction,
            "churned": churn,
            "lifetime_value": lifetime
        })

    cleaned_df = pd.DataFrame(cleaned_rows, columns=[
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
    ])

    # R12 – sort by customer_id ascending and write CSV
    cleaned_df = cleaned_df.sort_values(by="customer_id", ascending=True)
    cleaned_df.to_csv(cleaned_path, index=False, float_format='%.2f')

    # Build summary JSON
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": len(cleaned_df),
        "duplicates_removed": dup_removed,
        "rows_dropped": counters
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
