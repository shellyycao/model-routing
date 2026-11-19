import os
import re
import json
import math
from datetime import datetime

import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

# R3: accepted signup_date formats, tried in this exact order
DATE_FORMATS = [
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY (e.g. 05-Mar-2024)
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY (e.g. March 5, 2024)
]

# R4
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

# R5
CONTRACT_MAP = {
    "monthly": "Monthly",
    "month-to-month": "Monthly",
    "m2m": "Monthly",
    "annual": "Annual",
    "yearly": "Annual",
    "1 year": "Annual",
}

# R10
CHURN_MAP = {
    "yes": 1, "y": 1, "true": 1, "1": 1, "churned": 1,
    "no": 0, "n": 0, "false": 0, "0": 0, "active": 0,
}


def parse_number(text):
    """Parse text as a finite float; return None on failure."""
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return value


def parse_signup_date(text):
    """Try each accepted format; return normalised YYYY-MM-DD or None."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)

    # R1: read every column as text; no automatic NA coercion
    raw = pd.read_csv(input_path, dtype=str, keep_default_na=False, na_filter=False)
    raw_rows = int(len(raw))

    summary = {
        "raw_rows": raw_rows,
        "duplicates_removed": 0,
        "dropped_signup_date": 0,
        "dropped_plan": 0,
        "dropped_contract_type": 0,
        "dropped_monthly_fee": 0,
        "dropped_tenure_months": 0,
        "dropped_support_tickets": 0,
        "satisfaction_set_missing": 0,
        "dropped_churned": 0,
        "cleaned_rows": 0,
    }

    def clean_cell(x):
        # R1: strip whitespace, normalise missing tokens (case-insensitive)
        text = "" if x is None else str(x).strip()
        if text.lower() in MISSING_TOKENS:
            return None
        return text

    records = [
        {col: clean_cell(row[col]) for col in raw.columns}
        for _, row in raw.iterrows()
    ]

    # R2: remove duplicates on customer_id BEFORE any other row filter;
    # keep the first occurrence in raw-file order
    seen_ids = set()
    deduped = []
    for rec in records:
        cid = rec.get("customer_id")
        if cid is not None:
            if cid in seen_ids:
                summary["duplicates_removed"] += 1
                continue
            seen_ids.add(cid)
        deduped.append(rec)

    cleaned = []
    for rec in deduped:
        # R3: signup_date
        sd = rec.get("signup_date")
        parsed = parse_signup_date(sd) if sd is not None else None
        if parsed is None:
            summary["dropped_signup_date"] += 1
            continue
        rec["signup_date"] = parsed

        # R4: plan
        plan_raw = rec.get("plan")
        plan = PLAN_MAP.get(plan_raw.lower()) if plan_raw is not None else None
        if plan is None:
            summary["dropped_plan"] += 1
            continue
        rec["plan"] = plan

        # R5: contract_type
        ct_raw = rec.get("contract_type")
        contract = CONTRACT_MAP.get(ct_raw.lower()) if ct_raw is not None else None
        if contract is None:
            summary["dropped_contract_type"] += 1
            continue
        rec["contract_type"] = contract

        # R6: monthly_fee
        fee_raw = rec.get("monthly_fee")
        fee = None
        if fee_raw is not None:
            text = fee_raw.replace("$", "").replace(",", "")
            text = re.sub(r"usd", "", text, flags=re.IGNORECASE).strip()
            fee = parse_number(text)
        if fee is None or fee <= 0 or fee > 500:
            summary["dropped_monthly_fee"] += 1
            continue
        rec["monthly_fee"] = fee

        # R7: tenure_months
        ten_raw = rec.get("tenure_months")
        tenure = None
        if ten_raw is not None:
            text = re.sub(r"\s*months?\s*$", "", ten_raw, flags=re.IGNORECASE).strip()
            num = parse_number(text)
            if num is not None and num.is_integer() and 0 <= num <= 120:
                tenure = int(num)
        if tenure is None:
            summary["dropped_tenure_months"] += 1
            continue
        rec["tenure_months"] = tenure

        # R8: support_tickets (missing means 0)
        st_raw = rec.get("support_tickets")
        if st_raw is None:
            rec["support_tickets"] = 0
        else:
            num = parse_number(st_raw)
            if num is None or not num.is_integer() or num < 0 or num > 100:
                summary["dropped_support_tickets"] += 1
                continue
            rec["support_tickets"] = int(num)

        # R9: satisfaction_score (invalid/missing -> empty cell, keep row)
        ss_raw = rec.get("satisfaction_score")
        score = None
        if ss_raw is not None:
            num = parse_number(ss_raw)
            if num is not None and num.is_integer() and 1 <= num <= 5:
                score = int(num)
        if score is None:
            summary["satisfaction_set_missing"] += 1
        rec["satisfaction_score"] = score

        # R10: churned
        ch_raw = rec.get("churned")
        churned = CHURN_MAP.get(ch_raw.lower()) if ch_raw is not None else None
        if churned is None:
            summary["dropped_churned"] += 1
            continue
        rec["churned"] = churned

        # R11: lifetime_value
        rec["lifetime_value"] = round(rec["monthly_fee"] * rec["tenure_months"], 2)

        cleaned.append(rec)

    # R12: exact column order, typed, sorted by customer_id ascending
    columns = [
        "customer_id", "signup_date", "plan", "contract_type",
        "monthly_fee", "tenure_months", "support_tickets",
        "satisfaction_score", "churned", "lifetime_value",
    ]
    df = pd.DataFrame(cleaned, columns=columns)
    df["customer_id"] = df["customer_id"].fillna("").astype(str)
    df["monthly_fee"] = df["monthly_fee"].astype(float)
    df["tenure_months"] = df["tenure_months"].astype(int)
    df["support_tickets"] = df["support_tickets"].astype(int)
    df["churned"] = df["churned"].astype(int)
    # Nullable integer so missing values are written as empty cells
    df["satisfaction_score"] = pd.array(df["satisfaction_score"], dtype="Int64")
    df["lifetime_value"] = df["lifetime_value"].astype(float)

    df = df.sort_values("customer_id", kind="stable").reset_index(drop=True)

    out_csv = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(out_csv, index=False)

    summary["cleaned_rows"] = int(len(df))
    with open(os.path.join(output_dir, "cleaning_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
