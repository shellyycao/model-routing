import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import re

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_DIR = os.getenv('INPUT_DIR')
OUTPUT_DIR = os.getenv('OUTPUT_DIR')
RAW_FILE = os.path.join(INPUT_DIR, 'raw.csv')
CLEANED_FILE = os.path.join(OUTPUT_DIR, 'cleaned.csv')
SUMMARY_FILE = os.path.join(OUTPUT_DIR, 'cleaning_summary.json')
output_filename = 'cleaned.csv'

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
MISSING_VALUES = {'', 'na', 'n/a', 'null', 'none', '-'}

def clean_cell(v):
    if isinstance(v, str):
        v = v.strip()
        if v.lower() in MISSING_VALUES:
            return np.nan
        return v
    return v

def parse_date(s):
    if pd.isna(s):
        return None
    s = s.strip()
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d-%b-%Y",   # e.g. 05-Mar-2024
        "%Y/%m/%d",
        "%B %d, %Y"   # e.g. March 5, 2024
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def convert_energy(v):
    """Return energy in kWh (float) or np.nan if invalid."""
    if pd.isna(v):
        return np.nan
    s = str(v).replace(',', '').strip()
    # Regex to capture number and optional unit
    m = re.match(r"^([0-9]*\.?[0-9]+)\s*([a-zA-Z]*)$", s, re.IGNORECASE)
    if not m:
        return np.nan
    number = float(m.group(1))
    unit = m.group(2).lower()
    if unit == 'mwh':
        number *= 1000.0
    elif unit == 'kwh' or unit == '':
        pass
    else:
        # unknown unit
        return np.nan
    if number < 0 or number > 100000:
        return np.nan
    return round(number, 2)

def convert_temperature(v):
    """Return temperature in Celsius (float) or np.nan if invalid.
    Rows are *kept* even if temperature becomes missing.
    """
    if pd.isna(v):
        return np.nan
    s = str(v).strip().replace('°', '')
    # Detect unit
    m = re.match(r"^([+-]?[0-9]*\.?[0-9]+)\s*([cCfF]?)$", s)
    if not m:
        return np.nan
    number = float(m.group(1))
    unit = m.group(2).upper()
    if unit == 'F':
        c = (number - 32) * 5.0 / 9.0
    else:  # C or empty -> already Celsius
        c = number
    if c < -40 or c > 50:
        return np.nan
    return round(c, 1)

# ---------------------------------------------------------------------------
# Load raw data (all columns as text)
# ---------------------------------------------------------------------------
df_raw = pd.read_csv(RAW_FILE, dtype=str, keep_default_na=False)
raw_rows = len(df_raw)

# Strip whitespace and normalise missing values
df = df_raw.applymap(clean_cell)

# ---------------------------------------------------------------------------
# R2 – Remove duplicate reading_id (keep first)
# ---------------------------------------------------------------------------
duplicates_removed = raw_rows - df['reading_id'].nunique()
df = df.drop_duplicates(subset='reading_id', keep='first')

# ---------------------------------------------------------------------------
# R3 – reading_date parsing
# ---------------------------------------------------------------------------
df['reading_date_parsed'] = df['reading_date'].apply(parse_date)
invalid_date_mask = df['reading_date_parsed'].isna()
date_invalid = invalid_date_mask.sum()
df = df[~invalid_date_mask]

# ---------------------------------------------------------------------------
# R4 – meter_id upper‑casing
# ---------------------------------------------------------------------------
df['meter_id'] = df['meter_id'].str.upper()
meter_missing = df['meter_id'].isna().sum()
df = df[~df['meter_id'].isna()]

# ---------------------------------------------------------------------------
# R5 – building_type normalisation
# ---------------------------------------------------------------------------
building_map = {
    'residential': 'Residential',
    'res': 'Residential',
    'resi': 'Residential',
    'commercial': 'Commercial',
    'comm': 'Commercial',
    'industrial': 'Industrial',
    'ind': 'Industrial'
}

def map_building(v):
    if pd.isna(v):
        return np.nan
    return building_map.get(v.lower())

df['building_type_norm'] = df['building_type'].apply(map_building)
building_invalid = df['building_type_norm'].isna().sum()
df = df[~df['building_type_norm'].isna()]

# ---------------------------------------------------------------------------
# R6 – tariff normalisation
# ---------------------------------------------------------------------------
 tariff_map = {
    'peak': 'peak',
    'off-peak': 'off-peak',
    'offpeak': 'off-peak',
    'off peak': 'off-peak'
}

def map_tariff(v):
    if pd.isna(v):
        return np.nan
    return tariff_map.get(v.lower())

df['tariff_norm'] = df['tariff'].apply(map_tariff)
 tariff_invalid = df['tariff_norm'].isna().sum()
 df = df[~df['tariff_norm'].isna()]

# ---------------------------------------------------------------------------
# R7 – energy conversion to kWh
# ---------------------------------------------------------------------------
df['energy_kwh'] = df['energy'].apply(convert_energy)
energy_invalid = df['energy_kwh'].isna().sum()
df = df[~df['energy_kwh'].isna()]

# ---------------------------------------------------------------------------
# R8 – temperature conversion (keep row even if missing)
# ---------------------------------------------------------------------------
df['temperature_c'] = df['temperature'].apply(convert_temperature)
temperature_invalid = df['temperature_c'].isna().sum()

# ---------------------------------------------------------------------------
# Final column selection and ordering
# ---------------------------------------------------------------------------
final_df = df[['reading_id', 'reading_date_parsed', 'meter_id', 'building_type_norm',
               'tariff_norm', 'energy_kwh', 'temperature_c']].copy()
final_df.rename(columns={
    'reading_date_parsed': 'reading_date',
    'building_type_norm': 'building_type',
    'tariff_norm': 'tariff'
}, inplace=True)

# Ensure correct dtypes for CSV output (pandas will handle conversion)
final_df['reading_date'] = final_df['reading_date'].astype(str)
final_df['building_type'] = final_df['building_type'].astype(str)
final_df['tariff'] = final_df['tariff'].astype(str)

# Sort by reading_id ascending (string sort)
final_df.sort_values('reading_id', inplace=True)

# Write cleaned CSV
final_df.to_csv(CLEANED_FILE, index=False, float_format='%.2f')
cleaned_rows = len(final_df)

# ---------------------------------------------------------------------------
# Write cleaning summary JSON
# ---------------------------------------------------------------------------
summary = {
    "raw_rows": raw_rows,
    "cleaned_rows": cleaned_rows,
    "duplicates_removed": duplicates_removed,
    "date_invalid": int(date_invalid),
    "meter_missing": int(meter_missing),
    "building_invalid": int(building_invalid),
    "tariff_invalid": int(tariff_invalid),
    "energy_invalid": int(energy_invalid),
    "temperature_invalid": int(temperature_invalid)
}
with open(SUMMARY_FILE, 'w') as f:
    json.dump(summary, f, indent=2)

# The script finishes without printing anything.
