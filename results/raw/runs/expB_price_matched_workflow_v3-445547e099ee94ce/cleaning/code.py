"""Cleaning stage for project customer_churn (prompt v3).

Reads raw.csv from INPUT_DIR, applies cleaning rules R1-R12 in order, and
writes cleaned.csv plus cleaning_summary.json to OUTPUT_DIR.
"""

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
    "%d-%b-%Y",   # DD-Mon-YYYY, English 3-letter month abbreviation
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

CONTRACT_TYPE_MAP = {
    "monthly": "Monthly",
    "month-to-month": "Monthly",
    "m2m": "Monthly",
    "annual": "Annual",
    "yearly": "Annual",
    "1 year": "Annual",
}

CHURNED_MAP = {
    "yes": 1,
    "y": 1,
    "true": 1,
    "1": 1,
    "churned": 1,
    "no": 0,
    "n": 0,
    "false": 0,
    "0": 0,
    "active": 0,
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

COUNT_KEYS = [
    "duplicates_removed",
    "dropped_missing_customer_id",
    "dropped_signup_date",
    "dropped_plan",
    "dropped_contract_type",
    "dropped_monthly_fee",
    "dropped_tenure_months",
    "dropped_support_tickets",
    "satisfaction_score_set_missing",
    "dropped_churned",
]


def clean_text(value):
    """R1: strip whitespace; map known missing tokens (case-insensitive) to None."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in MISSING_TOKENS:
        return None
    return text


def parse_signup_date(text):
    """R3: try exactly the five allowed formats; return YYYY-MM-DD or None."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
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


def parse_whole_number(text):
    value = parse_number(text)
    if value is None or not value.is_integer():
        return None
    return int(value)


def parse_monthly_fee(text):
    """R6: remove '$', 'USD' and ',' plus surrounding spaces, then parse."""
    cleaned = re.sub(r"[$,]", "", text)
    cleaned = re.sub(r"usd", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    if not cleaned:
        return None
    return parse_number(cleaned)


def parse_tenure_months(text):
    """R7: remove a trailing 'month'/'months' word (case-insensitive), then parse."""
    cleaned = re.sub(r"\s*months?\s*$", "", text, flags=re.IGNORECASE).strip()
    if not cleaned:
        return None
    return parse_whole_number(cleaned)


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # R1: read every column as text, with no automatic NA conversion.
    raw = pd.read_csv(
        input_path, dtype=str, keep_default_na=False, encoding="utf-8-sig"
    )
    raw.columns = [str(col).strip() for col in raw.columns]
    raw_rows = int(len(raw))

    counts = {key: 0 for key in COUNT_KEYS}

    # R1 normalisation + R2 de-duplication (keep first occurrence in raw order).
    seen_ids = set()
    candidate_rows = []
    for record in raw.to_dict(orient="records"):
        row = {col: clean_text(record.get(col)) for col in raw.columns}
        cid = row.get("customer_id")
        if cid is not None:
            if cid in seen_ids:
                counts["duplicates_removed"] += 1
                continue
            seen_ids.add(cid)
        candidate_rows.append(row)

    cleaned_rows = []
    for row in candidate_rows:
        cid = row.get("customer_id")
        if cid is None:
            counts["dropped_missing_customer_id"] += 1
            continue

        # R3: signup_date
        signup_raw = row.get("signup_date")
        signup_date = (
            parse_signup_date(signup_raw) if signup_raw is not None else None
        )
        if signup_date is None:
            counts["dropped_signup_date"] += 1
            continue

        # R4: plan
        plan_raw = row.get("plan")
        plan = PLAN_MAP.get(plan_raw.lower()) if plan_raw is not None else None
        if plan is None:
            counts["dropped_plan"] += 1
            continue

        # R5: contract_type
        contract_raw = row.get("contract_type")
        contract_type = (
            CONTRACT_TYPE_MAP.get(contract_raw.lower())
            if contract_raw is not None
            else None
        )
        if contract_type is None:
            counts["dropped_contract_type"] += 1
            continue

        # R6: monthly_fee
        fee_raw = row.get("monthly_fee")
        monthly_fee = (
            parse_monthly_fee(fee_raw) if fee_raw is not None else None
        )
        if monthly_fee is None or monthly_fee <= 0 or monthly_fee > 500:
            counts["dropped_monthly_fee"] += 1
            continue

        # R7: tenure_months
        tenure_raw = row.get("tenure_months")
        tenure_months = (
            parse_tenure_months(tenure_raw) if tenure_raw is not None else None
        )
        if (
            tenure_months is None
            or tenure_months < 0
            or tenure_months > 120
        ):
            counts["dropped_tenure_months"] += 1
            continue

        # R8: support_tickets (missing means 0)
        tickets_raw = row.get("support_tickets")
        if tickets_raw is None:
            support_tickets = 0
        else:
            support_tickets = parse_whole_number(tickets_raw)
            if (
                support_tickets is None
                or support_tickets < 0
                or support_tickets > 100
            ):
                counts["dropped_support_tickets"] += 1
                continue

        # R9: satisfaction_score (invalid -> missing, keep the row)
        sat_raw = row.get("satisfaction_score")
        satisfaction = (
            parse_whole_number(sat_raw) if sat_raw is not None else None
        )
        if satisfaction is None or satisfaction < 1 or satisfaction > 5:
            satisfaction = None
            counts["satisfaction_score_set_missing"] += 1

        # R10: churned
        churn_raw = row.get("churned")
        churned = (
            CHURNED_MAP.get(churn_raw.lower()) if churn_raw is not None else None
        )
        if churned is None:
            counts["dropped_churned"] += 1
            continue

        # R11: lifetime_value
        lifetime_value = round(monthly_fee * tenure_months, 2)

        cleaned_rows.append(
            {
                "customer_id": cid,
                "signup_date": signup_date,
                "plan": plan,
                "contract_type": contract_type,
                "monthly_fee": monthly_fee,
                "tenure_months": tenure_months,
                "support_tickets": support_tickets,
                "satisfaction_score": satisfaction,
                "churned": churned,
                "lifetime_value": lifetime_value,
            }
        )

    # R12: exact columns, dtypes, sort order; write CSV with header, no index.
    cleaned_df = pd.DataFrame(cleaned_rows, columns=OUTPUT_COLUMNS)
    cleaned_df["monthly_fee"] = cleaned_df["monthly_fee"].astype("float64")
    cleaned_df["tenure_months"] = cleaned_df["tenure_months"].astype("int64")
    cleaned_df["support_tickets"] = cleaned_df["support_tickets"].astype("int64")
    cleaned_df["satisfaction_score"] = cleaned_df["satisfaction_score"].astype("Int64")
    cleaned_df["churned"] = cleaned_df["churned"].astype("int64")
    cleaned_df["lifetime_value"] = cleaned_df["lifetime_value"].astype("float64")
    cleaned_df = cleaned_df.sort_values("customer_id", kind="stable").reset_index(
        drop=True
    )
    cleaned_df.to_csv(output_path, index=False)

    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": int(len(cleaned_df)),
    }
    summary.update({key: int(value) for key, value in counts.items()})
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)


if __name__ == "__main__":
    main()
