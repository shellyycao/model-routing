import json
import os
import re
from datetime import datetime

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

# R1: tokens treated as missing (case-insensitive, after stripping)
MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

# R3: exactly these signup_date formats
DATE_FORMATS = (
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY (e.g. 05-Mar-2024)
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY (e.g. March 5, 2024)
)

PLAN_MAP = {
    "basic": "Basic", "basic plan": "Basic",
    "standard": "Standard", "std": "Standard", "standard plan": "Standard",
    "premium": "Premium", "prem": "Premium", "premium plan": "Premium",
}

CONTRACT_MAP = {
    "monthly": "Monthly", "month-to-month": "Monthly", "m2m": "Monthly",
    "annual": "Annual", "yearly": "Annual", "1 year": "Annual",
}

CHURN_MAP = {
    "yes": 1, "y": 1, "true": 1, "1": 1, "churned": 1,
    "no": 0, "n": 0, "false": 0, "0": 0, "active": 0,
}


def normalize(value):
    """R1: strip whitespace; map missing tokens to None."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in MISSING_TOKENS:
        return None
    return text


def parse_date(value):
    if value is None:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_fee(value):
    if value is None:
        return None
    text = re.sub(r"usd", "", value, flags=re.IGNORECASE)
    text = text.replace("$", "").replace(",", "").strip()
    if text == "":
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if not np.isfinite(number) or number <= 0 or number > 500:
        return None
    return number


def parse_tenure(value):
    if value is None:
        return None
    text = re.sub(r"\s*months?\s*$", "", value, flags=re.IGNORECASE).strip()
    if text == "":
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if not np.isfinite(number) or not number.is_integer() or number < 0 or number > 120:
        return None
    return int(number)


def parse_tickets(value):
    # R8: missing means 0; invalid returns None (row dropped).
    if value is None:
        return 0
    try:
        number = float(value)
    except ValueError:
        return None
    if not np.isfinite(number) or not number.is_integer() or number < 0 or number > 100:
        return None
    return int(number)


def parse_satisfaction(value):
    # R9: invalid/missing -> None (kept as empty cell); valid -> int 1-5.
    if value is None:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    if not np.isfinite(number) or not number.is_integer() or number < 1 or number > 5:
        return None
    return int(number)


def main():
    raw_path = os.path.join(INPUT_DIR, "raw.csv")
    # R1: read every column as text, no automatic NA conversion.
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_filter=False)
    summary = {"raw_rows": int(len(df))}

    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        df[col] = df[col].map(normalize)

    # customer_id is not nullable in the output schema; rows without one cannot be used.
    summary["dropped_missing_customer_id"] = int(df["customer_id"].isna().sum())
    df = df[df["customer_id"].notna()]

    # R2: drop duplicate customer_id rows first, keeping raw-file order's first occurrence.
    before = len(df)
    df = df[~df["customer_id"].duplicated(keep="first")]
    summary["duplicates_removed"] = int(before - len(df))

    # R3: signup_date
    df["signup_date"] = df["signup_date"].map(parse_date)
    before = len(df)
    df = df[df["signup_date"].notna()]
    summary["dropped_bad_signup_date"] = int(before - len(df))

    # R4: plan
    df["plan"] = df["plan"].map(lambda v: PLAN_MAP.get(v.lower()) if v is not None else None)
    before = len(df)
    df = df[df["plan"].notna()]
    summary["dropped_bad_plan"] = int(before - len(df))

    # R5: contract_type
    df["contract_type"] = df["contract_type"].map(lambda v: CONTRACT_MAP.get(v.lower()) if v is not None else None)
    before = len(df)
    df = df[df["contract_type"].notna()]
    summary["dropped_bad_contract_type"] = int(before - len(df))

    # R6: monthly_fee
    df["monthly_fee"] = df["monthly_fee"].map(parse_fee)
    before = len(df)
    df = df[df["monthly_fee"].notna()]
    summary["dropped_bad_monthly_fee"] = int(before - len(df))
    df["monthly_fee"] = df["monthly_fee"].astype(float)

    # R7: tenure_months
    df["tenure_months"] = df["tenure_months"].map(parse_tenure)
    before = len(df)
    df = df[df["tenure_months"].notna()]
    summary["dropped_bad_tenure_months"] = int(before - len(df))
    df["tenure_months"] = df["tenure_months"].astype(int)

    # R8: support_tickets (missing -> 0)
    df["support_tickets"] = df["support_tickets"].map(parse_tickets)
    before = len(df)
    df = df[df["support_tickets"].notna()]
    summary["dropped_bad_support_tickets"] = int(before - len(df))
    df["support_tickets"] = df["support_tickets"].astype(int)

    # R9: satisfaction_score (invalid -> missing, keep row)
    had_value = df["satisfaction_score"].notna()
    df["satisfaction_score"] = df["satisfaction_score"].map(parse_satisfaction)
    summary["satisfaction_score_set_missing"] = int((had_value & df["satisfaction_score"].isna()).sum())

    # R10: churned
    df["churned"] = df["churned"].map(lambda v: CHURN_MAP.get(v.lower()) if v is not None else None)
    before = len(df)
    df = df[df["churned"].notna()]
    summary["dropped_bad_churned"] = int(before - len(df))
    df["churned"] = df["churned"].astype(int)

    # R11: lifetime_value
    df["lifetime_value"] = (df["monthly_fee"] * df["tenure_months"]).round(2)

    # R12: schema, ordering and output
    df["satisfaction_score"] = pd.array(list(df["satisfaction_score"]), dtype="Int64")
    df = df.sort_values("customer_id", kind="mergesort").reset_index(drop=True)
    out = df[[
        "customer_id", "signup_date", "plan", "contract_type", "monthly_fee",
        "tenure_months", "support_tickets", "satisfaction_score", "churned",
        "lifetime_value",
    ]]
    out.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)

    summary["cleaned_rows"] = int(len(out))
    with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
