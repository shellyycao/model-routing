import os
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions for each cleaning rule
# ---------------------------------------------------------------------------

def strip_and_normalise(df):
    """R1 – strip whitespace and convert defined missing tokens to NaN."""
    missing_tokens = {'', 'na', 'n/a', 'null', 'none', '-'}
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.replace({v: np.nan for v in missing_tokens})
    return df

def parse_signup_date(value):
    """R3 – try the allowed date formats, return YYYY‑MM‑DD string or None."""
    if pd.isna(value):
        return None
    value = value.strip()
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            # %b expects Jan, Feb … case‑insensitive, but we normalise the string
            dt = datetime.strptime(value, fmt)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            continue
    return None

def map_plan(value):
    """R4 – map various textual representations to the three canonical plans."""
    if pd.isna(value):
        return None
    v = value.strip().lower()
    mapping = {
        'basic': 'Basic',
        'basic plan': 'Basic',
        'standard': 'Standard',
        'std': 'Standard',
        'standard plan': 'Standard',
        'premium': 'Premium',
        'prem': 'Premium',
        'premium plan': 'Premium'
    }
    return mapping.get(v)

def map_contract(value):
    """R5 – map contract type strings to Monthly or Annual."""
    if pd.isna(value):
        return None
    v = value.strip().lower()
    mapping = {
        'monthly': 'Monthly',
        'month-to-month': 'Monthly',
        'm2m': 'Monthly',
        'annual': 'Annual',
        'yearly': 'Annual',
        '1 year': 'Annual'
    }
    return mapping.get(v)

def parse_monthly_fee(value):
    """R6 – clean currency symbols/commas and parse as float, enforce limits."""
    if pd.isna(value):
        return None
    # remove $, USD, commas and surrounding spaces
    cleaned = re.sub(r"\$|USD|,", "", str(value), flags=re.IGNORECASE).strip()
    try:
        fee = float(cleaned)
        if fee <= 0 or fee > 500:
            return None
        return fee
    except Exception:
        return None

def parse_tenure(value):
    """R7 – strip the word month(s) and parse as integer within limits."""
    if pd.isna(value):
        return None
    v = re.sub(r"(?i)\s*months?\s*", "", str(value)).strip()
    try:
        months = int(float(v))  # allow "47.0" style strings
        if months < 0 or months > 120:
            return None
        return months
    except Exception:
        return None

def parse_support_tickets(value):
    """R8 – missing → 0, otherwise integer within limits."""
    if pd.isna(value):
        return 0
    try:
        tickets = int(float(str(value).strip()))
        if tickets < 0 or tickets > 100:
            return None
        return tickets
    except Exception:
        return None

def parse_satisfaction(value):
    """R9 – integer 1‑5, otherwise set to missing (None)."""
    if pd.isna(value):
        return None
    try:
        score = int(float(str(value).strip()))
        if 1 <= score <= 5:
            return score
        else:
            return None
    except Exception:
        return None

def map_churned(value):
    """R10 – map various truthy/falsy strings to 1/0, drop if not mappable."""
    if pd.isna(value):
        return None
    v = value.strip().lower()
    truthy = {'yes', 'y', 'true', '1', 'churned'}
    falsy = {'no', 'n', 'false', '0', 'active'}
    if v in truthy:
        return 1
    if v in falsy:
        return 0
    return None

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get('INPUT_DIR')
    output_dir = os.environ.get('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('INPUT_DIR and OUTPUT_DIR environment variables must be set')

    raw_path = os.path.join(input_dir, 'raw.csv')
    df_raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_values=[])
    raw_rows = len(df_raw)

    # R1 – strip whitespace and normalise missing tokens
    df = strip_and_normalise(df_raw)

    # R2 – drop duplicate customer_id, keep first occurrence
    before_dup = len(df)
    df = df.drop_duplicates(subset=['customer_id'], keep='first')
    dup_removed = before_dup - len(df)

    # Prepare summary counters
    summary = {
        'raw_rows': raw_rows,
        'duplicates_removed': dup_removed,
        'rows_dropped_signup_date': 0,
        'rows_dropped_plan': 0,
        'rows_dropped_contract_type': 0,
        'rows_dropped_monthly_fee': 0,
        'rows_dropped_tenure_months': 0,
        'rows_dropped_support_tickets': 0,
        'rows_dropped_churned': 0,
        'cleaned_rows': 0
    }

    cleaned_records = []
    for _, row in df.iterrows():
        cust_id = row.get('customer_id')
        if pd.isna(cust_id):
            # customer_id is required – drop silently (not counted in any rule)
            continue

        # R3 – signup_date
        signup = parse_signup_date(row.get('signup_date'))
        if not signup:
            summary['rows_dropped_signup_date'] += 1
            continue

        # R4 – plan
        plan = map_plan(row.get('plan'))
        if not plan:
            summary['rows_dropped_plan'] += 1
            continue

        # R5 – contract_type
        contract = map_contract(row.get('contract_type'))
        if not contract:
            summary['rows_dropped_contract_type'] += 1
            continue

        # R6 – monthly_fee
        fee = parse_monthly_fee(row.get('monthly_fee'))
        if fee is None:
            summary['rows_dropped_monthly_fee'] += 1
            continue

        # R7 – tenure_months
        tenure = parse_tenure(row.get('tenure_months'))
        if tenure is None:
            summary['rows_dropped_tenure_months'] += 1
            continue

        # R8 – support_tickets
        tickets = parse_support_tickets(row.get('support_tickets'))
        if tickets is None:
            summary['rows_dropped_support_tickets'] += 1
            continue

        # R9 – satisfaction_score (do NOT drop)
        satisfaction = parse_satisfaction(row.get('satisfaction_score'))
        # keep None for missing/invalid

        # R10 – churned
        churn = map_churned(row.get('churned'))
        if churn is None:
            summary['rows_dropped_churned'] += 1
            continue

        # R11 – lifetime_value
        lifetime = round(fee * tenure, 2)

        cleaned_records.append({
            'customer_id': cust_id.strip(),
            'signup_date': signup,
            'plan': plan,
            'contract_type': contract,
            'monthly_fee': fee,
            'tenure_months': tenure,
            'support_tickets': tickets,
            'satisfaction_score': satisfaction,
            'churned': churn,
            'lifetime_value': lifetime
        })

    summary['cleaned_rows'] = len(cleaned_records)

    # Create DataFrame with required column order
    cols = ['customer_id', 'signup_date', 'plan', 'contract_type', 'monthly_fee',
            'tenure_months', 'support_tickets', 'satisfaction_score', 'churned', 'lifetime_value']
    df_clean = pd.DataFrame(cleaned_records, columns=cols)

    # Sort by customer_id ascending (string sort)
    df_clean = df_clean.sort_values(by='customer_id')

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    df_clean.to_csv(cleaned_path, index=False, float_format='%.2f', na_rep='')

    # Write cleaning summary JSON
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
