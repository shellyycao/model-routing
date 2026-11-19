import os
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INPUT_DIR = os.environ.get("INPUT_DIR", ".")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", ".")
RAW_FILE = os.path.join(INPUT_DIR, "raw.csv")
CLEANED_FILE = os.path.join(OUTPUT_DIR, "cleaned.csv")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "cleaning_summary.json")

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
MISSING_VALUES = {"", "na", "n/a", "null", "none", "-"}

def is_missing(val):
    return isinstance(val, str) and val.strip().lower() in MISSING_VALUES

def parse_date(val):
    if pd.isna(val):
        return None
    val = val.strip()
    date_formats = [
        "%Y-%m-%d",          # 2024-01-01
        "%m/%d/%Y",          # 01/31/2024
        "%d-%b-%Y",          # 05-Mar-2024
        "%Y/%m/%d",          # 2024/01/02
        "%B %d, %Y",         # January 5, 2024
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def clean_energy(val):
    if pd.isna(val):
        return None
    # remove commas and surrounding whitespace
    val = val.replace(",", "").strip()
    # regex to capture number and optional unit
    m = re.match(r"(?i)^(?P<num>[-+]?\d*\.?\d+)(?:\s*(?P<unit>mwh|kwh))?$", val)
    if not m:
        return None
    num = float(m.group('num'))
    unit = m.group('unit')
    if unit:
        unit = unit.lower()
    if unit == 'mwh':
        num *= 1000  # convert to kWh
    # if unit is kwh or None, keep as is (already kWh)
    if num < 0 or num > 100000:
        return None
    return round(num, 2)

def clean_temperature(val):
    if pd.isna(val):
        return np.nan
    val = val.strip()
    # capture numeric part and optional unit (F, C, °F, °C)
    m = re.match(r"(?i)^(?P<num>[-+]?\d*\.?\d+)(?:\s*°?\s*(?P<unit>[FC]))?$", val)
    if not m:
        return np.nan
    num = float(m.group('num'))
    unit = m.group('unit')
    if unit:
        unit = unit.upper()
    # default to Celsius if unit missing or C, convert if F
    if unit == 'F':
        num = (num - 32) * 5.0 / 9.0
    # now num is Celsius
    if num < -40 or num > 50:
        return np.nan
    return round(num, 1)

# ---------------------------------------------------------------------------
# Load raw data (all columns as text)
# ---------------------------------------------------------------------------
raw_df = pd.read_csv(RAW_FILE, dtype=str, keep_default_na=False, na_values=[])
raw_rows = len(raw_df)

# Strip whitespace from every cell
raw_df = raw_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# Convert defined missing tokens to NaN
raw_df = raw_df.replace(to_replace=lambda v: is_missing(v) if isinstance(v, str) else False, value=np.nan)

# ---------------------------------------------------------------------------
# R2 – Remove duplicate reading_id rows (keep first)
# ---------------------------------------------------------------------------
dup_removed = raw_df.duplicated(subset='reading_id').sum()
clean_df = raw_df.drop_duplicates(subset='reading_id', keep='first')

# ---------------------------------------------------------------------------
# R3 – Parse reading_date
# ---------------------------------------------------------------------------
clean_df['reading_date_parsed'] = clean_df['reading_date'].apply(parse_date)
date_invalid = clean_df['reading_date_parsed'].isna().sum()
clean_df = clean_df.dropna(subset=['reading_date_parsed'])
clean_df = clean_df.rename(columns={'reading_date_parsed': 'reading_date'})

# ---------------------------------------------------------------------------
# R4 – meter_id to upper case, drop missing
# ---------------------------------------------------------------------------
clean_df['meter_id'] = clean_df['meter_id'].str.upper()
meter_missing = clean_df['meter_id'].isna().sum()
clean_df = clean_df.dropna(subset=['meter_id'])

# ---------------------------------------------------------------------------
# R5 – building_type mapping
# ---------------------------------------------------------------------------
building_map = {
    'residential': 'Residential', 'res': 'Residential', 'resi': 'Residential',
    'commercial': 'Commercial', 'comm': 'Commercial',
    'industrial': 'Industrial', 'ind': 'Industrial'
}
clean_df['building_type_mapped'] = clean_df['building_type'].str.lower().map(building_map)
building_invalid = clean_df['building_type_mapped'].isna().sum()
clean_df = clean_df.dropna(subset=['building_type_mapped'])
clean_df = clean_df.rename(columns={'building_type_mapped': 'building_type'})

# ---------------------------------------------------------------------------
# R6 – tariff mapping
# ---------------------------------------------------------------------------
tariff_map = {
    'peak': 'peak',
    'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'
}
clean_df['tariff_mapped'] = clean_df['tariff'].str.lower().map(tariff_map)
 tariff_invalid = clean_df['tariff_mapped'].isna().sum()
clean_df = clean_df.dropna(subset=['tariff_mapped'])
clean_df = clean_df.rename(columns={'tariff_mapped': 'tariff'})

# ---------------------------------------------------------------------------
# R7 – energy conversion to kWh
# ---------------------------------------------------------------------------
clean_df['energy_kwh'] = clean_df['energy'].apply(clean_energy)
energy_invalid = clean_df['energy_kwh'].isna().sum()
clean_df = clean_df.dropna(subset=['energy_kwh'])

# ---------------------------------------------------------------------------
# R8 – temperature conversion (keep row even if invalid)
# ---------------------------------------------------------------------------
clean_df['temperature_c'] = clean_df['temperature'].apply(clean_temperature)
# No rows are dropped for temperature; invalid values become NaN (empty cell)

# ---------------------------------------------------------------------------
# R9 – Final column selection, ordering and sorting
# ---------------------------------------------------------------------------
final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
clean_df = clean_df[final_cols]
clean_df = clean_df.sort_values('reading_id')

# Write cleaned CSV
clean_df.to_csv(CLEANED_FILE, index=False, float_format='%.2f')
cleaned_rows = len(clean_df)

# Write cleaning summary JSON
summary = {
    "raw_rows": raw_rows,
    "cleaned_rows": cleaned_rows,
    "duplicate_rows_removed": int(dup_removed),
    "rows_dropped_due_to_date": int(date_invalid),
    "rows_dropped_due_to_meter_id_missing": int(meter_missing),
    "rows_dropped_due_to_building_type_invalid": int(building_invalid),
    "rows_dropped_due_to_tariff_invalid": int(tariff_invalid),
    "rows_dropped_due_to_energy_invalid": int(energy_invalid)
}
with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

# Variable required by the evaluation harness
output_filename = "cleaned.csv"
