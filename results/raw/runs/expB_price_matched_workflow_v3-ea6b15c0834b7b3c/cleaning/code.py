"""Cleaning stage of the customer_churn workflow (prompt v3).

Reads raw.csv from INPUT_DIR, applies rules R1-R12 in order, and writes
cleaned.csv plus cleaning_summary.json to OUTPUT_DIR.
"""

import json
import math
import os
import re
from datetime import datetime

import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

DATE_FORMATS = [
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY (e.g. 05-Mar-2024)
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY (e.g. March 5, 2024)
]

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
    "yearly": "Yearly_FIX",  # placeholder replaced below
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

OUTPUT_COLUMNS = [
    "customer_id", "signup_date", "plan", "contract_type", "monthly_fee",
    "tenure_months", "support_tickets", "satisfaction_score", "churned",
    "lifetime_value",
]


def is_missing(value):
    return (
        value is None
        or value is pd.NA
        or (isinstance(value, float) and math.isnan(value))
    )


def parse_signup_date(text):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_monthly_fee(text):
    cleaned = re.sub(r"usd", "", text, flags=re.IGNORECASE)
    cleaned = cleaned.replace("$", "").replace(",", "").strip()
    if cleaned == "":
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value


def parse_whole_number(text):
    if text == "":
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if not math.isfinite(value) or not value.is_integer():
        return None
    return int(value)


def parse_tenure_months(text):
    cleaned = re.sub(r"\s*months?\s*$", "", text, flags=re.IGNORECASE).strip()
    return parse_whole_number(cleaned)


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)

    raw_path = os.path.join(input_dir, "raw.csv")
    df = pd.read_csv(
        raw_path,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        encoding="utf-8-sig",
    )
    df.columns = [str(c).strip() for c in df.columns]
    raw_rows = int(len(df))

    # R1: strip whitespace from every value and normalize missing-value tokens.
    def normalize(value):
        text = str(value).strip()
        return pd.NA if text.lower() in MISSING_TOKENS else text

    for column in df.columns:
        df[column] = df[column].map(normalize)

    # R2: remove duplicate customer_id rows FIRST, keeping the first occurrence
    # in raw-file order.
    duplicate_mask = df["customer_id"].duplicated(keep="first")
    duplicates_removed = int(duplicate_mask.sum())
    df = df.loc[~duplicate_mask]

    counts = {
        "duplicates_removed": duplicates_removed,
        "dropped_missing_customer_id": 0,
        "dropped_invalid_signup_date": 0,
        "dropped_invalid_plan": 0,
        "dropped_invalid_contract_type": 0,
        "dropped_invalid_monthly_fee": 0,
        "dropped_invalid_tenure_months": 0,
        "dropped_invalid_support_tickets": 0,
        "satisfaction_score_set_missing": 0,
        "dropped_invalid_churned": 0,
    }

    records = []
    for row in df.itertuples(index=False):
        customer_id = row.customer_id
        if is_missing(customer_id):
            counts["dropped_missing_customer_id"] += 1
            continue

        # R3: signup_date must match exactly one of the allowed formats.
        signup_date = (
            None if is_missing(row.signup_date) else parse_signup_date(row.signup_date)
        )
        if signup_date is None:
            counts["dropped_invalid_signup_date"] += 1
            continue

        # R4: plan mapping.
        plan = None if is_missing(row.plan) else PLAN_MAP.get(row.plan.lower())
        if plan is None:
            counts["dropped_invalid_plan"] += 1
            continue

        # R5: contract_type mapping.
        contract_type = (
            None
            if is_missing(row.contract_type)
            else CONTRACT_MAP.get(row.contract_type.lower())
        )
        if contract_type is None:
            counts["dropped_invalid_contract_type"] += 1
            continue

        # R6: monthly_fee numeric, 0 < fee <= 500.
        monthly_fee = (
            None if is_missing(row.monthly_fee) else parse_monthly_fee(row.monthly_fee)
        )
        if monthly_fee is None or monthly_fee <= 0 or monthly_fee > 500:
            counts["dropped_invalid_monthly_fee"] += 1
            continue

        # R7: tenure_months whole number in [0, 120].
        tenure_months = (
            None
            if is_missing(row.tenure_months)
            else parse_tenure_months(row.tenure_months)
        )
        if tenure_months is None or tenure_months < 0 or tenure_months > 120:
            counts["dropped_invalid_tenure_months"] += 1
            continue

        # R8: support_tickets; missing means 0, else whole number in [0, 100].
        if is_missing(row.support_tickets):
            support_tickets = 0
        else:
            support_tickets = parse_whole_number(row.support_tickets)
            if support_tickets is None or support_tickets < 0 or support_tickets > 100:
                counts["dropped_invalid_support_tickets"] += 1
                continue

        # R9: satisfaction_score; invalid/missing -> empty cell, row kept.
        satisfaction_score = None
        if not is_missing(row.satisfaction_score):
            parsed = parse_whole_number(row.satisfaction_score)
            if parsed is not None and 1 <= parsed <= 5:
                satisfaction_score = parsed
        if satisfaction_score is None:
            counts["satisfaction_score_set_missing"] += 1

        # R10: churned mapping to 0/1.
        churned = None if is_missing(row.churned) else CHURN_MAP.get(row.churned.lower())
        if churned is None:
            counts["dropped_invalid_churned"] += 1
            continue

        # R11: lifetime_value.
        lifetime_value = round(monthly_fee * tenure_months, 2)

        records.append(
            {
                "customer_id": customer_id,
                "signup_date": signup_date,
                "plan": plan,
                "contract_type": contract_type,
                "monthly_fee": monthly_fee,
                "tenure_months": tenure_months,
                "support_tickets": support_tickets,
                "satisfaction_score": satisfaction_score,
                "churned": churned,
                "lifetime_value": lifetime_value,
            }
        )

    # R12: exact column order, sort by customer_id ascending, enforce dtypes.
    out = pd.DataFrame(records, columns=OUTPUT_COLUMNS)
    out = out.sort_values("customer_id", kind="mergesort").reset_index(drop=True)
    out["monthly_fee"] = out["monthly_fee"].astype("float64")
    out["tenure_months"] = out["tenure_months"].astype("int64")
    out["support_tickets"] = out["support_tickets"].astype("int64")
    out["satisfaction_score"] = out["satisfaction_score"].astype("Int64")
    out["churned"] = out["churned"].astype("int64")
    out["lifetime_value"] = out["lifetime_value"].astype("float64")

    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    out.to_csv(cleaned_path, index=False)

    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": int(len(out)),
    }
    summary.update(counts)

    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)


if __name__ == "__main__":
    main()
