import os
import re
import json
import math
from datetime import datetime

import pandas as pd


MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

# R3: exactly these five signup_date formats, tried in order.
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
    "customer_id", "signup_date", "plan", "contract_type", "monthly_fee",
    "tenure_months", "support_tickets", "satisfaction_score", "churned",
    "lifetime_value",
]


def normalize_cell(value):
    """R1: strip whitespace; map NA-like tokens (case-insensitive) to None."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in MISSING_TOKENS:
        return None
    return text


def lookup_key(text):
    """Lowercase key with internal whitespace collapsed for robust mapping."""
    return " ".join(text.lower().split())


def parse_signup_date(text):
    candidate = " ".join(text.split())
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(candidate, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_number(text):
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return value


def parse_monthly_fee(text):
    # R6: remove '$', 'USD' and ',' (plus surrounding spaces), then parse.
    cleaned = re.sub(r"usd", "", text, flags=re.IGNORECASE)
    cleaned = cleaned.replace("$", "").replace(",", "").strip()
    value = parse_number(cleaned)
    if value is None or value <= 0 or value > 500:
        return None
    return value


def parse_tenure_months(text):
    # R7: strip a trailing 'month'/'months' word, then require a whole number 0-120.
    cleaned = re.sub(r"\s*months?\s*$", "", text, flags=re.IGNORECASE).strip()
    value = parse_number(cleaned)
    if value is None or not value.is_integer() or value < 0 or value > 120:
        return None
    return int(value)


def parse_support_tickets(text):
    # R8: whole number 0-100.
    value = parse_number(text)
    if value is None or not value.is_integer() or value < 0 or value > 100:
        return None
    return int(value)


def parse_satisfaction(text):
    # R9: whole number 1-5, else None (row is kept, cell written empty).
    value = parse_number(text)
    if value is None or not value.is_integer() or value < 1 or value > 5:
        return None
    return int(value)


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    raw_path = os.path.join(input_dir, "raw.csv")

    # R1: read every column as text; do not let pandas coerce NA tokens itself.
    raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw.columns = [str(c).strip() for c in raw.columns]
    summary = {"raw_rows": int(len(raw))}

    for col in raw.columns:
        raw[col] = raw[col].map(normalize_cell)

    # R2: deduplicate on customer_id BEFORE any other row filter; keep first
    # occurrence in raw-file order. Rows without a customer_id cannot satisfy
    # the output schema and are removed here too.
    missing_ids = int(raw["customer_id"].isna().sum())
    raw = raw[raw["customer_id"].notna()]
    before_dedupe = len(raw)
    raw = raw.drop_duplicates(subset="customer_id", keep="first")
    summary["missing_customer_id_removed"] = missing_ids
    summary["duplicates_removed"] = int(before_dedupe - len(raw))

    counts = {
        "dropped_signup_date": 0,
        "dropped_plan": 0,
        "dropped_contract_type": 0,
        "dropped_monthly_fee": 0,
        "dropped_tenure_months": 0,
        "dropped_support_tickets": 0,
        "dropped_churned": 0,
        "satisfaction_set_missing": 0,
    }

    records = []
    for _, row in raw.iterrows():
        # R3: signup_date
        signup_raw = row["signup_date"]
        signup_date = parse_signup_date(signup_raw) if signup_raw is not None else None
        if signup_date is None:
            counts["dropped_signup_date"] += 1
            continue

        # R4: plan
        plan_raw = row["plan"]
        plan = PLAN_MAP.get(lookup_key(plan_raw)) if plan_raw is not None else None
        if plan is None:
            counts["dropped_plan"] += 1
            continue

        # R5: contract_type
        contract_raw = row["contract_type"]
        contract = CONTRACT_MAP.get(lookup_key(contract_raw)) if contract_raw is not None else None
        if contract is None:
            counts["dropped_contract_type"] += 1
            continue

        # R6: monthly_fee
        fee_raw = row["monthly_fee"]
        fee = parse_monthly_fee(fee_raw) if fee_raw is not None else None
        if fee is None:
            counts["dropped_monthly_fee"] += 1
            continue

        # R7: tenure_months
        tenure_raw = row["tenure_months"]
        tenure = parse_tenure_months(tenure_raw) if tenure_raw is not None else None
        if tenure is None:
            counts["dropped_tenure_months"] += 1
            continue

        # R8: support_tickets (missing means 0)
        tickets_raw = row["support_tickets"]
        if tickets_raw is None:
            tickets = 0
        else:
            tickets = parse_support_tickets(tickets_raw)
            if tickets is None:
                counts["dropped_support_tickets"] += 1
                continue

        # R9: satisfaction_score (invalid/missing -> empty cell, keep row)
        sat_raw = row["satisfaction_score"]
        satisfaction = parse_satisfaction(sat_raw) if sat_raw is not None else None
        if satisfaction is None:
            counts["satisfaction_set_missing"] += 1

        # R10: churned
        churn_raw = row["churned"]
        churned = CHURN_MAP.get(lookup_key(churn_raw)) if churn_raw is not None else None
        if churned is None:
            counts["dropped_churned"] += 1
            continue

        # R11: lifetime_value
        lifetime_value = round(fee * tenure, 2)

        records.append({
            "customer_id": row["customer_id"],
            "signup_date": signup_date,
            "plan": plan,
            "contract_type": contract,
            "monthly_fee": fee,
            "tenure_months": tenure,
            "support_tickets": tickets,
            "satisfaction_score": satisfaction,
            "churned": churned,
            "lifetime_value": lifetime_value,
        })

    # R12: exact column order, sorted by customer_id ascending.
    cleaned = pd.DataFrame(records, columns=OUTPUT_COLUMNS)
    cleaned = cleaned.sort_values("customer_id", kind="stable").reset_index(drop=True)
    # Nullable integer so missing satisfaction_score is written as an empty cell.
    cleaned["satisfaction_score"] = cleaned["satisfaction_score"].astype("Int64")

    summary.update(counts)
    summary["cleaned_rows"] = int(len(cleaned))

    os.makedirs(output_dir, exist_ok=True)
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    cleaned.to_csv(cleaned_path, index=False)

    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
