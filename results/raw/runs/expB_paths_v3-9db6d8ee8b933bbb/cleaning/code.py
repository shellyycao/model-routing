import os
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

# ---------- Helper functions ----------

def is_missing(val):
    if pd.isna(val):
        return True
    if isinstance(val, str):
        return val.strip().lower() in {"", "na", "n/a", "null", "none", "-"}
    return False

def parse_date(val):
    if pd.isna(val):
        return None
    val = val.strip()
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            # For %b (abbr) make month abbreviation title case to match strptime expectations
            if "%b" in fmt:
                val_mod = re.sub(r"(\d{2})-([A-Za-z]{3})-(\d{4})",
                                 lambda m: f"{m.group(1)}-{m.group(2).title()}-{m.group(3)}",
                                 val)
            else:
                val_mod = val
            dt = datetime.strptime(val_mod, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return None

def map_plan(val):
    if pd.isna(val):
        return None
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
    return mapping.get(val.strip().lower())

def map_contract(val):
    if pd.isna(val):
        return None
    mapping = {
        "monthly": "Monthly",
        "month-to-month": "Monthly",
        "m2m": "Monthly",
        "annual": "Annual",
        "yearly": "Annual",
        "1 year": "Annual",
    }
    return mapping.get(val.strip().lower())

def clean_monthly_fee(val):
    if pd.isna(val):
        return np.nan
    # remove $ , USD and surrounding spaces
    cleaned = re.sub(r"\$|USD", "", str(val), flags=re.I)
    cleaned = cleaned.replace(",", "").strip()
    try:
        num = float(cleaned)
        if num <= 0 or num > 500:
            return np.nan
        return round(num, 2)
    except Exception:
        return np.nan

def clean_tenure(val):
    if pd.isna(val):
        return np.nan
    # remove trailing 'months' or 'month'
    cleaned = re.sub(r"\s*(months?|Months?)$", "", str(val)).strip()
    try:
        num = float(cleaned)
        if not num.is_integer():
            return np.nan
        num_int = int(num)
        if num_int < 0 or num_int > 120:
            return np.nan
        return num_int
    except Exception:
        return np.nan

def clean_support_tickets(val):
    if is_missing(val):
        return 0
    try:
        num = float(val)
        if not num.is_integer():
            return np.nan
        num_int = int(num)
        if num_int < 0 or num_int > 100:
            return np.nan
        return num_int
    except Exception:
        return np.nan

def clean_satisfaction(val):
    if is_missing(val):
        return np.nan
    try:
        num = float(val)
        if not num.is_integer():
            return np.nan
        num_int = int(num)
        if 1 <= num_int <= 5:
            return num_int
        else:
            return np.nan
    except Exception:
        return np.nan

def map_churned(val):
    if pd.isna(val):
        return None
    mapping = {
        "yes": 1, "y": 1, "true": 1, "1": 1, "churned": 1,
        "no": 0, "n": 0, "false": 0, "0": 0, "active": 0,
    }
    return mapping.get(val.strip().lower())

# ---------- Main cleaning workflow ----------

def main():
    input_dir = os.getenv("INPUT_DIR")
    output_dir = os.getenv("OUTPUT_DIR")
    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # 1. Read raw CSV as text, no NA conversion
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)

    # 2. Strip whitespace from every cell
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # 3. Convert defined missing tokens to NaN
    missing_tokens = {"", "na", "n/a", "null", "none", "-"}
    df = df.replace(to_replace=lambda v: isinstance(v, str) and v.strip().lower() in missing_tokens,
                    value=np.nan)

    # 4. Remove duplicate customer_id rows (keep first)
    before_dup = len(df)
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    dup_removed = before_dup - len(df)

    # Prepare counters for summary
    counters = {
        "duplicates_removed": dup_removed,
        "rows_dropped_signup_date": 0,
        "rows_dropped_plan": 0,
        "rows_dropped_contract_type": 0,
        "rows_dropped_monthly_fee": 0,
        "rows_dropped_tenure_months": 0,
        "rows_dropped_support_tickets": 0,
        "rows_dropped_churned": 0,
    }

    # 5. signup_date parsing
    df["signup_date_parsed"] = df["signup_date"].apply(parse_date)
    mask = df["signup_date_parsed"].notna()
    counters["rows_dropped_signup_date"] = (~mask).sum()
    df = df[mask]

    # 6. plan mapping
    df["plan_mapped"] = df["plan"].apply(map_plan)
    mask = df["plan_mapped"].notna()
    counters["rows_dropped_plan"] = (~mask).sum()
    df = df[mask]

    # 7. contract_type mapping
    df["contract_mapped"] = df["contract_type"].apply(map_contract)
    mask = df["contract_mapped"].notna()
    counters["rows_dropped_contract_type"] = (~mask).sum()
    df = df[mask]

    # 8. monthly_fee cleaning
    df["monthly_fee_clean"] = df["monthly_fee"].apply(clean_monthly_fee)
    mask = df["monthly_fee_clean"].notna()
    counters["rows_dropped_monthly_fee"] = (~mask).sum()
    df = df[mask]

    # 9. tenure_months cleaning
    df["tenure_clean"] = df["tenure_months"].apply(clean_tenure)
    mask = df["tenure_clean"].notna()
    counters["rows_dropped_tenure_months"] = (~mask).sum()
    df = df[mask]

    # 10. support_tickets cleaning
    df["support_clean"] = df["support_tickets"].apply(clean_support_tickets)
    mask = df["support_clean"].notna()
    counters["rows_dropped_support_tickets"] = (~mask).sum()
    df = df[mask]

    # 11. satisfaction_score cleaning (do NOT drop rows)
    df["satisfaction_clean"] = df["satisfaction_score"].apply(clean_satisfaction)

    # 12. churned mapping
    df["churned_mapped"] = df["churned"].apply(map_churned)
    mask = df["churned_mapped"].notna()
    counters["rows_dropped_churned"] = (~mask).sum()
    df = df[mask]

    # 13. Compute lifetime_value
    df["lifetime_value"] = (df["monthly_fee_clean"] * df["tenure_clean"]).round(2)

    # 14. Assemble final dataframe with required column order
    final_df = pd.DataFrame({
        "customer_id": df["customer_id"],
        "signup_date": df["signup_date_parsed"],
        "plan": df["plan_mapped"],
        "contract_type": df["contract_mapped"],
        "monthly_fee": df["monthly_fee_clean"],
        "tenure_months": df["tenure_clean"],
        "support_tickets": df["support_clean"],
        "satisfaction_score": df["satisfaction_clean"],
        "churned": df["churned_mapped"].astype(int),
        "lifetime_value": df["lifetime_value"],
    })

    # 15. Sort by customer_id ascending
    final_df = final_df.sort_values(by="customer_id").reset_index(drop=True)

    # 16. Write cleaned CSV
    final_df.to_csv(cleaned_path, index=False, na_rep="")

    # 17. Write cleaning summary JSON
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": len(final_df),
        **counters,
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
