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

# Treat these values as missing (case-insensitive)
MISSING_VALS = {"", "na", "n/a", "null", "none", "-"}
def to_missing(val):
    if isinstance(val, str) and val.strip().lower() in MISSING_VALS:
        return np.nan
    return val

df = df.applymap(to_missing)

# ── R2: Deduplicate on customer_id (keep first) ───────────────────────────────
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
before_date = len(df)
df = df.dropna(subset=["signup_date"])
date_dropped = before_date - len(df)
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
before_plan = len(df)
df = df.dropna(subset=["plan"])
plan_dropped = before_plan - len(df)

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
before_contract = len(df)
df = df.dropna(subset=["contract_type"])
contract_dropped = before_contract - len(df)

# ── R6: Parse monthly_fee ─────────────────────────────────────────────────────
def parse_fee(val):
    if pd.isna(val):
        return np.nan
    s = str(val).replace("$", "").replace("USD", "").replace(",", "").strip()
    try:
        f = float(s)
    except ValueError:
        return np.nan
    if f <= 0 or f > 500:
        return np.nan
    return f

df["monthly_fee"] = df["monthly_fee"].apply(parse_fee)
before_fee = len(df)
df = df.dropna(subset=["monthly_fee"])
fee_dropped = before_fee - len(df)

# ── R7: Parse tenure_months ───────────────────────────────────────────────────
import re

def parse_tenure(val):
    if pd.isna(val):
        return np.nan
    s = re.sub(r'(?i)\s*months?\s*$', '', str(val).strip()).strip()
    try:
        f = float(s)
    except ValueError:
        return np.nan
    if f != int(f):
        return np.nan
    i = int(f)
    if i < 0 or i > 120:
        return np.nan
    return i

df["tenure_months"] = df["tenure_months"].apply(parse_tenure)
before_tenure = len(df)
df = df.dropna(subset=["tenure_months"])
tenure_dropped = before_tenure - len(df)
df["tenure_months"] = df["tenure_months"].astype(int)

# ── R8: Parse support_tickets ─────────────────────────────────────────────────
def parse_tickets(val):
    if pd.isna(val):
        return 0
    try:
        f = float(str(val).strip())
    except ValueError:
        return np.nan
    if f != int(f):
        return np.nan
    i = int(f)
    if i < 0 or i > 100:
        return np.nan
    return i

df["support_tickets"] = df["support_tickets"].apply(parse_tickets)
before_tickets = len(df)
df = df.dropna(subset=["support_tickets"])
tickets_dropped = before_tickets - len(df)
df["support_tickets"] = df["support_tickets"].astype(int)

# ── R9: Parse satisfaction_score (nullable) ───────────────────────────────────
def parse_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        f = float(str(val).strip())
    except ValueError:
        return np.nan
    if f != int(f):
        return np.nan
    i = int(f)
    if i < 1 or i > 5:
        return np.nan
    return i

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
before_churned = len(df)
df = df.dropna(subset=["churned"])
churned_dropped = before_churned - len(df)
df["churned"] = df["churned"].astype(int)

# ── R11: Add lifetime_value ───────────────────────────────────────────────────
df["lifetime_value"] = (df["monthly_fee"] * df["tenure_months"]).round(2)

# ── R12: Select, order, sort columns ─────────────────────────────────────────
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
# satisfaction_score: write as integer where present, empty where NaN
df["satisfaction_score"] = df["satisfaction_score"].apply(
    lambda x: int(x) if not pd.isna(x) else ""
)
df.to_csv(out_csv, index=False)

# Write cleaning summary
summary = {
    "raw_rows": raw_rows,
    "cleaned_rows": cleaned_rows,
    "duplicates_removed": duplicates_removed,
    "dropped_bad_signup_date": date_dropped,
    "dropped_bad_plan": plan_dropped,
    "dropped_bad_contract_type": contract_dropped,
    "dropped_bad_monthly_fee": fee_dropped,
    "dropped_bad_tenure_months": tenure_dropped,
    "dropped_bad_support_tickets": tickets_dropped,
    "dropped_bad_churned": churned_dropped,
    "total_rows_dropped": raw_rows - cleaned_rows,
}
summary_path = os.path.join(OUTPUT_DIR, "cleaning_summary.json")
with open(summary_path, "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_rows} raw rows -> {cleaned_rows} cleaned rows.")
print(f"Summary written to {summary_path}")
