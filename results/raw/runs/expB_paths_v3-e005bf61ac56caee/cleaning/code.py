import os
import json
import re
import pandas as pd
import numpy as np
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_DIR = os.getenv('INPUT_DIR', '.')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '.')
RAW_FILE = os.path.join(INPUT_DIR, 'raw.csv')
CLEANED_FILE = os.path.join(OUTPUT_DIR, 'cleaned.csv')
SUMMARY_FILE = os.path.join(OUTPUT_DIR, 'cleaning_summary.json')
output_filename = 'cleaned.csv'

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
MISSING_VALUES = {'', 'na', 'n/a', 'null', 'none', '-'}

def clean_missing(val):
    if isinstance(val, str):
        v = val.strip()
        if v.lower() in MISSING_VALUES:
            return np.nan
        return v
    return val

def parse_date(val):
    if pd.isna(val):
        return None
    val = val.strip()
    date_formats = [
        "%Y-%m-%d",          # 2024-01-01
        "%m/%d/%Y",          # 01/02/2024
        "%d-%b-%Y",          # 05-Mar-2024 (abbr month, case‑insensitive)
        "%Y/%m/%d",          # 2024/01/02
        "%B %d, %Y"          # January 2, 2024
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            continue
    return None

def convert_energy(val):
    if pd.isna(val):
        return None
    # remove commas and surrounding whitespace
    s = str(val).replace(',', '').strip()
    # regex to capture number and optional unit (kwh/mwh) – case‑insensitive, optional space
    m = re.fullmatch(r"(?i)([0-9]*\.?[0-9]+)\s*(mwh|kwh)?", s)
    if not m:
        return None
    number = float(m.group(1))
    unit = m.group(2)
    if unit:
        unit = unit.lower()
    if unit == 'mwh':
        number *= 1000  # convert to kWh
    # kwh or no unit stays as is
    if number < 0 or number > 100000:
        return None
    return round(number, 2)

def convert_temperature(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    # capture numeric part and optional unit (C/F) – allow degree sign
    m = re.fullmatch(r"(?i)(-?[0-9]*\.?[0-9]+)\s*°?\s*([cf])?", s)
    if not m:
        return np.nan
    number = float(m.group(1))
    unit = m.group(2)
    if unit:
        unit = unit.lower()
    if unit == 'f':
        # Fahrenheit to Celsius
        number = (number - 32) * 5.0 / 9.0
    # if unit is C or missing, value is already Celsius
    number = round(number, 1)
    if number < -40 or number > 50:
        return np.nan
    return number

# ---------------------------------------------------------------------------
# Load raw data (all columns as text)
# ---------------------------------------------------------------------------
raw_df = pd.read_csv(RAW_FILE, dtype=str, keep_default_na=False)
raw_rows = len(raw_df)

# ---------------------------------------------------------------------------
# R1 – strip whitespace and normalise missing values
# ---------------------------------------------------------------------------
clean_df = raw_df.applymap(clean_missing)

# ---------------------------------------------------------------------------
# R2 – drop duplicate reading_id (keep first)
# ---------------------------------------------------------------------------
duplicates_removed = clean_df['reading_id'].duplicated().sum()
clean_df = clean_df[~clean_df['reading_id'].duplicated(keep='first')]

# ---------------------------------------------------------------------------
# R3 – parse reading_date
# ---------------------------------------------------------------------------
clean_df['reading_date'] = clean_df['reading_date'].apply(parse_date)
rows_dropped_date = clean_df['reading_date'].isna().sum()
clean_df = clean_df.dropna(subset=['reading_date'])

# ---------------------------------------------------------------------------
# R4 – normalise meter_id
# ---------------------------------------------------------------------------
clean_df['meter_id'] = clean_df['meter_id'].apply(lambda x: x.upper() if pd.notna(x) else x)
rows_dropped_meter = clean_df['meter_id'].isna().sum()
clean_df = clean_df.dropna(subset=['meter_id'])

# ---------------------------------------------------------------------------
# R5 – normalise building_type
# ---------------------------------------------------------------------------
building_map = {
    'residential': 'Residential', 'res': 'Residential', 'resi': 'Residential',
    'commercial': 'Commercial', 'comm': 'Commercial',
    'industrial': 'Industrial', 'ind': 'Industrial'
}

def map_building(val):
    if pd.isna(val):
        return None
    key = val.strip().lower()
    return building_map.get(key)

clean_df['building_type'] = clean_df['building_type'].apply(map_building)
rows_dropped_building = clean_df['building_type'].isna().sum()
clean_df = clean_df.dropna(subset=['building_type'])

# ---------------------------------------------------------------------------
# R6 – normalise tariff
# ---------------------------------------------------------------------------
 tariff_map = {
    'peak': 'peak',
    'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'
}

def map_tariff(val):
    if pd.isna(val):
        return None
    key = val.strip().lower()
    return tariff_map.get(key)

clean_df['tariff'] = clean_df['tariff'].apply(map_tariff)
rows_dropped_tariff = clean_df['tariff'].isna().sum()
clean_df = clean_df.dropna(subset=['tariff'])

# ---------------------------------------------------------------------------
# R7 – convert energy to kWh
# ---------------------------------------------------------------------------
clean_df['energy_kwh'] = clean_df['energy'].apply(convert_energy)
rows_dropped_energy = clean_df['energy_kwh'].isna().sum()
clean_df = clean_df.dropna(subset=['energy_kwh'])

# ---------------------------------------------------------------------------
# R8 – convert temperature to Celsius (keep row, set missing if out of range)
# ---------------------------------------------------------------------------
clean_df['temperature_c'] = clean_df['temperature'].apply(convert_temperature)
# No rows are dropped for temperature issues.

# ---------------------------------------------------------------------------
# R9 – final column selection, ordering and sorting
# ---------------------------------------------------------------------------
final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
clean_df = clean_df[final_cols]
clean_df = clean_df.sort_values('reading_id')

# Ensure correct dtypes (categories are kept as strings in CSV)
clean_df['energy_kwh'] = clean_df['energy_kwh'].astype(float)
clean_df['temperature_c'] = clean_df['temperature_c'].astype(float)

# Write cleaned CSV
clean_df.to_csv(CLEANED_FILE, index=False, float_format='%.2f')
cleaned_rows = len(clean_df)

# Write cleaning summary
summary = {
    "raw_rows": raw_rows,
    "cleaned_rows": cleaned_rows,
    "duplicates_removed": int(duplicates_removed),
    "rows_dropped_due_to_date": int(rows_dropped_date),
    "rows_dropped_due_to_meter": int(rows_dropped_meter),
    "rows_dropped_due_to_building_type": int(rows_dropped_building),
    "rows_dropped_due_to_tariff": int(rows_dropped_tariff),
    "rows_dropped_due_to_energy": int(rows_dropped_energy)
}
with open(SUMMARY_FILE, 'w') as f:
    json.dump(summary, f, indent=2)

# ---------------------------------------------------------------------------
# End of script
# ---------------------------------------------------------------------------
