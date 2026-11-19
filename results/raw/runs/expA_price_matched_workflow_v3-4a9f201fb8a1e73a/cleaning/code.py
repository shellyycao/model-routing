import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def clean_data():
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    
    raw_path = os.path.join(input_dir, "raw.csv")
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    
    raw_rows = len(df)
    stats = {'raw_rows': raw_rows}
    
    # R1: Strip whitespace and standardize missing values
    def standardize_missing(val):
        if not isinstance(val, str):
            return val
        val = val.strip()
        if val.lower() in ['', 'na', 'n/a', 'null', 'none', '-']:
            return np.nan
        return val
    
    for col in df.columns:
        df[col] = df[col].apply(standardize_missing)
    
    # R2: Remove duplicates based on reading_id
    before_r2 = len(df)
    df = df.drop_duplicates(subset=['reading_id'], keep='first')
    stats['duplicates_removed'] = before_r2 - len(df)
    
    # R3: Parse reading_date
    def parse_date(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        # Try YYYY-MM-DD
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except ValueError:
            pass
        # Try MM/DD/YYYY
        try:
            return datetime.strptime(val, '%m/%d/%Y').date()
        except ValueError:
            pass
        # Try DD-Mon-YYYY
        try:
            return datetime.strptime(val, '%d-%b-%Y').date()
        except ValueError:
            pass
        # Try YYYY/MM/DD
        try:
            return datetime.strptime(val, '%Y/%m/%d').date()
        except ValueError:
            pass
        # Try Month D, YYYY
        try:
            return datetime.strptime(val, '%B %d, %Y').date()
        except ValueError:
            pass
        return None
    
    before_r3 = len(df)
    df['reading_date'] = df['reading_date'].apply(parse_date)
    df = df.dropna(subset=['reading_date'])
    stats['invalid_dates_dropped'] = before_r3 - len(df)
    df['reading_date'] = df['reading_date'].apply(lambda x: x.strftime('%Y-%m-%d') if x else None)
    
    # R4: meter_id to upper case, drop missing
    before_r4 = len(df)
    df['meter_id'] = df['meter_id'].str.upper()
    df = df.dropna(subset=['meter_id'])
    stats['invalid_meter_id_dropped'] = before_r4 - len(df)
    
    # R5: building_type mapping
    def map_building_type(val):
        if pd.isna(val):
            return None
        val = str(val).strip().lower()
        if val in ['res', 'resi', 'residential']:
            return 'Residential'
        if val in ['comm', 'commercial']:
            return 'Commercial'
        if val in ['ind', 'industrial']:
            return 'Industrial'
        return None
    
    before_r5 = len(df)
    df['building_type'] = df['building_type'].apply(map_building_type)
    df = df.dropna(subset=['building_type'])
    stats['invalid_building_type_dropped'] = before_r5 - len(df)
    
    # R6: tariff mapping
    def map_tariff(val):
        if pd.isna(val):
            return None
        val = str(val).strip().lower()
        if val == 'peak':
            return 'peak'
        if val in ['off-peak', 'offpeak', 'off peak']:
            return 'off-peak'
        return None
    
    before_r6 = len(df)
    df['tariff'] = df['tariff'].apply(map_tariff)
    df = df.dropna(subset=['tariff'])
    stats['invalid_tariff_dropped'] = before_r6 - len(df)
    
    # R7: energy -> energy_kwh
    def parse_energy(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        val = val.replace(',', '')
        
        is_mwh = False
        # Check for MWh
        match = re.search(r'\s*mwh$', val, re.IGNORECASE)
        if match:
            is_mwh = True
            val = val[:match.start()]
        else:
            # Check for kWh
            match = re.search(r'\s*kwh$', val, re.IGNORECASE)
            if match:
                val = val[:match.start()]
        
        try:
            num = float(val)
            if is_mwh:
                num *= 1000
            return num
        except ValueError:
            return None
    
    before_r7 = len(df)
    df['energy_kwh'] = df['energy'].apply(parse_energy)
    df = df.dropna(subset=['energy_kwh'])
    df = df[(df['energy_kwh'] >= 0) & (df['energy_kwh'] <= 100000)]
    df['energy_kwh'] = df['energy_kwh'].round(2)
    stats['invalid_energy_dropped'] = before_r7 - len(df)
    
    # R8: temperature -> temperature_c
    def parse_temperature(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip()
        
        # Remove degree sign
        val = val.replace('°', '')
        
        is_fahrenheit = False
        # Check for F
        if val.upper().endswith('F'):
            is_fahrenheit = True
            val = val[:-1]
        elif val.upper().endswith('C'):
            val = val[:-1]
        
        try:
            num = float(val)
            if is_fahrenheit:
                num = (num - 32) * 5 / 9
            return round(num, 1)
        except ValueError:
            return np.nan
    
    df['temperature_c'] = df['temperature'].apply(parse_temperature)
    # Set out-of-range to NaN
    df.loc[(df['temperature_c'] < -40) | (df['temperature_c'] > 50), 'temperature_c'] = np.nan
    
    # R9: Final output preparation
    final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
    df = df[final_cols]
    df = df.sort_values('reading_id')
    
    cleaned_rows = len(df)
    stats['cleaned_rows'] = cleaned_rows
    
    # Write cleaned CSV
    output_csv_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(output_csv_path, index=False)
    
    # Write summary JSON
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(stats, f, indent=2)

if __name__ == "__main__":
    clean_data()