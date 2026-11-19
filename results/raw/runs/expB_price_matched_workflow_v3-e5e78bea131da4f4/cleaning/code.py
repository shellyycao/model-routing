import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def parse_reading_date(val):
    """Parse date strings according to specified formats."""
    if not val:
        return None
    val = val.strip()
    # Try YYYY-MM-DD
    try:
        return datetime.strptime(val, '%Y-%m-%d')
    except ValueError:
        pass
    # Try MM/DD/YYYY
    try:
        return datetime.strptime(val, '%m/%d/%Y')
    except ValueError:
        pass
    # Try DD-Mon-YYYY
    try:
        return datetime.strptime(val, '%d-%b-%Y')
    except ValueError:
        pass
    # Try YYYY/MM/DD
    try:
        return datetime.strptime(val, '%Y/%m/%d')
    except ValueError:
        pass
    # Try 'Month D, YYYY' (full month name)
    try:
        return datetime.strptime(val, '%B %d, %Y')
    except ValueError:
        pass
    return None

def parse_energy(val):
    """Parse energy values, handling units and scaling."""
    if not val:
        return None
    val = val.strip()
    # Remove commas
    val = val.replace(',', '')
    
    multiplier = 1
    # Check for MWh (case-insensitive, optional space)
    mwh_match = re.match(r'^(.+?)\s*mwh$', val, re.IGNORECASE)
    if mwh_match:
        val = mwh_match.group(1).strip()
        multiplier = 1000
    else:
        # Check for kWh (case-insensitive)
        kwh_match = re.match(r'^(.+?)\s*kwh$', val, re.IGNORECASE)
        if kwh_match:
            val = kwh_match.group(1).strip()
    
    try:
        num = float(val)
        return round(num * multiplier, 2)
    except ValueError:
        return None

def parse_temperature(val):
    """Parse temperature values, handling units and conversion."""
    if not val:
        return None
    val = val.strip()
    
    # Remove degree sign if present
    val = val.replace('°', '')
    
    # Check for Fahrenheit
    f_match = re.match(r'^(.+?)\s*f$', val, re.IGNORECASE)
    if f_match:
        try:
            f_val = float(f_match.group(1).strip())
            c_val = (f_val - 32) * 5 / 9
            return round(c_val, 1)
        except ValueError:
            return None
    
    # Check for Celsius or no unit
    c_match = re.match(r'^(.+?)\s*c$', val, re.IGNORECASE)
    if c_match:
        val = c_match.group(1).strip()
    
    try:
        return round(float(val), 1)
    except ValueError:
        return None

def main():
    input_dir = os.environ['INPUT_DIR']
    output_dir = os.environ['OUTPUT_DIR']
    
    # R1: Read all columns as text
    df = pd.read_csv(os.path.join(input_dir, 'raw.csv'), dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # R1: Strip whitespace and standardize missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    for col in df.columns:
        df[col] = df[col].str.strip()
        df[col] = df[col].apply(lambda x: '' if x in missing_vals else x)
    
    # R2: Remove duplicates based on reading_id, keep first
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['reading_id'], keep='first')
    duplicates_removed = before_dedup - len(df)
    
    # R3: Parse reading_date
    df['reading_date_parsed'] = df['reading_date'].apply(parse_reading_date)
    before_date = len(df)
    df = df[df['reading_date_parsed'].notna()].copy()
    dates_dropped = before_date - len(df)
    df['reading_date'] = df['reading_date_parsed'].dt.strftime('%Y-%m-%d')
    df.drop(columns=['reading_date_parsed'], inplace=True)
    
    # R4: meter_id - uppercase, drop missing
    df['meter_id'] = df['meter_id'].str.upper()
    before_meter = len(df)
    df = df[df['meter_id'] != ''].copy()
    meters_dropped = before_meter - len(df)
    
    # R5: building_type mapping
    btype_map = {
        'residential': 'Residential', 'res': 'Residential', 'resi': 'Residential',
        'commercial': 'Commercial', 'comm': 'Commercial',
        'industrial': 'Industrial', 'ind': 'Industrial'
    }
    df['building_type'] = df['building_type'].str.lower().map(btype_map)
    before_btype = len(df)
    df = df[df['building_type'].notna()].copy()
    btypes_dropped = before_btype - len(df)
    
    # R6: tariff mapping
    tariff_map = {
        'peak': 'peak',
        'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'
    }
    df['tariff'] = df['tariff'].str.lower().map(tariff_map)
    before_tariff = len(df)
    df = df[df['tariff'].notna()].copy()
    tariffs_dropped = before_tariff - len(df)
    
    # R7: energy -> energy_kwh
    df['energy_kwh'] = df['energy'].apply(parse_energy)
    before_energy = len(df)
    df = df[df['energy_kwh'].notna()].copy()
    df = df[(df['energy_kwh'] >= 0) & (df['energy_kwh'] <= 100000)].copy()
    energy_dropped = before_energy - len(df)
    df.drop(columns=['energy'], inplace=True)
    
    # R8: temperature -> temperature_c
    df['temperature_c'] = df['temperature'].apply(parse_temperature)
    # Set out-of-range to NaN (keep row)
    df.loc[df['temperature_c'] < -40, 'temperature_c'] = np.nan
    df.loc[df['temperature_c'] > 50, 'temperature_c'] = np.nan
    df.drop(columns=['temperature'], inplace=True)
    
    # R9: Select columns and sort
    final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
    df = df[final_cols].sort_values('reading_id').reset_index(drop=True)
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    output_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(output_path, index=False)
    
    # Write cleaning summary
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed': duplicates_removed,
        'dates_dropped': dates_dropped,
        'meters_dropped': meters_dropped,
        'building_types_dropped': btypes_dropped,
        'tariffs_dropped': tariffs_dropped,
        'energy_values_dropped': energy_dropped
    }
    with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
