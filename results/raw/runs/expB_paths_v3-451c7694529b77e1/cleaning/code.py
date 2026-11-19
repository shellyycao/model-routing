import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

# ── R1: Read everything as text, strip whitespace, normalise missing ──────────
raw_path = os.path.join(INPUT_DIR, "raw.csv")
df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
raw_rows = len(df)

# Strip whitespace from column names
df.columns = [c.strip() for c in df.columns]

# Strip whitespace from every cell
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# Treat these values as missing (case-insensitive after strip)
MISSING_VALS = {"", "na", "n/a", "null", "none", "-"}
def to_missing(val):
    if isinstance(val, str) and val.strip().lower() in MISSING_VALS:
        return np.nan
    return val

df = df.applymap(to_missing)

# ── R2: Remove duplicate customer_id rows (keep first) ───────────────────────
before_dedup = len(df)
df = df.drop_duplicates(subset=["customer_id"], keep="first")
duplicates_removed = before_dedup - len(df)

# ── R3: Parse signup_date ─────────────────────────────────────────────────────
DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d-%b-%Y",
    "%Y/%m/%d",
    "%B %d, %Y",
]

def parse_date(val):
    if pd.isna(val):
        return pd.NaT
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except ValueError:
            continue
    return pd.NaT

df["signup_date"] = df["signup_date"].apply(parse_date)
before = len(df)
df = df.dropna(subset=["signup_date"])
signup_date_dropped = before - len(df)
df["signup_date"] = df["signup_date"].apply(lambda d: d.strftime("%Y-%m-%d") if not pd.isna(d) else d)

# ── R4: Normalise plan ────────────────────────────────────────────────────────
PLAN_MAP = {
    "basic": "Basic",
    "basic plan": "Basic",
    "standard": "Standard",
    "std": "Standard",
    "standard plan": "Standard",
    "premium": "Premium",
    "prem": "Premium",
    "premium plan": "Premium",
}

def map_plan(val):
    if pd.isna(val):
        return np.nan
    return PLAN_MAP.get(str(val).strip().lower(), np.nan)

df["plan"] = df["plan"].apply(map_plan)
before = len(df)
df = df.dropna(subset=["plan"])
plan_dropped = before - len(df)

# ── R5: Normalise contract_type ───────────────────────────────────────────────
CONTRACT_MAP = {
    "monthly": "Monthly",
    "month-to-month": "Monthly",
    "m2m": "Monthly",
    "annual": "Annual",
    "yearly": "Annual",
    "1 year": "Annual",
}

def map_contract(val):
    if pd.isna(val):
        return np.nan
    return CONTRACT_MAP.get(str(val).strip().lower(), np.nan)

df["contract_type"] = df["contract_type"].apply(map_contract)
before = len(df)
df = df.dropna(subset=["contract_type"])
contract_dropped = before - len(df)

# ── R6: Parse monthly_fee ─────────────────────────────────────────────────────
def parse_fee(val):
    if pd.isna(val):
        return np.nan
    s = str(val).replace("$", "").replace("USD", "").replace(",", "").strip()
    try:
        v = float(s)
    except ValueError:
        return np.nan
    if v <= 0 or v > 500:
        return np.nan
    return v

df["monthly_fee"] = df["monthly_fee"].apply(parse_fee)
before = len(df)
df = df.dropna(subset=["monthly_fee"])
fee_dropped = before - len(df)

# ── R7: Parse tenure_months ───────────────────────────────────────────────────
import re

def parse_tenure(val):
    if pd.isna(val):
        return np.nan
    s = re.sub(r'(?i)\s*months?\s*$', '', str(val).strip()).strip()
    try:
        v = float(s)
    except ValueError:
        return np.nan
    if v != int(v) or v < 0 or v > 120:
        return np.nan
    return int(v)

df["tenure_months"] = df["tenure_months"].apply(parse_tenure)
before = len(df)
df = df.dropna(subset=["tenure_months"])
tenure_dropped = before - len(df)
df["tenure_months"] = df["tenure_months"].astype(int)

# ── R8: Parse support_tickets ─────────────────────────────────────────────────
def parse_tickets(val):
    if pd.isna(val):
        return 0  # missing -> 0
    try:
        v = float(str(val).strip())
    except ValueError:
        return np.nan
    if v != int(v) or v < 0 or v > 100:
        return np.nan
    return int(v)

df["support_tickets"] = df["support_tickets"].apply(parse_tickets)
before = len(df)
df = df.dropna(subset=["support_tickets"])
tickets_dropped = before - len(df)
df["support_tickets"] = df["support_tickets"].astype(int)

# ── R9: Parse satisfaction_score (nullable) ───────────────────────────────────
def parse_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        v = float(str(val).strip())
    except ValueError:
        return np.nan
    if v != int(v) or v < 1 or v > 5:
        return np.nan
    return int(v)

df["satisfaction_score"] = df["satisfaction_score"].apply(parse_satisfaction)
# Rows are KEPT even if satisfaction_score is NaN

# ── R10: Parse churned ────────────────────────────────────────────────────────
CHURNED_MAP = {
    "yes": 1, "y": 1, "true": 1, "1": 1, "churned": 1,
    "no": 0, "n": 0, "false": 0, "0": 0, "active": 0,
}

def map_churned(val):
    if pd.isna(val):
        return np.nan
    return CHURNED_MAP.get(str(val).strip().lower(), np.nan)

df["churned"] = df["churned"].apply(map_churned)
before = len(df)
df = df.dropna(subset=["churned"])
churned_dropped = before - len(df)
df["churned"] = df["churned"].astype(int)

# ── R11: Add lifetime_value ───────────────────────────────────────────────────
df["lifetime_value"] = (df["monthly_fee"] * df["tenure_months"]).round(2)

# ── R12: Select columns, sort, write ─────────────────────────────────────────
COLUMNS = [
    "customer_id", "signup_date", "plan", "contract_type",
    "monthly_fee", "tenure_months", "support_tickets",
    "satisfaction_score", "churned", "lifetime_value",
]
df = df[COLUMNS]
df = df.sort_values("customer_id", ascending=True)

cleaned_rows = len(df)

# Write cleaned CSV
out_csv = os.path.join(OUTPUT_DIR, "cleaned.csv")
df.to_csv(out_csv, index=False, na_rep="")

# Write cleaning summary
summary = {
    "raw_rows": raw_rows,
    "cleaned_rows": cleaned_rows,
    "duplicates_removed": duplicates_removed,
    "signup_date_dropped": signup_date_dropped,
    "plan_dropped": plan_dropped,
    "contract_type_dropped": contract_dropped,
    "monthly_fee_dropped": fee_dropped,
    "tenure_months_dropped": tenure_dropped,
    "support_tickets_dropped": tickets_dropped,
    "churned_dropped": churned_dropped,
    "total_rows_dropped": raw_rows - cleaned_rows,
}
out_json = os.path.join(OUTPUT_DIR, "cleaning_summary.json")
with open(out_json, "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_rows} raw rows -> {cleaned_rows} cleaned rows.")
