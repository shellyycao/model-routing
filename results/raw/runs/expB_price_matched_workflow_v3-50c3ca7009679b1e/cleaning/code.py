import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def clean_data():
    input_dir = os.environ.get("INPUT_DIR", ".")
    output_dir = os.environ.get("OUTPUT_DIR", ".")
    
    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    
    # R1: Read all columns as text and strip whitespace
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    
    # Track raw rows
    raw_rows = len(df)
    
    # Strip whitespace from all values
    for col in df.columns:
        df[col] = df[col].str.strip()
    
    # Define missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    # Replace missing values with actual NaN for easier handling
    df = df.apply(lambda x: x.where(~x.str.strip().str.lower().isin([v.lower() for v in missing_vals]), np.nan))
    
    # R2: Remove duplicates based on reading_id, keep first occurrence
    rows_before_r2 = len(df)
    df = df.drop_duplicates(subset='reading_id', keep='first')
    duplicates_removed = rows_before_r2 - len(df)
    
    # R3: Parse reading_date
    def parse_date(val):
        if pd.isna(val):
            return None
        val = val.strip()
        
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
        
        # Try 'Month D, YYYY' (full month name)
        try:
            return datetime.strptime(val, '%B %d, %Y').date()
        except ValueError:
            pass
        
        return None
    
    rows_before_r3 = len(df)
    df['reading_date'] = df['reading_date'].apply(parse_date)
    df = df[df['reading_date'].notna()]
    rows_after_r3 = len(df)
    r3_dropped = rows_before_r3 - rows_after_r3
    
    # R4: meter_id - convert to upper case, drop missing
    rows_before_r4 = len(df)
    df['meter_id'] = df['meter_id'].str.upper()
    df = df[df['meter_id'].notna()]
    rows_after_r4 = len(df)
    r4_dropped = rows_before_r4 - rows_after_r4
    
    # R5: building_type - map variants
    rows_before_r5 = len(df)
    def map_building_type(val):
        if pd.isna(val):
            return None
        val_lower = val.strip().lower()
        if val_lower in ['res', 'resi', 'residential']:
            return 'Residential'
        elif val_lower in ['comm', 'commercial']:
            return 'Commercial'
        elif val_lower in ['ind', 'industrial']:
            return 'Industrial'
        return None
    
    df['building_type'] = df['building_type'].apply(map_building_type)
    df = df[df['building_type'].notna()]
    rows_after_r5 = len(df)
    r5_dropped = rows_before_r5 - rows_after_r5
    
    # R6: tariff - map variants
    rows_before_r6 = len(df)
    def map_tariff(val):
        if pd.isna(val):
            return None
        val_lower = val.strip().lower()
        if val_lower == 'peak':
            return 'peak'
        elif val_lower in ['off-peak', 'offpeak', 'off peak']:
            return 'off-peak'
        return None
    
    df['tariff'] = df['tariff'].apply(map_tariff)
    df = df[df['tariff'].notna()]
    rows_after_r6 = len(df)
    r6_dropped = rows_before_r6 - rows_after_r6
    
    # R7: energy -> energy_kwh
    rows_before_r7 = len(df)
    def parse_energy(val):
        if pd.isna(val):
            return None
        val = val.strip()
        
        # Remove commas
        val = val.replace(',', '')
        
        # Check for MWh unit
        val_lower = val.lower()
        multiplier = 1
        if val_lower.endswith('mwh'):
            val = val[:-3].strip()
            multiplier = 1000
        elif val_lower.endswith('kwh'):
            val = val[:-3].strip()
        
        try:
            num = float(val)
            return round(num * multiplier, 2)
        except ValueError:
            return None
    
    df['energy_kwh'] = df['energy'].apply(parse_energy)
    df = df[df['energy_kwh'].notna()]
    df = df[(df['energy_kwh'] >= 0) & (df['energy_kwh'] <= 100000)]
    rows_after_r7 = len(df)
    r7_dropped = rows_before_r7 - rows_after_r7
    
    # R8: temperature -> temperature_c
    def parse_temperature(val):
        if pd.isna(val):
            return np.nan
        val = val.strip()
        
        # Remove degree sign
        val = val.replace('°', '')
        
        # Determine unit
        val_lower = val.lower()
        is_fahrenheit = False
        
        if val_lower.endswith('f'):
            is_fahrenheit = True
            val = val[:-1].strip()
        elif val_lower.endswith('c'):
            val = val[:-1].strip()
        
        try:
            num = float(val)
            if is_fahrenheit:
                num = (num - 32) * 5 / 9
            
            # Round to 1 decimal
            num = round(num, 1)
            
            # Check range -40 to 50
            if num < -40 or num > 50:
                return np.nan
            
            return num
        except ValueError:
            return np.nan
    
    df['temperature_c'] = df['temperature'].apply(parse_temperature)
    # Note: R8 does not drop rows, just sets invalid temps to NaN
    
    # R9: Select and order columns, sort by reading_id
    df = df[['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']]
    df = df.sort_values('reading_id')
    
    # Format reading_date as YYYY-MM-DD string
    df['reading_date'] = df['reading_date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else '')
    
    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False)
    
    # Write cleaning summary
    cleaned_rows = len(df)
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows,
        "duplicates_removed": duplicates_removed,
        "r3_date_parse_dropped": r3_dropped,
        "r4_meter_id_dropped": r4_dropped,
        "r5_building_type_dropped": r5_dropped,
        "r6_tariff_dropped": r6_dropped,
        "r7_energy_dropped": r7_dropped
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()
