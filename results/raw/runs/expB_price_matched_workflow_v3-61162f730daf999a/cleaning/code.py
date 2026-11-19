import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def parse_date(date_str):
    """Parse date string into YYYY-MM-DD format or return None."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    
    formats = [
        '%Y-%m-%d',       # YYYY-MM-DD
        '%m/%d/%Y',       # MM/DD/YYYY
        '%d-%b-%Y',       # DD-Mon-YYYY
        '%Y/%m/%d',       # YYYY/MM/DD
        '%B %d, %Y'       # Month D, YYYY
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def clean_energy(val):
    """Convert energy value to kWh float."""
    if not val:
        return None
    val = str(val).replace(',', '').strip()
    
    # Check for MWh (case-insensitive, optional space)
    mwh_match = re.match(r'^([\d.]+)\s*mwh$', val, re.IGNORECASE)
    if mwh_match:
        try:
            return float(mwh_match.group(1)) * 1000
        except ValueError:
            return None
    
    # Check for kWh (case-insensitive)
    kwh_match = re.match(r'^([\d.]+)\s*kwh$', val, re.IGNORECASE)
    if kwh_match:
        try:
            return float(kwh_match.group(1))
        except ValueError:
            return None
    
    # No unit - assume kWh
    try:
        return float(val)
    except ValueError:
        return None

def clean_temperature(val):
    """Convert temperature to Celsius float."""
    if not val:
        return np.nan
    val = str(val).strip()
    
    # Remove degree sign and any spaces around it
    val = re.sub(r'\s*°\s*', '', val)
    
    # Check for Fahrenheit
    f_match = re.match(r'^([\d.-]+)\s*F$', val, re.IGNORECASE)
    if f_match:
        try:
            f_val = float(f_match.group(1))
            c_val = (f_val - 32) * 5 / 9
            return round(c_val, 1)
        except ValueError:
            return np.nan
    
    # Check for Celsius or no unit
    c_match = re.match(r'^([\d.-]+)\s*C?$', val, re.IGNORECASE)
    if c_match:
        try:
            return round(float(c_match.group(1)), 1)
        except ValueError:
            return np.nan
    
    return np.nan

def main():
    input_dir = os.environ['INPUT_DIR']
    output_dir = os.environ['OUTPUT_DIR']
    
    # R1: Read all columns as text and strip whitespace
    df = pd.read_csv(
        os.path.join(input_dir, 'raw.csv'),
        dtype=str,
        keep_default_na=False
    )
    
    raw_rows = len(df)
    
    # Strip whitespace from all values
    for col in df.columns:
        df[col] = df[col].str.strip()
    
    # R1: Treat specific values as missing
    missing_values = ['', 'NA', 'N/A', 'null', 'None', '-']
    for col in df.columns:
        df[col] = df[col].apply(lambda x: '' if x in missing_values else x)
    
    # R2: Remove duplicates based on reading_id (keep first)
    rows_before_r2 = len(df)
    df = df.drop_duplicates(subset='reading_id', keep='first')
    duplicates_removed = rows_before_r2 - len(df)
    
    # R3: Parse reading_date
    df['reading_date'] = df['reading_date'].apply(parse_date)
    rows_before_r3 = len(df)
    df = df[df['reading_date'].notna() & (df['reading_date'] != '')]
    rows_dropped_r3 = rows_before_r3 - len(df)
    
    # R4: meter_id - uppercase and drop missing
    df['meter_id'] = df['meter_id'].str.upper()
    rows_before_r4 = len(df)
    df = df[df['meter_id'] != '']
    rows_dropped_r4 = rows_before_r4 - len(df)
    
    # R5: building_type mapping
    building_map = {
        'residential': 'Residential',
        'res': 'Residential',
        'resi': 'Residential',
        'commercial': 'Commercial',
        'comm': 'Commercial',
        'industrial': 'Industrial',
        'ind': 'Industrial'
    }
    df['building_type'] = df['building_type'].str.lower().map(building_map)
    rows_before_r5 = len(df)
    df = df[df['building_type'].notna()]
    rows_dropped_r5 = rows_before_r5 - len(df)
    
    # R6: tariff mapping
    tariff_map = {
        'peak': 'peak',
        'off-peak': 'off-peak',
        'offpeak': 'off-peak',
        'off peak': 'off-peak'
    }
    df['tariff'] = df['tariff'].str.lower().map(tariff_map)
    rows_before_r6 = len(df)
    df = df[df['tariff'].notna()]
    rows_dropped_r6 = rows_before_r6 - len(df)
    
    # R7: energy -> energy_kwh
    df['energy_kwh'] = df['energy'].apply(clean_energy)
    df['energy_kwh'] = df['energy_kwh'].round(2)
    rows_before_r7 = len(df)
    df = df[
        df['energy_kwh'].notna() & 
        (df['energy_kwh'] >= 0) & 
        (df['energy_kwh'] <= 100000)
    ]
    rows_dropped_r7 = rows_before_r7 - len(df)
    
    # R8: temperature -> temperature_c
    df['temperature_c'] = df['temperature'].apply(clean_temperature)
    # Set out-of-range values to NaN but keep the row
    df.loc[
        (df['temperature_c'] < -40) | (df['temperature_c'] > 50),
        'temperature_c'
    ] = np.nan
    
    # R9: Select columns and sort
    df = df[['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']]
    df = df.sort_values('reading_id')
    
    # Write temperature_c as empty string for NaN (for CSV output)
    df['temperature_c'] = df['temperature_c'].apply(lambda x: '' if pd.isna(x) else x)
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    output_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(output_path, index=False)
    
    # Write cleaning summary
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed': duplicates_removed,
        'rows_dropped_invalid_date': rows_dropped_r3,
        'rows_dropped_invalid_meter_id': rows_dropped_r4,
        'rows_dropped_invalid_building_type': rows_dropped_r5,
        'rows_dropped_invalid_tariff': rows_dropped_r6,
        'rows_dropped_invalid_energy': rows_dropped_r7
    }
    
    with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
