import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

# ---------- Helper functions ----------

def is_missing(val):
    if pd.isna(val):
        return True
    if isinstance(val, str):
        return val.strip().lower() in {'', 'na', 'n/a', 'null', 'none', '-'}
    return False

def clean_missing(df):
    for col in df.columns:
        df[col] = df[col].apply(lambda x: np.nan if is_missing(x) else x)
    return df

def parse_date(val):
    if pd.isna(val):
        return np.nan
    val = val.strip()
    formats = [
        "%Y-%m-%d",          # 2024-01-01
        "%m/%d/%Y",          # 01/02/2024
        "%d-%b-%Y",          # 05-Mar-2024
        "%Y/%m/%d",          # 2024/01/02
        "%B %d, %Y",         # January 5, 2024
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return np.nan

def map_building_type(val):
    if pd.isna(val):
        return np.nan
    mapping = {
        'residential': 'Residential',
        'commercial': 'Commercial',
        'industrial': 'Industrial',
        'res': 'Residential',
        'resi': 'Residential',
        'comm': 'Commercial',
        'ind': 'Industrial',
    }
    key = val.strip().lower()
    return mapping.get(key, np.nan)

def map_tariff(val):
    if pd.isna(val):
        return np.nan
    key = val.strip().lower().replace(' ', '')
    if key == 'peak':
        return 'peak'
    if key in {'offpeak', 'off-peak'}:
        return 'off-peak'
    return np.nan

def convert_energy(val):
    if pd.isna(val):
        return np.nan
    s = str(val).replace(',', '').strip()
    # detect unit
    low = s.lower()
    if low.endswith('mwh'):
        num_part = low[:-3].strip()
        try:
            num = float(num_part)
            return num * 1000.0
        except ValueError:
            return np.nan
    if low.endswith('kwh'):
        num_part = low[:-3].strip()
        try:
            return float(num_part)
        except ValueError:
            return np.nan
    # no unit, assume kWh
    try:
        return float(s)
    except ValueError:
        return np.nan

def convert_temperature(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    if not s:
        return np.nan
    # remove degree sign if present
    s = s.replace('°', '')
    low = s.lower()
    if low.endswith('f'):
        num_part = low[:-1].strip()
        try:
            f = float(num_part)
            c = (f - 32) * 5.0 / 9.0
        except ValueError:
            return np.nan
    elif low.endswith('c'):
        num_part = low[:-1].strip()
        try:
            c = float(num_part)
        except ValueError:
            return np.nan
    else:
        # no unit, assume Celsius
        try:
            c = float(s)
        except ValueError:
            return np.nan
    # Validate range
    if c < -40 or c > 50:
        return np.nan
    return round(c, 1)

# ---------- Main cleaning routine ----------

def main():
    input_dir = os.environ.get('INPUT_DIR')
    output_dir = os.environ.get('OUTPUT_DIR')
    raw_path = os.path.join(input_dir, 'raw.csv')
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')

    # Read raw CSV as text, no NA parsing
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)

    # R1: strip whitespace and treat defined strings as missing
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = clean_missing(df)

    # Counters for summary
    summary_counts = {
        'duplicates_removed': 0,
        'invalid_reading_date': 0,
        'missing_meter_id': 0,
        'invalid_building_type': 0,
        'invalid_tariff': 0,
        'invalid_energy': 0,
    }

    # R2: remove duplicate reading_id (keep first)
    dup_mask = df.duplicated(subset='reading_id', keep='first')
    summary_counts['duplicates_removed'] = int(dup_mask.sum())
    df = df[~dup_mask]

    # R3: parse reading_date
    df['reading_date'] = df['reading_date'].apply(parse_date)
    before = len(df)
    df = df.dropna(subset=['reading_date'])
    summary_counts['invalid_reading_date'] = before - len(df)

    # R4: meter_id upper case, drop missing
    df['meter_id'] = df['meter_id'].apply(lambda x: x.upper() if pd.notna(x) else np.nan)
    before = len(df)
    df = df.dropna(subset=['meter_id'])
    summary_counts['missing_meter_id'] = before - len(df)

    # R5: building_type mapping
    df['building_type'] = df['building_type'].apply(map_building_type)
    before = len(df)
    df = df.dropna(subset=['building_type'])
    summary_counts['invalid_building_type'] = before - len(df)

    # R6: tariff mapping
    df['tariff'] = df['tariff'].apply(map_tariff)
    before = len(df)
    df = df.dropna(subset=['tariff'])
    summary_counts['invalid_tariff'] = before - len(df)

    # R7: energy conversion
    df['energy_kwh'] = df['energy'].apply(convert_energy)
    # drop rows with missing/invalid energy or out of bounds
    before = len(df)
    df = df.dropna(subset=['energy_kwh'])
    df = df[(df['energy_kwh'] >= 0) & (df['energy_kwh'] <= 100000)]
    summary_counts['invalid_energy'] = before - len(df)
    df['energy_kwh'] = df['energy_kwh'].round(2)

    # R8: temperature conversion (keep row even if result is NaN)
    df['temperature_c'] = df['temperature'].apply(convert_temperature)
    # Round already done in conversion; ensure one decimal if not NaN
    df['temperature_c'] = df['temperature_c'].apply(lambda x: round(x, 1) if pd.notna(x) else np.nan)

    # R9: select and order columns, sort by reading_id
    final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
    df = df[final_cols]
    df = df.sort_values('reading_id')

    # Format numeric columns as required strings (energy 2 decimals, temperature 1 decimal, empty if NaN)
    df['energy_kwh'] = df['energy_kwh'].apply(lambda x: f"{x:.2f}")
    df['temperature_c'] = df['temperature_c'].apply(lambda x: '' if pd.isna(x) else f"{x:.1f}")

    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False)

    # Prepare summary JSON
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': len(df),
    }
    summary.update(summary_counts)
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
