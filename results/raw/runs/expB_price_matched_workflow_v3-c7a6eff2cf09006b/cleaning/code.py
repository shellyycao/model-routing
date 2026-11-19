import json
import math
import os
import re
from datetime import datetime

import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

DATE_FORMATS = (
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY (English 3-letter month)
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY (full English month name)
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
    "customer_id",
    "signup_date",
    "plan",
    "contract_type",
    "monthly_fee",
    "tenure_months",
    "support_tickets",
    "satisfaction_score",
    "churned",
    "lifetime_value",
]


def normalize(value):
    """R1: strip whitespace and map missing tokens (case-insensitive) to None."""
    if value is None:
        return None
    text = str(value).strip()
    return None if text.lower() in MISSING_TOKENS else text


def to_number(text):
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def parse_signup_date(value):
    """R3: parse with exactly the five allowed formats; return 'YYYY-MM-DD' or None."""
    if value is None:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_plan(value):
    if value is None:
        return None
    return PLAN_MAP.get(value.lower())


def parse_contract_type(value):
    if value is None:
        return None
    return CONTRACT_MAP.get(value.lower())


def parse_monthly_fee(value):
    """R6: strip '$', 'USD' and ',' then parse; must be 0 < fee <= 500."""
    if value is None:
        return None
    cleaned = value.replace("$", "").replace(",", "")
    cleaned = re.sub(r"USD", "", cleaned, flags=re.IGNORECASE).strip()
    number = to_number(cleaned)
    if number is None or number <= 0 or number > 500:
        return None
    return number


def parse_tenure_months(value):
    """R7: strip a trailing 'month'/'months', whole number in [0, 120]."""
    if value is None:
        return None
    cleaned = re.sub(r"\s*months?\s*$", "", value, flags=re.IGNORECASE).strip()
    number = to_number(cleaned)
    if number is None or not number.is_integer() or number < 0 or number > 120:
        return None
    return int(number)


def parse_support_tickets(value):
    """R8: missing -> 0; otherwise whole number in [0, 100] or None to drop."""
    if value is None:
        return 0
    number = to_number(value)
    if number is None or not number.is_integer() or number < 0 or number > 100:
        return None
    return int(number)


def parse_satisfaction_score(value):
    """R9: return int 1-5, or None when the value must be stored as missing."""
    if value is None:
        return None
    number = to_number(value)
    if number is None or not number.is_integer() or number < 1 or number > 5:
        return None
    return int(number)


def parse_churned(value):
    if value is None:
        return None
    return CHURN_MAP.get(value.lower())


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # R1: read every column as text, strip whitespace, normalise missing tokens.
    df = pd.read_csv(
        input_path,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        encoding="utf-8-sig",
    )
    df.columns = [str(c).strip() for c in df.columns]
    raw_rows = len(df)
    df = df.apply(lambda col: col.map(normalize))

    counts = {
        "dropped_missing_customer_id": 0,
        "duplicates_removed": 0,
        "dropped_signup_date": 0,
        "dropped_plan": 0,
        "dropped_contract_type": 0,
        "dropped_monthly_fee": 0,
        "dropped_tenure_months": 0,
        "dropped_support_tickets": 0,
        "satisfaction_score_set_missing": 0,
        "dropped_churned": 0,
    }

    # R2: before any other row filter, drop rows without a usable customer_id
    # and de-duplicate on customer_id, keeping the first raw-file occurrence.
    missing_id = df["customer_id"].isna()
    counts["dropped_missing_customer_id"] = int(missing_id.sum())
    df = df[~missing_id]
    before = len(df)
    df = df.drop_duplicates(subset="customer_id", keep="first")
    counts["duplicates_removed"] = int(before - len(df))

    cleaned_rows = []
    for record in df.to_dict("records"):
        # R3
        signup_date = parse_signup_date(record["signup_date"])
        if signup_date is None:
            counts["dropped_signup_date"] += 1
            continue
        # R4
        plan = parse_plan(record["plan"])
        if plan is None:
            counts["dropped_plan"] += 1
            continue
        # R5
        contract_type = parse_contract_type(record["contract_type"])
        if contract_type is None:
            counts["dropped_contract_type"] += 1
            continue
        # R6
        monthly_fee = parse_monthly_fee(record["monthly_fee"])
        if monthly_fee is None:
            counts["dropped_monthly_fee"] += 1
            continue
        # R7
        tenure_months = parse_tenure_months(record["tenure_months"])
        if tenure_months is None:
            counts["dropped_tenure_months"] += 1
            continue
        # R8
        support_tickets = parse_support_tickets(record["support_tickets"])
        if support_tickets is None:
            counts["dropped_support_tickets"] += 1
            continue
        # R9: invalid satisfaction becomes missing but the row is kept.
        raw_satisfaction = record["satisfaction_score"]
        satisfaction_score = parse_satisfaction_score(raw_satisfaction)
        if raw_satisfaction is not None and satisfaction_score is None:
            counts["satisfaction_score_set_missing"] += 1
        # R10
        churned = parse_churned(record["churned"])
        if churned is None:
            counts["dropped_churned"] += 1
            continue
        # R11
        lifetime_value = round(monthly_fee * tenure_months, 2)

        cleaned_rows.append({
            "customer_id": record["customer_id"],
            "signup_date": signup_date,
            "plan": plan,
            "contract_type": contract_type,
            "monthly_fee": monthly_fee,
            "tenure_months": tenure_months,
            "support_tickets": support_tickets,
            "satisfaction_score": satisfaction_score,
            "churned": churned,
            "lifetime_value": lifetime_value,
        })

    # R12: exact column order, sort by customer_id ascending, plain CSV output.
    out = pd.DataFrame(cleaned_rows, columns=OUTPUT_COLUMNS)
    out["satisfaction_score"] = out["satisfaction_score"].astype("Int64")
    out = out.sort_values("customer_id", kind="mergesort").reset_index(drop=True)
    out.to_csv(cleaned_path, index=False)

    summary = {"raw_rows": int(raw_rows), "cleaned_rows": int(len(out))}
    summary.update(counts)
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print(f"cleaning done: raw_rows={raw_rows} cleaned_rows={len(out)}")


if __name__ == "__main__":
    main()
