"""Cleaning stage for the customer_churn project.

Reads raw.csv from INPUT_DIR, applies cleaning rules R1-R12 in order, and
writes cleaned.csv plus cleaning_summary.json to OUTPUT_DIR.
"""

import json
import math
import os
import re
from datetime import datetime

import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}


def normalize_text(value):
    """R1: strip whitespace; map missing tokens (case-insensitive) to None."""
    if value is None:
        return None
    text = str(value).strip()
    return None if text.lower() in MISSING_TOKENS else text


# ---------------------------------------------------------------------------
# R1: read every column as text, strip whitespace, normalise missing values.
# ---------------------------------------------------------------------------
raw = pd.read_csv(
    os.path.join(INPUT_DIR, "raw.csv"),
    dtype=str,
    keep_default_na=False,
    na_filter=False,
)
summary = {"raw_rows": int(len(raw))}
raw.columns = [str(c).strip() for c in raw.columns]
records = [
    {col: normalize_text(value) for col, value in row.items()}
    for row in raw.to_dict("records")
]

# ---------------------------------------------------------------------------
# R2: remove duplicate customer_id rows (keep first in raw-file order) BEFORE
# any other row filter.
# ---------------------------------------------------------------------------
seen_ids = set()
deduped = []
duplicates_removed = 0
for rec in records:
    cid = rec.get("customer_id")
    key = ("__missing__",) if cid is None else ("id", cid)
    if key in seen_ids:
        duplicates_removed += 1
        continue
    seen_ids.add(key)
    deduped.append(rec)
summary["duplicates_removed_customer_id"] = duplicates_removed

# ---------------------------------------------------------------------------
# Field parsers and mappings (R3-R10).
# ---------------------------------------------------------------------------
DATE_PATTERNS = [
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "%Y-%m-%d"),          # YYYY-MM-DD
    (re.compile(r"^\d{2}/\d{2}/\d{4}$"), "%m/%d/%Y"),          # MM/DD/YYYY (month first)
    (re.compile(r"^\d{2}-[A-Za-z]{3}-\d{4}$"), "%d-%b-%Y"),    # DD-Mon-YYYY
    (re.compile(r"^\d{4}/\d{2}/\d{2}$"), "%Y/%m/%d"),          # YYYY/MM/DD
    (re.compile(r"^[A-Za-z]+ \d{1,2}, \d{4}$"), "%B %d, %Y"),  # Month D, YYYY
]


def parse_signup_date(value):
    """R3: parse with exactly one of the five allowed formats."""
    if value is None:
        return None
    for pattern, fmt in DATE_PATTERNS:
        if pattern.match(value):
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                return None
    return None


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

CONTRACT_MAP = {
    "monthly": "Monthly",
    "month-to-month": "Monthly",
    "m2m": "Monthly",
    "annual": "Annual",
    "yearly": "Annual",
    "1 year": "Annual",
}

CHURN_MAP = {
    "yes": 1, "y": 1, "true": 1, "1": 1, "churned": 1,
    "no": 0, "n": 0, "false": 0, "0": 0, "active": 0,
}


def parse_monthly_fee(value):
    """R6: strip '$', 'USD' and ',', parse number, require 0 < fee <= 500."""
    if value is None:
        return None
    text = re.sub(r"usd", "", value, flags=re.IGNORECASE)
    text = text.replace("$", "").replace(",", "").strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if not math.isfinite(number) or number <= 0 or number > 500:
        return None
    return number


def parse_tenure_months(value):
    """R7: drop trailing 'month(s)', require whole number in [0, 120]."""
    if value is None:
        return None
    text = re.sub(r"\s*months?\s*$", "", value, flags=re.IGNORECASE).strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if (not math.isfinite(number)) or (not number.is_integer()) \
            or number < 0 or number > 120:
        return None
    return int(number)


_DROP = object()


def parse_support_tickets(value):
    """R8: missing -> 0; otherwise require whole number in [0, 100]."""
    if value is None:
        return 0
    try:
        number = float(value)
    except ValueError:
        return _DROP
    if (not math.isfinite(number)) or (not number.is_integer()) \
            or number < 0 or number > 100:
        return _DROP
    return int(number)


def parse_satisfaction(value):
    """R9: return int 1-5, or None (write empty cell but KEEP the row)."""
    if value is None:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    if (not math.isfinite(number)) or (not number.is_integer()) \
            or number < 1 or number > 5:
        return None
    return int(number)


# ---------------------------------------------------------------------------
# Apply rules R3-R10 in order; build cleaned records with R11 lifetime_value.
# ---------------------------------------------------------------------------
drop_counts = {
    "missing_customer_id": 0,
    "invalid_signup_date": 0,
    "invalid_plan": 0,
    "invalid_contract_type": 0,
    "invalid_monthly_fee": 0,
    "invalid_tenure_months": 0,
    "invalid_support_tickets": 0,
    "invalid_churned": 0,
}
satisfaction_set_missing = 0
cleaned = []

for rec in deduped:
    customer_id = rec.get("customer_id")
    if customer_id is None:
        drop_counts["missing_customer_id"] += 1
        continue

    signup_date = parse_signup_date(rec.get("signup_date"))
    if signup_date is None:
        drop_counts["invalid_signup_date"] += 1
        continue

    plan = PLAN_MAP.get((rec.get("plan") or "").lower())
    if plan is None:
        drop_counts["invalid_plan"] += 1
        continue

    contract_type = CONTRACT_MAP.get((rec.get("contract_type") or "").lower())
    if contract_type is None:
        drop_counts["invalid_contract_type"] += 1
        continue

    monthly_fee = parse_monthly_fee(rec.get("monthly_fee"))
    if monthly_fee is None:
        drop_counts["invalid_monthly_fee"] += 1
        continue

    tenure_months = parse_tenure_months(rec.get("tenure_months"))
    if tenure_months is None:
        drop_counts["invalid_tenure_months"] += 1
        continue

    support_tickets = parse_support_tickets(rec.get("support_tickets"))
    if support_tickets is _DROP:
        drop_counts["invalid_support_tickets"] += 1
        continue

    satisfaction_score = parse_satisfaction(rec.get("satisfaction_score"))
    if satisfaction_score is None:
        satisfaction_set_missing += 1  # row kept, cell written empty (R9)

    churned = CHURN_MAP.get((rec.get("churned") or "").lower())
    if churned is None:
        drop_counts["invalid_churned"] += 1
        continue

    cleaned.append({
        "customer_id": customer_id,
        "signup_date": signup_date,
        "plan": plan,
        "contract_type": contract_type,
        "monthly_fee": monthly_fee,
        "tenure_months": tenure_months,
        "support_tickets": support_tickets,
        "satisfaction_score": satisfaction_score,
        "churned": churned,
        "lifetime_value": round(monthly_fee * tenure_months, 2),  # R11
    })

# ---------------------------------------------------------------------------
# R12: exact column order, sort by customer_id ascending, write outputs.
# ---------------------------------------------------------------------------
COLUMNS = [
    "customer_id", "signup_date", "plan", "contract_type", "monthly_fee",
    "tenure_months", "support_tickets", "satisfaction_score", "churned",
    "lifetime_value",
]
out = pd.DataFrame(cleaned, columns=COLUMNS)
if len(out) > 0:
    out["monthly_fee"] = out["monthly_fee"].astype(float)
    out["tenure_months"] = out["tenure_months"].astype(int)
    out["support_tickets"] = out["support_tickets"].astype(int)
    out["satisfaction_score"] = out["satisfaction_score"].astype("Int64")  # nullable int -> empty cell
    out["churned"] = out["churned"].astype(int)
    out["lifetime_value"] = out["lifetime_value"].astype(float)
out = out.sort_values("customer_id", kind="mergesort").reset_index(drop=True)
out.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)

summary.update({
    "cleaned_rows": int(len(out)),
    "dropped_missing_customer_id": drop_counts["missing_customer_id"],
    "dropped_invalid_signup_date": drop_counts["invalid_signup_date"],
    "dropped_invalid_plan": drop_counts["invalid_plan"],
    "dropped_invalid_contract_type": drop_counts["invalid_contract_type"],
    "dropped_invalid_monthly_fee": drop_counts["invalid_monthly_fee"],
    "dropped_invalid_tenure_months": drop_counts["invalid_tenure_months"],
    "dropped_invalid_support_tickets": drop_counts["invalid_support_tickets"],
    "satisfaction_score_set_to_missing": satisfaction_set_missing,
    "dropped_invalid_churned": drop_counts["invalid_churned"],
})
with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w",
          encoding="utf-8") as fh:
    json.dump(summary, fh, indent=2)
