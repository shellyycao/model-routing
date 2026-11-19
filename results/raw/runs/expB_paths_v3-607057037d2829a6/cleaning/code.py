import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def strip_and_mark_missing(val):
    """Strip whitespace and convert defined missing tokens to NaN.
    Missing tokens (case‑insensitive): "", "NA", "N/A", "null", "None", "-".
    """
    if not isinstance(val, str):
        return np.nan
    v = val.strip()
    if v.lower() in {"", "na", "n/a", "null", "none", "-"}:
        return np.nan
    return v

def parse_date(date_str):
    """Try the allowed date formats, return a string YYYY‑MM‑DD or NaT."""
    if pd.isna(date_str):
        return pd.NaT
    date_str = date_str.strip()
    formats = [
        "%Y-%m-%d",          # 2024-01-01
        "%m/%d/%Y",          # 01/02/2024
        "%d-%b-%Y",          # 05-Mar-2024 (abbr month)
        "%Y/%m/%d",          # 2024/01/02
        "%B %d, %Y",         # January 5, 2024 (full month name)
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return pd.NaT

def clean_energy(val):
    """Convert energy column to kWh (float). Return (value, valid_flag)."""
    if pd.isna(val):
        return (np.nan, False)
    # remove commas and surrounding spaces
    s = val.replace(",", "").strip()
    # regex to capture number and optional unit (kwh/mwh) – case‑insensitive, optional space
    m = re.match(r"^([0-9]*\.?[0-9]+)\s*([kKmM][wW][hH])?$", s)
    if not m:
        # maybe unit attached without space, e.g. 498.85kwh or 1.2MWh
        m = re.match(r"^([0-9]*\.?[0-9]+)\s*([kKmM][wW][hH])$", s)
    if not m:
        return (np.nan, False)
    number = float(m.group(1))
    unit = m.group(2)
    if unit is None:
        # no unit – already kWh
        kwh = number
    else:
        unit = unit.lower()
        if unit == "mwh":
            kwh = number * 1000.0
        else:  # kwh
            kwh = number
    if kwh < 0 or kwh > 100000:
        return (np.nan, False)
    return (round(kwh, 2), True)

def clean_temperature(val):
    """Convert temperature to Celsius (float). Return (value, valid_flag).
    If conversion fails or out of allowed range, return (np.nan, False) – the row is kept.
    """
    if pd.isna(val):
        return (np.nan, False)
    s = val.strip()
    # remove degree sign if present
    s = s.replace('°', '')
    # regex to capture number and optional unit (F or C)
    m = re.match(r"^([+-]?[0-9]*\.?[0-9]+)\s*([fFcC])?$", s)
    if not m:
        return (np.nan, False)
    number = float(m.group(1))
    unit = m.group(2)
    if unit is None or unit.upper() == 'C':
        c = number
    else:  # Fahrenheit
        c = (number - 32) * 5.0 / 9.0
    if c < -40 or c > 50:
        return (np.nan, False)
    return (round(c, 1), True)

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.getenv('INPUT_DIR')
    output_dir = os.getenv('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('Both INPUT_DIR and OUTPUT_DIR environment variables must be set')

    raw_path = os.path.join(input_dir, 'raw.csv')
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)

    # R1 – strip whitespace and mark missing values
    df = df.applymap(strip_and_mark_missing)

    # R2 – drop duplicate reading_id (keep first)
    dup_before = len(df)
    df = df.drop_duplicates(subset='reading_id', keep='first')
    duplicates_removed = dup_before - len(df)

    # Prepare counters for summary
    counters = {
        'date_invalid': 0,
        'meter_missing': 0,
        'building_invalid': 0,
        'tariff_invalid': 0,
        'energy_invalid': 0,
        'temperature_invalid': 0,
    }

    # R3 – reading_date parsing
    df['reading_date_parsed'] = df['reading_date'].apply(parse_date)
    mask_date_ok = df['reading_date_parsed'].notna()
    counters['date_invalid'] = (~mask_date_ok).sum()
    df = df[mask_date_ok].copy()
    df['reading_date'] = df['reading_date_parsed']
    df.drop(columns=['reading_date_parsed'], inplace=True)

    # R4 – meter_id upper case, drop missing
    df['meter_id'] = df['meter_id'].apply(lambda x: x.upper() if pd.notna(x) else x)
    mask_meter_ok = df['meter_id'].notna()
    counters['meter_missing'] = (~mask_meter_ok).sum()
    df = df[mask_meter_ok].copy()

    # R5 – building_type mapping
    building_map = {
        'residential': 'Residential', 'res': 'Residential', 'resi': 'Residential',
        'commercial': 'Commercial', 'comm': 'Commercial',
        'industrial': 'Industrial', 'ind': 'Industrial'
    }
    def map_building(val):
        if pd.isna(val):
            return np.nan
        return building_map.get(val.strip().lower())
    df['building_type_mapped'] = df['building_type'].apply(map_building)
    mask_build_ok = df['building_type_mapped'].notna()
    counters['building_invalid'] = (~mask_build_ok).sum()
    df = df[mask_build_ok].copy()
    df['building_type'] = df['building_type_mapped']
    df.drop(columns=['building_type_mapped'], inplace=True)

    # R6 – tariff mapping
    tariff_map = {
        'peak': 'peak',
        'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'
    }
    def map_tariff(val):
        if pd.isna(val):
            return np.nan
        return tariff_map.get(val.strip().lower())
    df['tariff_mapped'] = df['tariff'].apply(map_tariff)
    mask_tariff_ok = df['tariff_mapped'].notna()
    counters['tariff_invalid'] = (~mask_tariff_ok).sum()
    df = df[mask_tariff_ok].copy()
    df['tariff'] = df['tariff_mapped']
    df.drop(columns=['tariff_mapped'], inplace=True)

    # R7 – energy conversion to kWh
    energy_vals = []
    energy_valid_flags = []
    for v in df['energy']:
        val, ok = clean_energy(v)
        energy_vals.append(val)
        energy_valid_flags.append(ok)
    df['energy_kwh'] = energy_vals
    mask_energy_ok = pd.Series(energy_valid_flags)
    counters['energy_invalid'] = (~mask_energy_ok).sum()
    df = df[mask_energy_ok].copy()

    # R8 – temperature conversion to Celsius (keep row even if invalid)
    temp_vals = []
    temp_valid_flags = []
    for v in df['temperature']:
        val, ok = clean_temperature(v)
        temp_vals.append(val)
        temp_valid_flags.append(ok)
    df['temperature_c'] = temp_vals
    counters['temperature_invalid'] = sum(1 for ok in temp_valid_flags if not ok)
    # No row removal for temperature

    # R9 – final column selection, ordering and sorting
    final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
    df = df[final_cols]
    df = df.sort_values(by='reading_id')

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(cleaned_path, index=False, float_format='%.2f')

    # Prepare cleaning summary
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': len(df),
        'duplicates_removed': duplicates_removed,
        'date_invalid': int(counters['date_invalid']),
        'meter_missing': int(counters['meter_missing']),
        'building_invalid': int(counters['building_invalid']),
        'tariff_invalid': int(counters['tariff_invalid']),
        'energy_invalid': int(counters['energy_invalid']),
        'temperature_invalid': int(counters['temperature_invalid'])
    }
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # Output filename variable for the orchestrator
    print(json.dumps({"output_filename": "cleaned.csv"}))

if __name__ == '__main__':
    main()
