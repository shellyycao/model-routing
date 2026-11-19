import os
import json
import re
import datetime
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------
INPUT_DIR = os.getenv('INPUT_DIR')
OUTPUT_DIR = os.getenv('OUTPUT_DIR')
RAW_PATH = os.path.join(INPUT_DIR, 'raw.csv')
CLEANED_PATH = os.path.join(OUTPUT_DIR, 'cleaned.csv')
SUMMARY_PATH = os.path.join(OUTPUT_DIR, 'cleaning_summary.json')

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
MISSING_VALUES = {'', 'na', 'n/a', 'null', 'none', '-'}

def strip_and_nullify(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from every cell and convert defined missing strings to NaN."""
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.replace(
        to_replace=lambda v: isinstance(v, str) and v.lower() in MISSING_VALUES,
        value=np.nan
    )
    return df

def parse_date(val):
    """Parse a date string using the allowed formats. Return YYYY‑MM‑DD or None."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    formats = [
        '%Y-%m-%d',        # 2024-01-01
        '%m/%d/%Y',        # 01/02/2024 (month first)
        '%d-%b-%Y',        # 05-Mar-2024 (abbr month)
        '%Y/%m/%d',        # 2024/01/03
        '%B %d, %Y'        # January 5, 2024
    ]
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(s, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def convert_energy(val):
    """Convert the raw energy field to a float kWh value.
    Returns None if conversion fails or value out of allowed range.
    """
    if pd.isna(val):
        return None
    s = str(val).replace(',', '').strip()
    # Regex captures number and optional unit (MWh/kWh) ignoring case and spaces
    m = re.match(r'(?i)^([0-9]*\.?[0-9]+)\s*(mwh|kwh)?\s*$', s)
    if not m:
        return None
    number = float(m.group(1))
    unit = m.group(2)
    if unit:
        unit = unit.lower()
    if unit == 'mwh':
        number *= 1000  # convert megawatt‑hours to kilowatt‑hours
    # kWh or missing unit is already kWh
    if number < 0 or number > 100000:
        return None
    return round(number, 2)

def convert_temperature(val):
    """Convert temperature to Celsius, round to 1 decimal.
    Returns np.nan if missing/invalid/out of range.
    """
    if pd.isna(val):
        return np.nan
    s = str(val).replace('°', '').strip()
    m = re.match(r'(?i)^([+-]?[0-9]*\.?[0-9]+)\s*([cf])?\s*$', s)
    if not m:
        return np.nan
    number = float(m.group(1))
    unit = m.group(2)
    if unit:
        unit = unit.lower()
    if unit == 'f':
        c = (number - 32) * 5.0 / 9.0
    else:
        c = number  # already Celsius or no unit
    if c < -40 or c > 50:
        return np.nan
    return round(c, 1)

# ---------------------------------------------------------------------------
# Load raw data (all columns as text)
# ---------------------------------------------------------------------------
raw_df = pd.read_csv(RAW_PATH, dtype=str, keep_default_na=False)
raw_rows = len(raw_df)

# R1 – strip whitespace and normalise missing values
raw_df = strip_and_nullify(raw_df)

# R2 – drop duplicate reading_id, keep first occurrence
pre_dup_rows = len(raw_df)
raw_df = raw_df.drop_duplicates(subset='reading_id', keep='first')
dup_removed = pre_dup_rows - len(raw_df)

# ---------------------------------------------------------------------------
# Row‑level cleaning according to the rules (applied sequentially)
# ---------------------------------------------------------------------------
# R3 – reading_date parsing
raw_df['reading_date'] = raw_df['reading_date'].apply(parse_date)
pre_date_rows = len(raw_df)
raw_df = raw_df.dropna(subset=['reading_date'])
date_dropped = pre_date_rows - len(raw_df)

# R4 – meter_id upper‑casing and non‑missing check
raw_df['meter_id'] = raw_df['meter_id'].str.upper()
pre_meter_rows = len(raw_df)
raw_df = raw_df.dropna(subset=['meter_id'])
meter_dropped = pre_meter_rows - len(raw_df)

# R5 – building_type mapping
building_map = {
    'residential': 'Residential', 'res': 'Residential', 'resi': 'Residential',
    'commercial': 'Commercial', 'comm': 'Commercial',
    'industrial': 'Industrial', 'ind': 'Industrial'
}
raw_df['building_type'] = raw_df['building_type'].str.lower().map(building_map)
pre_build_rows = len(raw_df)
raw_df = raw_df.dropna(subset=['building_type'])
building_dropped = pre_build_rows - len(raw_df)

# R6 – tariff mapping
tariff_map = {
    'peak': 'peak',
    'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'
}
raw_df['tariff'] = raw_df['tariff'].str.lower().map(tariff_map)
pre_tariff_rows = len(raw_df)
raw_df = raw_df.dropna(subset=['tariff'])
tariff_dropped = pre_tariff_rows - len(raw_df)

# R7 – energy conversion to kWh
raw_df['energy_kwh'] = raw_df['energy'].apply(convert_energy)
pre_energy_rows = len(raw_df)
raw_df = raw_df.dropna(subset=['energy_kwh'])
energy_dropped = pre_energy_rows - len(raw_df)

# R8 – temperature conversion (keep row even if result is missing)
raw_df['temperature_c'] = raw_df['temperature'].apply(convert_temperature)
# No row removal; just count how many become missing
temp_missing = raw_df['temperature_c'].isna().sum()

# ---------------------------------------------------------------------------
# Final column selection, ordering and sorting
# ---------------------------------------------------------------------------
final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type',
              'tariff', 'energy_kwh', 'temperature_c']
cleaned_df = raw_df[final_cols].copy()
cleaned_df = cleaned_df.sort_values('reading_id')
cleaned_rows = len(cleaned_df)

# Write cleaned CSV
cleaned_df.to_csv(CLEANED_PATH, index=False, na_rep='')

# Write cleaning summary JSON
summary = {
    'raw_rows': raw_rows,
    'cleaned_rows': cleaned_rows,
    'duplicate_rows_removed': dup_removed,
    'rows_dropped_due_to_date': date_dropped,
    'rows_dropped_due_to_meter_id': meter_dropped,
    'rows_dropped_due_to_building_type': building_dropped,
    'rows_dropped_due_to_tariff': tariff_dropped,
    'rows_dropped_due_to_energy': energy_dropped,
    'rows_with_missing_temperature': int(temp_missing)
}
with open(SUMMARY_PATH, 'w') as f:
    json.dump(summary, f, indent=2)

# ---------------------------------------------------------------------------
# End of script
# ---------------------------------------------------------------------------
