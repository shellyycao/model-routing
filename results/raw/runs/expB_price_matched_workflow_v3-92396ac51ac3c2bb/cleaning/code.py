import os
import json
from datetime import date

import numpy as np
import pandas as pd


INPUT_NAME = 'raw.csv'
output_filename = 'cleaned.csv'
SUMMARY_NAME = 'cleaning_summary.json'

RAW_COLUMNS = [
    'reading_id',
    'reading_date',
    'meter_id',
    'building_type',
    'tariff',
    'energy',
    'temperature',
]
OUT_COLUMNS = [
    'reading_id',
    'reading_date',
    'meter_id',
    'building_type',
    'tariff',
    'energy_kwh',
    'temperature_c',
]

MISSING_TOKENS = {'', 'na', 'n/a', 'null', 'none', '-'}
MONTH_ABBR = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}
MONTH_FULL = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5,
    'june': 6, 'july': 7, 'august': 8, 'september': 9, 'october': 10,
    'november': 11, 'december': 12,
}
BUILDING_MAP = {
    'residential': 'Residential',
    'res': 'Residential',
    'resi': 'Residential',
    'commercial': 'Commercial',
    'comm': 'Commercial',
    'industrial': 'Industrial',
    'ind': 'Industrial',
}
TARIFF_MAP = {
    'peak': 'peak',
    'off-peak': 'off-peak',
    'offpeak': 'off-peak',
    'off peak': 'off-peak',
}


def is_missing(value):
    return value is None or pd.isna(value)


def normalize_cell(value):
    if is_missing(value):
        return pd.NA
    text = str(value).strip()
    if text.lower() in MISSING_TOKENS:
        return pd.NA
    return text


def all_digits(text):
    return text != '' and all(ch in '0123456789' for ch in text)


def safe_date(year, month, day):
    try:
        return date(year, month, day).isoformat()
    except (TypeError, ValueError):
        return pd.NA


def parse_reading_date(value):
    if is_missing(value):
        return pd.NA
    s = str(value)

    if len(s) == 10 and s[4] == '-' and s[7] == '-':
        y, m, d = s[:4], s[5:7], s[8:10]
        if all_digits(y) and all_digits(m) and all_digits(d):
            return safe_date(int(y), int(m), int(d))

    if len(s) == 10 and s[2] == '/' and s[5] == '/':
        m, d, y = s[:2], s[3:5], s[6:10]
        if all_digits(m) and all_digits(d) and all_digits(y):
            return safe_date(int(y), int(m), int(d))

    if len(s) == 11 and s[2] == '-' and s[6] == '-':
        d, mon, y = s[:2], s[3:6].lower(), s[7:11]
        if all_digits(d) and all_digits(y) and mon in MONTH_ABBR:
            return safe_date(int(y), MONTH_ABBR[mon], int(d))

    if len(s) == 10 and s[4] == '/' and s[7] == '/':
        y, m, d = s[:4], s[5:7], s[8:10]
        if all_digits(y) and all_digits(m) and all_digits(d):
            return safe_date(int(y), int(m), int(d))

    if s.count(',') == 1:
        left, right = s.split(',', 1)
        left = left.strip()
        right = right.strip()
        parts = left.split()
        if len(parts) == 2 and all_digits(right) and len(right) == 4:
            mon = parts[0].lower()
            d = parts[1]
            if mon in MONTH_FULL and all_digits(d):
                return safe_date(int(right), MONTH_FULL[mon], int(d))

    return pd.NA


def parse_energy(value):
    if is_missing(value):
        return pd.NA
    text = str(value).replace(',', '').strip()
    if text == '':
        return pd.NA
    low = text.lower()
    factor = 1.0
    if low.endswith('mwh'):
        factor = 1000.0
        number = text[:-3].strip()
    elif low.endswith('kwh'):
        number = text[:-3].strip()
    else:
        number = text
    try:
        amount = float(number)
    except (TypeError, ValueError):
        return pd.NA
    if not np.isfinite(amount):
        return pd.NA
    amount = amount * factor
    if amount < 0 or amount > 100000:
        return pd.NA
    return round(amount, 2)


def parse_temperature(value):
    if is_missing(value):
        return pd.NA
    text = str(value).strip()
    if text == '':
        return pd.NA
    low = text.lower()
    unit = 'C'
    number = text
    if low.endswith('f'):
        unit = 'F'
        number = text[:-1]
    elif low.endswith('c'):
        unit = 'C'
        number = text[:-1]
    number = number.rstrip()
    if number.endswith('°'):
        number = number[:-1].rstrip()
    try:
        temp = float(number)
    except (TypeError, ValueError):
        return pd.NA
    if not np.isfinite(temp):
        return pd.NA
    if unit == 'F':
        temp = (temp - 32.0) * 5.0 / 9.0
    if temp < -40.0 or temp > 50.0:
        return pd.NA
    return round(temp, 1)


def main():
    input_dir = os.environ['INPUT_DIR']
    output_dir = os.environ['OUTPUT_DIR']
    os.makedirs(output_dir, exist_ok=True)

    raw_path = os.path.join(input_dir, INPUT_NAME)
    out_path = os.path.join(output_dir, output_filename)
    summary_path = os.path.join(output_dir, SUMMARY_NAME)

    raw = pd.read_csv(
        raw_path,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        encoding='utf-8-sig',
    )
    raw_rows = int(len(raw))

    for col in RAW_COLUMNS:
        if col not in raw.columns:
            raw[col] = ''

    work = raw[RAW_COLUMNS].apply(lambda col: col.map(normalize_cell))

    duplicate_mask = work['reading_id'].notna() & work.duplicated(subset=['reading_id'], keep='first')
    duplicates_removed_reading_id = int(duplicate_mask.sum())
    work = work.loc[~duplicate_mask].copy()

    missing_reading_id_mask = work['reading_id'].isna()
    dropped_missing_reading_id = int(missing_reading_id_mask.sum())
    work = work.loc[~missing_reading_id_mask].copy()

    work['reading_date'] = work['reading_date'].map(parse_reading_date)
    before = len(work)
    work = work.loc[work['reading_date'].notna()].copy()
    dropped_reading_date = int(before - len(work))

    work['meter_id'] = work['meter_id'].map(lambda x: pd.NA if is_missing(x) else str(x).upper())
    before = len(work)
    work = work.loc[work['meter_id'].notna()].copy()
    dropped_meter_id = int(before - len(work))

    work['building_type'] = work['building_type'].map(
        lambda x: pd.NA if is_missing(x) else BUILDING_MAP.get(str(x).lower(), pd.NA)
    )
    before = len(work)
    work = work.loc[work['building_type'].notna()].copy()
    dropped_building_type = int(before - len(work))

    work['tariff'] = work['tariff'].map(
        lambda x: pd.NA if is_missing(x) else TARIFF_MAP.get(str(x).lower(), pd.NA)
    )
    before = len(work)
    work = work.loc[work['tariff'].notna()].copy()
    dropped_tariff = int(before - len(work))

    work['energy_kwh'] = work['energy'].map(parse_energy)
    before = len(work)
    work = work.loc[work['energy_kwh'].notna()].copy()
    dropped_energy = int(before - len(work))
    work['energy_kwh'] = pd.to_numeric(work['energy_kwh'], errors='coerce')

    work['temperature_c'] = work['temperature'].map(parse_temperature)
    temperature_set_missing = int(work['temperature_c'].isna().sum())
    work['temperature_c'] = pd.to_numeric(work['temperature_c'], errors='coerce')

    cleaned = work[OUT_COLUMNS].sort_values('reading_id', kind='mergesort').reset_index(drop=True)
    cleaned_rows = int(len(cleaned))
    cleaned.to_csv(out_path, index=False, na_rep='')

    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'output_filename': output_filename,
        'rule_counts': {
            'duplicates_removed_reading_id': duplicates_removed_reading_id,
            'dropped_missing_reading_id': dropped_missing_reading_id,
            'dropped_reading_date_missing_or_unparseable': dropped_reading_date,
            'dropped_meter_id_missing': dropped_meter_id,
            'dropped_building_type_missing_or_invalid': dropped_building_type,
            'dropped_tariff_missing_or_invalid': dropped_tariff,
            'dropped_energy_missing_or_invalid': dropped_energy,
            'temperature_set_missing_keep_row': temperature_set_missing,
        },
    }
    with open(summary_path, 'w', encoding='utf-8') as fh:
        json.dump(summary, fh, indent=2)
        fh.write('\n')


if __name__ == '__main__':
    main()
