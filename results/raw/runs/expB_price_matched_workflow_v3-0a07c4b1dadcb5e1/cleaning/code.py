import json
import math
import os
import re
from datetime import datetime

import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}
DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y")
PLAN_MAP = {
    "basic": "Basic", "basic plan": "Basic",
    "standard": "Standard", "std": "Standard", "standard plan": "Standard",
    "premium": "Premium", "prem": "Premium", "premium plan": "Premium",
}
CONTRACT_MAP = {
    "monthly": "Monthly", "month-to-month": "Monthly", "m2m": "Monthly",
    "annual": "Annual", "yearly": "Annual", "1 year": "Annual",
}
CHURN_TRUE = {"yes", "y", "true", "1", "churned"}
CHURN_FALSE = {"no", "n", "false", "0", "active"}
OUTPUT_COLUMNS = [
    "customer_id", "signup_date", "plan", "contract_type", "monthly_fee",
    "tenure_months", "support_tickets", "satisfaction_score", "churned",
    "lifetime_value",
]


def normalize(value):
    """R1: strip whitespace; map missing tokens (case-insensitive) to None."""
    if value is None:
        return None
    text = str(value).strip()
    return None if text.lower() in MISSING_TOKENS else text


def parse_signup_date(text):
    """R3: try each allowed format exactly; return YYYY-MM-DD or None."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_monthly_fee(text):
    """R6: strip '$', 'USD' (any case) and ',' then parse as a finite number."""
    cleaned = text.replace("$", "")
    cleaned = re.sub(r"usd", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace(",", "").strip()
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def parse_whole_number(text):
    """Parse a string as a finite whole number; return int or None."""
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or not value.is_integer():
        return None
    return int(value)


def parse_tenure(text):
    """R7: drop a trailing 'month'/'months' word, then parse a whole number."""
    stripped = re.sub(r"\s*months?\s*$", "", text, flags=re.IGNORECASE).strip()
    if not stripped:
        return None
    return parse_whole_number(stripped)


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)

    # R1: read every column as text, keep raw strings (no automatic NaN casting).
    raw = pd.read_csv(
        os.path.join(input_dir, "raw.csv"),
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    counts = {
        "dropped_missing_customer_id": 0,
        "duplicates_removed": 0,
        "dropped_signup_date": 0,
        "dropped_plan": 0,
        "dropped_contract_type": 0,
        "dropped_monthly_fee": 0,
        "dropped_tenure_months": 0,
        "dropped_support_tickets": 0,
        "satisfaction_already_missing": 0,
        "satisfaction_set_missing": 0,
        "dropped_churned": 0,
    }

    records = raw.to_dict("records")
    seen_ids = set()
    rows = []

    for record in records:
        rec = {key: normalize(value) for key, value in record.items()}

        # R2: deduplicate on customer_id before any other row filter; keep first.
        customer_id = rec.get("customer_id")
        if customer_id is None:
            counts["dropped_missing_customer_id"] += 1
            continue
        if customer_id in seen_ids:
            counts["duplicates_removed"] += 1
            continue
        seen_ids.add(customer_id)

        # R3: signup_date
        signup_raw = rec.get("signup_date")
        signup_date = parse_signup_date(signup_raw) if signup_raw is not None else None
        if signup_date is None:
            counts["dropped_signup_date"] += 1
            continue

        # R4: plan
        plan_raw = rec.get("plan")
        plan = PLAN_MAP.get(plan_raw.lower()) if plan_raw is not None else None
        if plan is None:
            counts["dropped_plan"] += 1
            continue

        # R5: contract_type
        contract_raw = rec.get("contract_type")
        contract_type = (
            CONTRACT_MAP.get(contract_raw.lower()) if contract_raw is not None else None
        )
        if contract_type is None:
            counts["dropped_contract_type"] += 1
            continue

        # R6: monthly_fee
        fee_raw = rec.get("monthly_fee")
        monthly_fee = parse_monthly_fee(fee_raw) if fee_raw is not None else None
        if monthly_fee is None or monthly_fee <= 0 or monthly_fee > 500:
            counts["dropped_monthly_fee"] += 1
            continue

        # R7: tenure_months
        tenure_raw = rec.get("tenure_months")
        tenure_months = parse_tenure(tenure_raw) if tenure_raw is not None else None
        if tenure_months is None or tenure_months < 0 or tenure_months > 120:
            counts["dropped_tenure_months"] += 1
            continue

        # R8: support_tickets (missing means 0)
        tickets_raw = rec.get("support_tickets")
        if tickets_raw is None:
            support_tickets = 0
        else:
            support_tickets = parse_whole_number(tickets_raw)
            if support_tickets is None or support_tickets < 0 or support_tickets > 100:
                counts["dropped_support_tickets"] += 1
                continue

        # R9: satisfaction_score (invalid -> missing, keep the row)
        satisfaction_raw = rec.get("satisfaction_score")
        if satisfaction_raw is None:
            satisfaction_score = None
            counts["satisfaction_already_missing"] += 1
        else:
            parsed = parse_whole_number(satisfaction_raw)
            if parsed is not None and 1 <= parsed <= 5:
                satisfaction_score = parsed
            else:
                satisfaction_score = None
                counts["satisfaction_set_missing"] += 1

        # R10: churned
        churned_raw = rec.get("churned")
        churned = None
        if churned_raw is not None:
            lowered = churned_raw.lower()
            if lowered in CHURN_TRUE:
                churned = 1
            elif lowered in CHURN_FALSE:
                churned = 0
        if churned is None:
            counts["dropped_churned"] += 1
            continue

        # R11: lifetime value
        lifetime_value = round(monthly_fee * tenure_months, 2)

        rows.append(
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

    cleaned = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    if len(cleaned) > 0:
        cleaned["tenure_months"] = cleaned["tenure_months"].astype("int64")
        cleaned["support_tickets"] = cleaned["support_tickets"].astype("int64")
        cleaned["churned"] = cleaned["churned"].astype("int64")
        cleaned["satisfaction_score"] = cleaned["satisfaction_score"].astype("Int64")

    # R12: exact column order, sorted by customer_id ascending, header, no index.
    cleaned = cleaned.sort_values("customer_id", kind="mergesort").reset_index(drop=True)
    cleaned = cleaned[OUTPUT_COLUMNS]
    cleaned.to_csv(os.path.join(output_dir, "cleaned.csv"), index=False, na_rep="")

    summary = {"raw_rows": int(len(raw)), "cleaned_rows": int(len(cleaned))}
    summary.update(counts)
    with open(os.path.join(output_dir, "cleaning_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    print("cleaning done: raw_rows=%d cleaned_rows=%d" % (summary["raw_rows"], summary["cleaned_rows"]))


if __name__ == "__main__":
    main()
