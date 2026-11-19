"""Cleaning stage of the customer_churn workflow (prompt v3).

Reads raw.csv from INPUT_DIR, applies rules R1-R12, writes cleaned.csv and
cleaning_summary.json to OUTPUT_DIR.
"""

import json
import math
import os
import re
from datetime import datetime

import pandas as pd

MISSING_TOKENS = {'', 'na', 'n/a', 'null', 'none', '-'}

DATE_FORMATS = [
    '%Y-%m-%d',   # YYYY-MM-DD
    '%m/%d/%Y',   # MM/DD/YYYY (month first)
    '%d-%b-%Y',   # DD-Mon-YYYY, e.g. 05-Mar-2024
    '%Y/%m/%d',   # YYYY/MM/DD
    '%B %d, %Y',  # Month D, YYYY, e.g. March 5, 2024
]

PLAN_MAP = {
    'basic': 'Basic', 'basic plan': 'Basic',
    'standard': 'Standard', 'std': 'Standard', 'standard plan': 'Standard',
    'premium': 'Premium', 'prem': 'Premium', 'premium plan': 'Premium',
}

CONTRACT_MAP = {
    'monthly': 'Monthly', 'month-to-month': 'Monthly', 'm2m': 'Monthly',
    'annual': 'Annual', 'yearly': 'Annual', '1 year': 'Annual',
}

CHURN_MAP = {
    'yes': 1, 'y': 1, 'true': 1, '1': 1, 'churned': 1,
    'no': 0, 'n': 0, 'false': 0, '0': 0, 'active': 0,
}

OUTPUT_COLUMNS = [
    'customer_id', 'signup_date', 'plan', 'contract_type', 'monthly_fee',
    'tenure_months', 'support_tickets', 'satisfaction_score', 'churned',
    'lifetime_value',
]


def parse_date(value):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def parse_monthly_fee(value):
    text = re.sub(r'usd', '', value, flags=re.IGNORECASE)
    text = text.replace('$', '').replace(',', '').strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def parse_whole_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or not number.is_integer():
        return None
    return int(number)


def parse_tenure_months(value):
    text = re.sub(r'\s*months?\s*$', '', value, flags=re.IGNORECASE).strip()
    return parse_whole_number(text)


def main():
    input_dir = os.environ['INPUT_DIR']
    output_dir = os.environ['OUTPUT_DIR']
    os.makedirs(output_dir, exist_ok=True)

    counts = {
        'duplicates_removed': 0,
        'dropped_missing_customer_id': 0,
        'dropped_signup_date': 0,
        'dropped_plan': 0,
        'dropped_contract_type': 0,
        'dropped_monthly_fee': 0,
        'dropped_tenure_months': 0,
        'dropped_support_tickets': 0,
        'satisfaction_set_missing': 0,
        'dropped_churned': 0,
    }

    # R1: read every column as text, strip whitespace, normalise missing tokens.
    df = pd.read_csv(
        os.path.join(input_dir, 'raw.csv'),
        dtype=str, keep_default_na=False, na_filter=False,
    )
    df.columns = [str(c).strip() for c in df.columns]
    df = df.apply(lambda col: col.str.strip())
    df = df.apply(lambda col: col.map(
        lambda v: None if v.lower() in MISSING_TOKENS else v))
    df = df.where(df.notna(), None)
    raw_rows = int(len(df))

    # R2: drop duplicate customer_id rows before any other row filter.
    before = len(df)
    df = df.drop_duplicates(subset='customer_id', keep='first')
    counts['duplicates_removed'] = int(before - len(df))

    # customer_id is not nullable in the target schema.
    missing_id = df['customer_id'].isna()
    counts['dropped_missing_customer_id'] = int(missing_id.sum())
    df = df[~missing_id]

    records = []
    for rec in df.to_dict('records'):
        # R3: signup_date (exactly the five allowed formats).
        value = rec['signup_date']
        parsed = parse_date(value) if value is not None else None
        if parsed is None:
            counts['dropped_signup_date'] += 1
            continue
        signup_date = parsed.strftime('%Y-%m-%d')

        # R4: plan.
        value = rec['plan']
        plan = PLAN_MAP.get(value.lower()) if value is not None else None
        if plan is None:
            counts['dropped_plan'] += 1
            continue

        # R5: contract_type.
        value = rec['contract_type']
        contract = CONTRACT_MAP.get(value.lower()) if value is not None else None
        if contract is None:
            counts['dropped_contract_type'] += 1
            continue

        # R6: monthly_fee.
        value = rec['monthly_fee']
        fee = parse_monthly_fee(value) if value is not None else None
        if fee is None or fee <= 0 or fee > 500:
            counts['dropped_monthly_fee'] += 1
            continue

        # R7: tenure_months.
        value = rec['tenure_months']
        tenure = parse_tenure_months(value) if value is not None else None
        if tenure is None or tenure < 0 or tenure > 120:
            counts['dropped_tenure_months'] += 1
            continue

        # R8: support_tickets (missing -> 0).
        value = rec['support_tickets']
        if value is None:
            tickets = 0
        else:
            tickets = parse_whole_number(value)
            if tickets is None or tickets < 0 or tickets > 100:
                counts['dropped_support_tickets'] += 1
                continue

        # R9: satisfaction_score (invalid -> missing, keep the row).
        value = rec['satisfaction_score']
        satisfaction = None
        if value is not None:
            parsed_sat = parse_whole_number(value)
            if parsed_sat is not None and 1 <= parsed_sat <= 5:
                satisfaction = parsed_sat
            else:
                counts['satisfaction_set_missing'] += 1

        # R10: churned.
        value = rec['churned']
        churned = CHURN_MAP.get(value.lower()) if value is not None else None
        if churned is None:
            counts['dropped_churned'] += 1
            continue

        # R11: lifetime_value.
        lifetime_value = round(fee * tenure, 2)

        records.append({
            'customer_id': rec['customer_id'],
            'signup_date': signup_date,
            'plan': plan,
            'contract_type': contract,
            'monthly_fee': fee,
            'tenure_months': tenure,
            'support_tickets': tickets,
            'satisfaction_score': satisfaction,
            'churned': churned,
            'lifetime_value': lifetime_value,
        })

    # R12: column order, sort by customer_id, write CSV (no index).
    out = pd.DataFrame(records, columns=OUTPUT_COLUMNS)
    out = out.sort_values('customer_id', ascending=True).reset_index(drop=True)
    out['tenure_months'] = out['tenure_months'].astype(int)
    out['support_tickets'] = out['support_tickets'].astype(int)
    out['churned'] = out['churned'].astype(int)
    out['satisfaction_score'] = out['satisfaction_score'].astype('Int64')
    out['lifetime_value'] = out['lifetime_value'].map(lambda x: f'{x:.2f}')

    output_filename = 'cleaned.csv'
    out.to_csv(os.path.join(output_dir, output_filename), index=False)

    summary = {
        'output_filename': output_filename,
        'raw_rows': raw_rows,
        'cleaned_rows': int(len(out)),
        'satisfaction_missing_total': int(out['satisfaction_score'].isna().sum()),
    }
    summary.update(counts)
    with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as fh:
        json.dump(summary, fh, indent=2)

    print(f'cleaning done: {raw_rows} raw rows -> {len(out)} cleaned rows')


if __name__ == '__main__':
    main()
