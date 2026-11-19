import os
import re
import json
from datetime import date

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

RAW_PATH = os.path.join(INPUT_DIR, "raw.csv")
CLEANED_PATH = os.path.join(OUTPUT_DIR, "cleaned.csv")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "cleaning_summary.json")

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

EXPECTED_COLUMNS = [
    "customer_id", "signup_date", "plan", "contract_type", "monthly_fee",
    "tenure_months", "support_tickets", "satisfaction_score", "churned",
]

MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

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


def safe_date(y, m, d):
    try:
        return date(y, m, d).isoformat()
    except ValueError:
        return None


def parse_signup_date(s):
    if s is None:
        return None
    s = str(s).strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)  # YYYY-MM-DD
    if m:
        return safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)  # MM/DD/YYYY
    if m:
        return safe_date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
    m = re.fullmatch(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", s)  # DD-Mon-YYYY
    if m:
        mon = MONTHS.get(m.group(2).lower())
        if mon is None:
            return None
        return safe_date(int(m.group(3)), mon, int(m.group(1)))
    m = re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", s)  # YYYY/MM/DD
    if m:
        return safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", s)  # Month D, YYYY
    if m:
        mon = MONTHS.get(m.group(1).lower())
        if mon is None:
            return None
        return safe_date(int(m.group(3)), mon, int(m.group(2)))
    return None


def clean_money(s):
    if s is None:
        return np.nan
    t = re.sub(r"usd", "", str(s), flags=re.IGNORECASE)
    t = t.replace("$", "").replace(",", "").strip()
    if t == "":
        return np.nan
    try:
        v = float(t)
    except ValueError:
        return np.nan
    if not np.isfinite(v) or v <= 0 or v > 500:
        return np.nan
    return v


def clean_tenure(s):
    if s is None:
        return None
    t = re.sub(r"\s*months?\s*$", "", str(s), flags=re.IGNORECASE).strip()
    if t == "":
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    if not np.isfinite(v) or not v.is_integer() or v < 0 or v > 120:
        return None
    return int(v)


def clean_tickets(s):
    if s is None:
        return 0
    try:
        v = float(str(s).strip())
    except ValueError:
        return None
    if not np.isfinite(v) or not v.is_integer() or v < 0 or v > 100:
        return None
    return int(v)


def clean_satisfaction(s):
    if s is None:
        return pd.NA
    try:
        v = float(str(s).strip())
    except ValueError:
        return pd.NA
    if not np.isfinite(v) or not v.is_integer() or v < 1 or v > 5:
        return pd.NA
    return int(v)


def drop_invalid(df, col):
    before = len(df)
    df = df[df[col].notna()].copy()
    return df, before - len(df)


def main():
    # R1: read everything as text, strip whitespace, normalise missing tokens.
    raw = pd.read_csv(RAW_PATH, dtype=str, keep_default_na=False, na_filter=False)
    raw_rows = int(len(raw))
    raw.columns = [str(c).strip() for c in raw.columns]
    df = raw.copy()
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[EXPECTED_COLUMNS]
    for col in EXPECTED_COLUMNS:
        df[col] = df[col].map(
            lambda v: None if v is None or str(v).strip().lower() in MISSING_TOKENS
            else str(v).strip()
        )

    summary = {"raw_rows": raw_rows}

    # R2: drop rows with missing customer_id, then duplicate customer_id (keep first in raw order).
    before = len(df)
    df = df[df["customer_id"].notna()].copy()
    summary["dropped_missing_customer_id"] = int(before - len(df))
    before = len(df)
    df = df[~df["customer_id"].duplicated(keep="first")].copy()
    summary["duplicates_removed"] = int(before - len(df))

    # R3: signup_date -> YYYY-MM-DD, drop unparseable/missing.
    df["signup_date"] = df["signup_date"].map(parse_signup_date)
    df, n = drop_invalid(df, "signup_date")
    summary["dropped_invalid_signup_date"] = int(n)

    # R4: plan normalisation.
    df["plan"] = df["plan"].map(lambda s: PLAN_MAP.get(str(s).lower()) if s is not None else None)
    df, n = drop_invalid(df, "plan")
    summary["dropped_invalid_plan"] = int(n)

    # R5: contract_type normalisation.
    df["contract_type"] = df["contract_type"].map(
        lambda s: CONTRACT_MAP.get(str(s).lower()) if s is not None else None
    )
    df, n = drop_invalid(df, "contract_type")
    summary["dropped_invalid_contract_type"] = int(n)

    # R6: monthly_fee -> float in (0, 500].
    df["monthly_fee"] = df["monthly_fee"].map(clean_money)
    df, n = drop_invalid(df, "monthly_fee")
    summary["dropped_invalid_monthly_fee"] = int(n)

    # R7: tenure_months -> int in [0, 120].
    df["tenure_months"] = df["tenure_months"].map(clean_tenure)
    df, n = drop_invalid(df, "tenure_months")
    summary["dropped_invalid_tenure_months"] = int(n)

    # R8: support_tickets -> int in [0, 100]; missing means 0.
    df["support_tickets"] = df["support_tickets"].map(clean_tickets)
    df, n = drop_invalid(df, "support_tickets")
    summary["dropped_invalid_support_tickets"] = int(n)

    # R9: satisfaction_score -> int 1-5 or missing (row kept).
    df["satisfaction_score"] = df["satisfaction_score"].map(clean_satisfaction)
    summary["satisfaction_score_set_missing"] = int(df["satisfaction_score"].isna().sum())

    # R10: churned -> 0/1, drop unmappable/missing.
    df["churned"] = df["churned"].map(
        lambda s: CHURN_MAP.get(str(s).lower()) if s is not None else None
    )
    df, n = drop_invalid(df, "churned")
    summary["dropped_invalid_churned"] = int(n)

    # R11: lifetime_value.
    df["lifetime_value"] = (df["monthly_fee"].astype(float) * df["tenure_months"].astype(int)).round(2)

    # Final dtypes.
    df["customer_id"] = df["customer_id"].astype(str)
    df["tenure_months"] = df["tenure_months"].astype(int)
    df["support_tickets"] = df["support_tickets"].astype(int)
    df["satisfaction_score"] = df["satisfaction_score"].astype("Int64")
    df["churned"] = df["churned"].astype(int)
    df["monthly_fee"] = df["monthly_fee"].astype(float)

    # R12: column order, sort by customer_id, write CSV without index.
    out_cols = [
        "customer_id", "signup_date", "plan", "contract_type", "monthly_fee",
        "tenure_months", "support_tickets", "satisfaction_score", "churned",
        "lifetime_value",
    ]
    df = df[out_cols].sort_values("customer_id", kind="mergesort").reset_index(drop=True)
    df.to_csv(CLEANED_PATH, index=False)

    summary["cleaned_rows"] = int(len(df))
    summary["rows_dropped_total"] = int(raw_rows - len(df))
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"cleaned.csv written: {len(df)} rows (raw: {raw_rows})")


if __name__ == "__main__":
    main()
