import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # R1: Read as text and strip whitespace
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # R1: Define missing values
    missing_vals = ['', 'na', 'n/a', 'null', 'none', '-']
    def is_missing(val):
        if pd.isna(val): return True
        if not isinstance(val, str): return False
        return val.lower() in missing_vals

    # R2: Remove duplicates based on reading_id
    # Keep first occurrence in raw-file order
    df.drop_duplicates(subset='reading_id', keep='first', inplace=True)
    
    # R3: Parse reading_date
    def parse_date(val):
        if is_missing(val): return None
        # Try YYYY-MM-DD
        try: return datetime.strptime(val, '%Y-%m-%d').date()
        except: pass
        # Try MM/DD/YYYY
        try: return datetime.strptime(val, '%m/%d/%Y').date()
        except: pass
        # Try DD-Mon-YYYY
        try: return datetime.strptime(val, '%d-%b-%Y').date()
        except: pass
        # Try YYYY/MM/DD
        try: return datetime.strptime(val, '%Y/%m/%d').date()
        except: pass
        # Try Month D, YYYY
        try: return datetime.strptime(val, '%B %d, %Y').date()
        except: pass
        return None
    
    df['reading_date'] = df['reading_date'].apply(parse_date)
    df = df[df['reading_date'].notna()]

    # R4: meter_id to upper case, drop missing
    df['meter_id'] = df['meter_id'].apply(lambda x: x.upper() if not is_missing(x) else None)
    df = df[df['meter_id'].notna()]

    # R5: building_type mapping
    btype_map = {
        'res': 'Residential', 'resi': 'Residential', 'residential': 'Residential',
        'comm': 'Commercial', 'commercial': 'Commercial',
        'ind': 'Industrial', 'industrial': 'Industrial'
    }
    def map_building_type(val):
        if is_missing(val): return None
        return btype_map.get(val.lower(), None)
    df['building_type'] = df['building_type'].apply(map_building_type)
    df = df[df['building_type'].notna()]

    # R6: tariff mapping
    tariff_map = {
        'peak': 'peak',
        'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'
    }
    def map_tariff(val):
        if is_missing(val): return None
        return tariff_map.get(val.lower(), None)
    df['tariff'] = df['tariff'].apply(map_tariff)
    df = df[df['tariff'].notna()]

    # R7: energy -> energy_kwh
    def parse_energy(val):
        if is_missing(val): return None
        # Remove commas
        val = val.replace(',', '')
        # Check for MWh
        mwh_match = re.match(r'^([\d.]+)\s*mwh$', val, re.IGNORECASE)
        if mwh_match:
            try: return float(mwh_match.group(1)) * 1000
            except: return None
        # Check for kWh
        kwh_match = re.match(r'^([\d.]+)\s*kwh$', val, re.IGNORECASE)
        if kwh_match:
            try: return float(kwh_match.group(1))
            except: return None
        # Plain number
        try: return float(val)
        except: return None
    
    df['energy_kwh'] = df['energy'].apply(parse_energy)
    # Drop missing, <0, >100000
    df = df[df['energy_kwh'].notna()]
    df = df[(df['energy_kwh'] >= 0) & (df['energy_kwh'] <= 100000)]
    df['energy_kwh'] = df['energy_kwh'].round(2)

    # R8: temperature -> temperature_c
    def parse_temp(val):
        if is_missing(val): return np.nan
        # Remove degree sign
        val = val.replace('°', '')
        # Fahrenheit
        f_match = re.match(r'^([\d.-]+)\s*f$', val, re.IGNORECASE)
        if f_match:
            try:
                f = float(f_match.group(1))
                c = (f - 32) * 5 / 9
                return round(c, 1)
            except: return np.nan
        # Celsius
        c_match = re.match(r'^([\d.-]+)\s*c$', val, re.IGNORECASE)
        if c_match:
            try: return round(float(c_match.group(1)), 1)
            except: return np.nan
        # Plain number (assume C)
        try: return round(float(val), 1)
        except: return np.nan
    
    df['temperature_c'] = df['temperature'].apply(parse_temp)
    # Validate range -40 to 50, set out-of-range to NaN but keep row
    df.loc[~df['temperature_c'].between(-40, 50), 'temperature_c'] = np.nan

    # R9: Select columns and sort
    final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
    df = df[final_cols]
    df.sort_values('reading_id', inplace=True)
    
    # Write output
    df.to_csv(cleaned_path, index=False, date_format='%Y-%m-%d')
    
    # Write summary
    cleaned_rows = len(df)
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows
    }
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()