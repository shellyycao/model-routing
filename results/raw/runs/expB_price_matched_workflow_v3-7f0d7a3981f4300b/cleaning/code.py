import os
import json
from datetime import datetime

import numpy as np
import pandas as pd

INPUT_DIR = os.environ['INPUT_DIR']
OUTPUT_DIR = os.environ['OUTPUT_DIR']
os.makedirs(OUTPUT_DIR, exist_ok=True)

MISSING_TOKENS = {'', 'na', 'n/a', 'null', 'none', '-'}
DATE_FORMATS = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
BUILDING_MAP = {
    'residential': 'Residential', 'res': 'Residential', 'resi': 'Residential',
    'commercial': 'Commercial', 'comm': 'Commercial',
    'industrial': 'Industrial', 'ind': 'Industrial',
}
TARIFF_MAP = {'peak': 'peak', 'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'}


def normalize(value):
    if value is None:
        return np.nan
    s = str(value).strip()
    return np.nan if s.lower() in MISSING_TOKENS else s


def parse_date(value):
    if not isinstance(value, str):
        return np.nan
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return np.nan


def parse_energy(value):
    if not isinstance(value, str):
        return np.nan
    t = value.replace(',', '').strip()
    low = t.lower()
    factor = 1.0
    if low.endswith('mwh'):
        t = t[:-3].strip()
        factor = 1000.0
    elif low.endswith('kwh'):
        t = t[:-3].strip()
    try:
        return float(t) * factor
    except ValueError:
        return np.nan


def parse_temperature(value):
    if not isinstance(value, str):
        return np.nan
    t = value.strip()
    low = t.lower()
    is_fahrenheit = False
    if low.endswith('f'):
        is_fahrenheit = True
        t = t[:-1]
    elif low.endswith('c'):
        t = t[:-1]
    t = t.strip()
    if t.endswith('°'):
        t = t[:-1].strip()
    try:
        v = float(t)
    except ValueError:
        return np.nan
    if is_fahrenheit:
        v = (v - 32.0) * 5.0 / 9.0
    if v < -40.0 or v > 50.0:
        return np.nan
    return round(v, 1)


def main():
    raw_path = os.path.join(INPUT_DIR, 'raw.csv')
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_filter=False)
    raw_rows = int(len(df))

    # R1: read as text, strip whitespace, normalise missing tokens to NaN
    for col in df.columns:
        df[col] = df[col].map(normalize)

    # R2: remove duplicate reading_id before any other row filter (keep first in raw order)
    before = len(df)
    df = df.drop_duplicates(subset='reading_id', keep='first')
    duplicates_removed = int(before - len(df))

    # R3: parse reading_date with the five allowed formats; drop missing/unparseable
    df['reading_date'] = df['reading_date'].map(parse_date)
    mask = df['reading_date'].notna()
    dropped_reading_date = int((~mask).sum())
    df = df[mask].copy()

    # R4: meter_id to upper case; drop missing
    mask = df['meter_id'].notna()
    dropped_meter_id = int((~mask).sum())
    df = df[mask].copy()
    df['meter_id'] = df['meter_id'].str.upper()

    # R5: building_type canonical mapping (case-insensitive); drop unmappable/missing
    df['building_type'] = df['building_type'].map(
        lambda v: BUILDING_MAP.get(v.lower(), np.nan) if isinstance(v, str) else np.nan)
    mask = df['building_type'].notna()
    dropped_building_type = int((~mask).sum())
    df = df[mask].copy()

    # R6: tariff canonical mapping (case-insensitive); drop unmappable/missing
    df['tariff'] = df['tariff'].map(
        lambda v: TARIFF_MAP.get(v.lower(), np.nan) if isinstance(v, str) else np.nan)
    mask = df['tariff'].notna()
    dropped_tariff = int((~mask).sum())
    df = df[mask].copy()

    # R7: energy -> energy_kwh (commas removed, MWh/kWh units handled); drop invalid/out of range
    df['energy_kwh'] = df['energy'].map(parse_energy)
    mask = (df['energy_kwh'].notna()
            & (df['energy_kwh'] >= 0.0)
            & (df['energy_kwh'] <= 100000.0))
    dropped_energy = int((~mask).sum())
    df = df[mask].copy()
    df['energy_kwh'] = df['energy_kwh'].round(2)

    # R8: temperature -> temperature_c; invalid or out-of-range becomes missing but row is kept
    df['temperature_c'] = df['temperature'].map(parse_temperature)
    temperature_c_missing = int(df['temperature_c'].isna().sum())

    # R9: final column order, sort by reading_id ascending, write CSV (no index)
    out = df[['reading_id', 'reading_date', 'meter_id', 'building_type',
              'tariff', 'energy_kwh', 'temperature_c']].sort_values('reading_id')
    cleaned_rows = int(len(out))
    out.to_csv(os.path.join(OUTPUT_DIR, 'cleaned.csv'), index=False, na_rep='')

    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed': duplicates_removed,
        'dropped_reading_date': dropped_reading_date,
        'dropped_meter_id': dropped_meter_id,
        'dropped_building_type': dropped_building_type,
        'dropped_tariff': dropped_tariff,
        'dropped_energy': dropped_energy,
        'temperature_c_missing': temperature_c_missing,
    }
    with open(os.path.join(OUTPUT_DIR, 'cleaning_summary.json'), 'w') as fh:
        json.dump(summary, fh, indent=2)


if __name__ == '__main__':
    main()
