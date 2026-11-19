"""Cleaning stage for the customer_churn project.

Reads raw.csv from INPUT_DIR, applies cleaning rules R1-R12, and writes
cleaned.csv plus cleaning_summary.json to OUTPUT_DIR.
"""

import json
import os
import re
from datetime import datetime

import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

DATE_FORMATS = (
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY, e.g. 05-Mar-2024
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY, e.g. March 5, 2024
)

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

OUTPUT_COLUMNS = [
    "customer_id", "signup_date", "plan", "contract_type", "monthly_fee",
    "tenure_months", "support_tickets", "satisfaction_score", "churned",
    "lifetime_value",
]


def clean_cell(value):
    """R1: strip whitespace; normalize missing tokens to None."""
    if value is None:
        return None
    text = str(value).strip()
    return None if text.lower() in MISSING_TOKENS else text


def parse_signup_date(text):
    """R3: accept exactly the five allowed date formats."""
    if text is None:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_plan(text):
    return None if text is None else PLAN_MAP.get(text.lower())


def parse_contract(text):
    return None if text is None else CONTRACT_MAP.get(text.lower())


def parse_monthly_fee(text):
    """R6: strip '$', 'USD', ','; number must be in (0, 500]."""
    if text is None:
        return None
    cleaned = text.replace("$", "").replace(",", "")
    cleaned = re.sub(r"USD", "", cleaned, flags=re.IGNORECASE).strip()
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if not (0 < value <= 500):
        return None
    return value


def parse_tenure_months(text):
    """R7: strip trailing 'month(s)'; whole number in [0, 120]."""
    if text is None:
        return None
    cleaned = re.sub(r"\s*months?\s*$", "", text, flags=re.IGNORECASE).strip()
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if not value.is_integer() or not (0 <= value <= 120):
        return None
    return int(value)


def parse_support_tickets(text):
    """R8: missing means 0; otherwise whole number in [0, 100]."""
    if text is None:
        return 0
    try:
        value = float(text)
    except ValueError:
        return None
    if not value.is_integer() or not (0 <= value <= 100):
        return None
    return int(value)


def parse_satisfaction(text):
    """R9: invalid values become missing (None); row is kept."""
    if text is None:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if not value.is_integer() or not (1 <= value <= 5):
        return None
    return int(value)


def parse_churned(text):
    return None if text is None else CHURN_MAP.get(text.lower())


def apply_drop_rule(df, column, parser, summary, count_key):
    """Apply a parser to a column, dropping rows where it returns None."""
    parsed = df[column].map(parser)
    bad = parsed.isna()
    summary[count_key] = int(bad.sum())
    kept = df.loc[~bad].copy()
    kept[column] = parsed.loc[~bad]
    return kept


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    summary = {}

    raw = pd.read_csv(
        os.path.join(INPUT_DIR, "raw.csv"), dtype=str, keep_default_na=False
    )
    raw.columns = [str(c).strip() for c in raw.columns]
    summary["raw_rows"] = int(len(raw))

    # R1: read as text, strip whitespace, normalize missing tokens.
    df = raw.apply(lambda col: col.map(clean_cell))

    # R2: drop duplicate customer_id records BEFORE any other row filter,
    # keeping the first occurrence in raw-file order.
    before = len(df)
    df = df.drop_duplicates(subset="customer_id", keep="first")
    summary["duplicates_removed"] = int(before - len(df))

    # R3-R8 and R10: validating rules that drop invalid rows.
    df = apply_drop_rule(df, "signup_date", parse_signup_date, summary, "dropped_signup_date")
    df = apply_drop_rule(df, "plan", parse_plan, summary, "dropped_plan")
    df = apply_drop_rule(df, "contract_type", parse_contract, summary, "dropped_contract_type")
    df = apply_drop_rule(df, "monthly_fee", parse_monthly_fee, summary, "dropped_monthly_fee")
    df = apply_drop_rule(df, "tenure_months", parse_tenure_months, summary, "dropped_tenure_months")
    df = apply_drop_rule(df, "support_tickets", parse_support_tickets, summary, "dropped_support_tickets")

    # R9: invalid satisfaction_score becomes missing; row is kept.
    originally_missing = df["satisfaction_score"].isna()
    parsed_sat = df["satisfaction_score"].map(parse_satisfaction)
    summary["satisfaction_score_set_missing"] = int(
        (~originally_missing & parsed_sat.isna()).sum()
    )
    df = df.copy()
    df["satisfaction_score"] = parsed_sat

    df = apply_drop_rule(df, "churned", parse_churned, summary, "dropped_churned")

    # Type normalization.
    df["monthly_fee"] = df["monthly_fee"].astype(float)
    df["tenure_months"] = df["tenure_months"].astype(int)
    df["support_tickets"] = df["support_tickets"].astype(int)
    df["churned"] = df["churned"].astype(int)
    df["satisfaction_score"] = df["satisfaction_score"].astype("Int64")

    # R11: lifetime value = monthly_fee * tenure_months, 2 decimals.
    df["lifetime_value"] = (df["monthly_fee"] * df["tenure_months"]).round(2)

    # R12: exact column order, sort by customer_id ascending, write CSV.
    df = df[OUTPUT_COLUMNS].sort_values("customer_id").reset_index(drop=True)
    summary["cleaned_rows"] = int(len(df))

    df.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)
    with open(
        os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w", encoding="utf-8"
    ) as fh:
        json.dump(summary, fh, indent=2)

    print(
        "cleaned.csv: {0} rows written ({1} raw rows).".format(
            summary["cleaned_rows"], summary["raw_rows"]
        )
    )


if __name__ == "__main__":
    main()
