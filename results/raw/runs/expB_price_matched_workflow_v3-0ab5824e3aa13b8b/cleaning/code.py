import json
import os
import re
from datetime import datetime

import pandas as pd

INPUT_PATH = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
OUTPUT_DIR = os.environ["OUTPUT_DIR"]
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "cleaned.csv")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "cleaning_summary.json")

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

counts = {
    "duplicates_removed": 0,
    "dropped_missing_customer_id": 0,
    "dropped_signup_date": 0,
    "dropped_plan": 0,
    "dropped_contract_type": 0,
    "dropped_monthly_fee": 0,
    "dropped_tenure_months": 0,
    "dropped_support_tickets": 0,
    "dropped_churned": 0,
    "satisfaction_score_set_missing": 0,
}


def parse_signup_date(value):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_whole(value, low, high):
    try:
        num = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if not num.is_integer() or num < low or num > high:
        return None
    return int(num)


def parse_monthly_fee(value):
    text = re.sub(r"usd", "", str(value), flags=re.IGNORECASE)
    text = text.replace("$", "").replace(",", "").strip()
    if not text:
        return None
    try:
        num = float(text)
    except ValueError:
        return None
    if num <= 0 or num > 500:
        return None
    return num


def parse_tenure(value):
    text = re.sub(r"\s*months?\s*$", "", str(value), flags=re.IGNORECASE).strip()
    return parse_whole(text, 0, 120)


def parse_churn(value):
    lowered = str(value).strip().lower()
    if lowered in CHURN_TRUE:
        return 1
    if lowered in CHURN_FALSE:
        return 0
    return None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    raw = pd.read_csv(INPUT_PATH, dtype=str, keep_default_na=False)
    raw_rows = int(len(raw))
    raw.columns = [str(c).strip() for c in raw.columns]

    # R1: strip whitespace from every value and normalise missing tokens.
    for col in raw.columns:
        raw[col] = raw[col].map(lambda v: v.strip() if isinstance(v, str) else v)
        raw[col] = raw[col].map(
            lambda v: pd.NA if isinstance(v, str) and v.lower() in MISSING_TOKENS else v
        )

    # R2: drop duplicate customer_id rows BEFORE any other row filter,
    # keeping the first occurrence in raw-file order.
    before = len(raw)
    raw = raw.drop_duplicates(subset="customer_id", keep="first")
    counts["duplicates_removed"] = int(before - len(raw))

    # customer_id is not nullable in the output schema.
    missing_cid = int(raw["customer_id"].isna().sum())
    if missing_cid:
        counts["dropped_missing_customer_id"] = missing_cid
        raw = raw[raw["customer_id"].notna()]

    records = []
    for row in raw.to_dict("records"):
        # R3: signup_date
        signup = None if pd.isna(row["signup_date"]) else parse_signup_date(row["signup_date"])
        if signup is None:
            counts["dropped_signup_date"] += 1
            continue

        # R4: plan
        plan = None if pd.isna(row["plan"]) else PLAN_MAP.get(row["plan"].lower())
        if plan is None:
            counts["dropped_plan"] += 1
            continue

        # R5: contract_type
        contract = None if pd.isna(row["contract_type"]) else CONTRACT_MAP.get(row["contract_type"].lower())
        if contract is None:
            counts["dropped_contract_type"] += 1
            continue

        # R6: monthly_fee
        fee = None if pd.isna(row["monthly_fee"]) else parse_monthly_fee(row["monthly_fee"])
        if fee is None:
            counts["dropped_monthly_fee"] += 1
            continue

        # R7: tenure_months
        tenure = None if pd.isna(row["tenure_months"]) else parse_tenure(row["tenure_months"])
        if tenure is None:
            counts["dropped_tenure_months"] += 1
            continue

        # R8: support_tickets (missing means 0)
        if pd.isna(row["support_tickets"]):
            tickets = 0
        else:
            tickets = parse_whole(row["support_tickets"], 0, 100)
            if tickets is None:
                counts["dropped_support_tickets"] += 1
                continue

        # R9: satisfaction_score (invalid -> missing, keep the row)
        satisfaction = None if pd.isna(row["satisfaction_score"]) else parse_whole(row["satisfaction_score"], 1, 5)
        if satisfaction is None:
            counts["satisfaction_score_set_missing"] += 1

        # R10: churned
        churned = None if pd.isna(row["churned"]) else parse_churn(row["churned"])
        if churned is None:
            counts["dropped_churned"] += 1
            continue

        records.append({
            "customer_id": row["customer_id"],
            "signup_date": signup,
            "plan": plan,
            "contract_type": contract,
            "monthly_fee": fee,
            "tenure_months": tenure,
            "support_tickets": tickets,
            "satisfaction_score": satisfaction,
            "churned": churned,
        })

    cleaned = pd.DataFrame(records, columns=OUTPUT_COLUMNS[:-1])
    if len(cleaned):
        cleaned["monthly_fee"] = cleaned["monthly_fee"].astype(float)
        cleaned["tenure_months"] = cleaned["tenure_months"].astype("int64")
        cleaned["support_tickets"] = cleaned["support_tickets"].astype("int64")
        cleaned["satisfaction_score"] = cleaned["satisfaction_score"].astype("Int64")
        cleaned["churned"] = cleaned["churned"].astype("int64")
        # R11: lifetime value
        cleaned["lifetime_value"] = (cleaned["monthly_fee"] * cleaned["tenure_months"]).round(2)
        # R12: sort by customer_id ascending (stable)
        cleaned = cleaned.sort_values("customer_id", kind="mergesort")
    cleaned = cleaned.reindex(columns=OUTPUT_COLUMNS)
    cleaned.to_csv(OUTPUT_CSV, index=False)

    summary = {"raw_rows": raw_rows, "cleaned_rows": int(len(cleaned))}
    summary.update({k: int(v) for k, v in counts.items()})
    with open(SUMMARY_PATH, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
