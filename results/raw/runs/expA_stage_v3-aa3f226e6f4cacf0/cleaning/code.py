import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def strip_and_normalize(df):
    """Strip whitespace from all string values and convert custom missing markers to NaN."""
    missing_markers = {'', 'na', 'n/a', 'null', 'none', '-'}
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].apply(lambda x: np.nan if x.lower() in missing_markers else x)
    return df

def parse_date(val):
    if pd.isna(val):
        return None
    val = val.strip()
    date_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d-%b-%Y",   # e.g. 05-Mar-2024
        "%Y/%m/%d",
        "%B %d, %Y",  # e.g. March 5, 2024
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def clean_energy(val):
    if pd.isna(val):
        return None
    # remove commas and surrounding whitespace
    val = val.replace(',', '').strip()
    # regex to capture number and optional unit
    m = re.match(r"(?i)^(?P<num>[-+]?[0-9]*\.?[0-9]+)\s*(?P<unit>mwh|kwh)?$", val)
    if not m:
        return None
    num = float(m.group('num'))
    unit = m.group('unit')
    if unit:
        unit = unit.lower()
    if unit == 'mwh':
        num *= 1000  # convert to kWh
    # if unit is kwh or None, keep as is
    if num < 0 or num > 100000:
        return None
    return round(num, 2)

def clean_temperature(val):
    if pd.isna(val):
        return np.nan
    val = val.strip()
    # capture numeric part and optional unit (C or F) possibly preceded by degree sign
    m = re.match(r"(?i)^(?P<num>[-+]?[0-9]*\.?[0-9]+)\s*(°?\s*(?P<unit>[cf]))?$", val)
    if not m:
        return np.nan
    num = float(m.group('num'))
    unit = m.group('unit')
    if unit:
        unit = unit.lower()
    if unit == 'f':
        # Convert Fahrenheit to Celsius
        num = (num - 32) * 5.0 / 9.0
    # if unit is 'c' or None, value is already Celsius
    if num < -40 or num > 50:
        return np.nan
    return round(num, 1)

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.getenv('INPUT_DIR')
    output_dir = os.getenv('OUTPUT_DIR')
    raw_path = os.path.join(input_dir, 'raw.csv')
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')

    # 1. Read raw CSV as text (all columns as strings)
    df_raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df_raw)

    # 2. R1 – strip whitespace and normalise missing values
    df = strip_and_normalize(df_raw.copy())

    # 3. R2 – drop duplicate reading_id, keep first
    before_dup = len(df)
    df = df.drop_duplicates(subset='reading_id', keep='first')
    dup_removed = before_dup - len(df)

    # 4. R3 – parse reading_date
    df['reading_date_parsed'] = df['reading_date'].apply(parse_date)
    before_date = len(df)
    df = df.dropna(subset=['reading_date_parsed'])
    date_dropped = before_date - len(df)
    df = df.drop(columns=['reading_date'])
    df = df.rename(columns={'reading_date_parsed': 'reading_date'})

    # 5. R4 – meter_id upper case, drop missing
    before_meter = len(df)
    df['meter_id'] = df['meter_id'].apply(lambda x: x.upper() if pd.notna(x) else np.nan)
    df = df.dropna(subset=['meter_id'])
    meter_dropped = before_meter - len(df)

    # 6. R5 – building_type mapping
    building_map = {
        'residential': 'Residential', 'res': 'Residential', 'resi': 'Residential',
        'commercial': 'Commercial', 'comm': 'Commercial',
        'industrial': 'Industrial', 'ind': 'Industrial'
    }
    def map_building(val):
        if pd.isna(val):
            return np.nan
        return building_map.get(val.lower())
    before_bt = len(df)
    df['building_type'] = df['building_type'].apply(map_building)
    df = df.dropna(subset=['building_type'])
    bt_dropped = before_bt - len(df)

    # 7. R6 – tariff mapping
    tariff_map = {
        'peak': 'peak',
        'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'
    }
    def map_tariff(val):
        if pd.isna(val):
            return np.nan
        return tariff_map.get(val.lower())
    before_tariff = len(df)
    df['tariff'] = df['tariff'].apply(map_tariff)
    df = df.dropna(subset=['tariff'])
    tariff_dropped = before_tariff - len(df)

    # 8. R7 – energy conversion to kWh
    before_energy = len(df)
    df['energy_kwh'] = df['energy'].apply(clean_energy)
    df = df.dropna(subset=['energy_kwh'])
    energy_dropped = before_energy - len(df)

    # 9. R8 – temperature conversion (keep row even if result is NaN)
    df['temperature_c'] = df['temperature'].apply(clean_temperature)
    # Count rows where temperature became missing (including original missing)
    temp_missing_count = df['temperature_c'].isna().sum()

    # 10. R9 – final column selection, ordering and sorting
    final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type',
                  'tariff', 'energy_kwh', 'temperature_c']
    df = df[final_cols]
    df = df.sort_values(by='reading_id')

    # Cast categorical columns
    df['building_type'] = pd.Categorical(df['building_type'], categories=['Residential', 'Commercial', 'Industrial'])
    df['tariff'] = pd.Categorical(df['tariff'], categories=['peak', 'off-peak'])

    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False, float_format='%.2f')
    cleaned_rows = len(df)

    # Build cleaning summary
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows,
        "duplicate_rows_removed": int(dup_removed),
        "rows_dropped_due_to_date": int(date_dropped),
        "rows_dropped_due_to_meter_id": int(meter_dropped),
        "rows_dropped_due_to_building_type": int(bt_dropped),
        "rows_dropped_due_to_tariff": int(tariff_dropped),
        "rows_dropped_due_to_energy": int(energy_dropped),
        "rows_with_invalid_temperature": int(temp_missing_count)
    }
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
