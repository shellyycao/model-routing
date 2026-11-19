import os
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def is_missing(val):
    """Return True if the string value should be considered missing.
    Missing values are: empty string, 'NA', 'N/A', 'null', 'None', '-'
    (case‑insensitive, after stripping)."""
    if pd.isna(val):
        return True
    if isinstance(val, str):
        v = val.strip().lower()
        return v in {"", "na", "n/a", "null", "none", "-"}
    return False

def parse_date(val):
    """Parse a date string using the allowed formats.
    Returns a string in YYYY‑MM‑DD format or None if parsing fails.
    """
    if is_missing(val):
        return None
    s = val.strip()
    formats = [
        "%Y-%m-%d",          # 2024-01-01
        "%m/%d/%Y",          # 01/31/2024
        "%d-%b-%Y",          # 05-Mar-2024 (abbr month)
        "%Y/%m/%d",          # 2024/01/02
        "%B %d, %Y",         # January 5, 2024 (full month name)
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def clean_energy(val):
    """Convert the raw energy field to a float in kWh.
    Handles commas, optional unit (MWh or kWh) and validates range.
    Returns (value, ok) where ok is False if the row must be dropped.
    """
    if is_missing(val):
        return (None, False)
    s = str(val).replace(",", "").strip()
    # Regex to capture number and optional unit
    m = re.match(r"(?i)^(?P<num>[-+]?\d*\.?\d+)(?:\s*(?P<unit>mwh|kwh))?$", s)
    if not m:
        return (None, False)
    num = float(m.group('num'))
    unit = m.group('unit')
    if unit:
        unit = unit.lower()
    if unit == 'mwh':
        num *= 1000.0
    # if unit is kwh or None, keep as is (already kWh)
    if num < 0 or num > 100000:
        return (None, False)
    return (round(num, 2), True)

def clean_temperature(val):
    """Convert temperature to Celsius, round to 1 decimal.
    Returns (value, is_valid) where is_valid indicates the value is within
    the allowed range. If not valid, value is set to np.nan but the row is kept.
    """
    if is_missing(val):
        return (np.nan, False)
    s = str(val).strip()
    # Remove trailing degree sign if present
    s = s.replace('°', '')
    # Regex to capture number and optional unit (F or C)
    m = re.match(r"(?i)^(?P<num>[-+]?\d*\.?\d+)(?P<unit>[fc])?$", s)
    if not m:
        return (np.nan, False)
    num = float(m.group('num'))
    unit = m.group('unit')
    if unit:
        unit = unit.lower()
    if unit == 'f':
        # Convert Fahrenheit to Celsius
        num = (num - 32) * 5.0 / 9.0
    # else C or missing -> already Celsius
    if num < -40 or num > 50:
        return (np.nan, False)
    return (round(num, 1), True)

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.getenv('INPUT_DIR')
    output_dir = os.getenv('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('Both INPUT_DIR and OUTPUT_DIR environment variables must be set')

    raw_path = os.path.join(input_dir, 'raw.csv')
    df_raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df_raw)

    # R1 – strip whitespace and normalise missing values
    df = df_raw.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.replace({np.nan: None})  # ensure NaN is None for our helper
    # Convert defined missing tokens to NaN
    for col in df.columns:
        df[col] = df[col].apply(lambda x: None if is_missing(x) else x)

    # R2 – deduplicate on reading_id (keep first)
    before_dup = len(df)
    df = df.drop_duplicates(subset='reading_id', keep='first')
    dup_removed = before_dup - len(df)

    # Counters for summary
    summary = {
        'raw_rows': raw_rows,
        'duplicates_removed': dup_removed,
        'rows_dropped_date': 0,
        'rows_dropped_meter_id': 0,
        'rows_dropped_building_type': 0,
        'rows_dropped_tariff': 0,
        'rows_dropped_energy': 0,
        'rows_temperature_invalid': 0,
    }

    # R3 – reading_date parsing
    df['reading_date_parsed'] = df['reading_date'].apply(parse_date)
    mask_date = df['reading_date_parsed'].notna()
    summary['rows_dropped_date'] = (~mask_date).sum()
    df = df[mask_date].copy()
    df['reading_date'] = df['reading_date_parsed']
    df.drop(columns=['reading_date_parsed'], inplace=True)

    # R4 – meter_id upper case, drop missing
    df['meter_id'] = df['meter_id'].apply(lambda x: x.upper() if isinstance(x, str) else None)
    mask_meter = df['meter_id'].notna()
    summary['rows_dropped_meter_id'] = (~mask_meter).sum()
    df = df[mask_meter]

    # R5 – building_type mapping
    bt_map = {
        'residential': 'Residential', 'res': 'Residential', 'resi': 'Residential',
        'commercial': 'Commercial', 'comm': 'Commercial',
        'industrial': 'Industrial', 'ind': 'Industrial'
    }
    def map_bt(val):
        if val is None:
            return None
        return bt_map.get(val.strip().lower())
    df['building_type'] = df['building_type'].apply(map_bt)
    mask_bt = df['building_type'].notna()
    summary['rows_dropped_building_type'] = (~mask_bt).sum()
    df = df[mask_bt]

    # R6 – tariff mapping
    tariff_map = {
        'peak': 'peak',
        'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'
    }
    def map_tariff(val):
        if val is None:
            return None
        return tariff_map.get(val.strip().lower())
    df['tariff'] = df['tariff'].apply(map_tariff)
    mask_tariff = df['tariff'].notna()
    summary['rows_dropped_tariff'] = (~mask_tariff).sum()
    df = df[mask_tariff]

    # R7 – energy conversion
    energy_clean = df['energy'].apply(clean_energy)
    df['energy_kwh'] = energy_clean.apply(lambda x: x[0])
    energy_ok = energy_clean.apply(lambda x: x[1])
    summary['rows_dropped_energy'] = (~energy_ok).sum()
    df = df[energy_ok]

    # R8 – temperature conversion (keep row, possibly set missing)
    temp_clean = df['temperature'].apply(clean_temperature)
    df['temperature_c'] = temp_clean.apply(lambda x: x[0])
    temp_valid = temp_clean.apply(lambda x: x[1])
    summary['rows_temperature_invalid'] = (~temp_valid).sum()
    # rows with invalid temperature already have NaN in temperature_c; keep them.

    # R9 – final column selection and ordering
    final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type',
                  'tariff', 'energy_kwh', 'temperature_c']
    df = df[final_cols]
    # Ensure correct dtypes (pandas will infer, but we enforce categories)
    df['building_type'] = pd.Categorical(df['building_type'], categories=['Residential', 'Commercial', 'Industrial'])
    df['tariff'] = pd.Categorical(df['tariff'], categories=['peak', 'off-peak'])
    df['energy_kwh'] = df['energy_kwh'].astype(float)
    # temperature_c may contain NaN already; keep as float
    df['temperature_c'] = df['temperature_c'].astype(float)

    # Sort by reading_id ascending (lexicographic)
    df.sort_values(by='reading_id', inplace=True)

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(cleaned_path, index=False, float_format='%.2f')

    # Prepare summary JSON
    summary['cleaned_rows'] = len(df)
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
