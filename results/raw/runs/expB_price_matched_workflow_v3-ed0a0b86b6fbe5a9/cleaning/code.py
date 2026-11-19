import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def parse_date(date_str):
    """Parse date string to YYYY-MM-DD format."""
    if not date_str:
        return None
    
    # Try YYYY-MM-DD
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        pass
    
    # Try MM/DD/YYYY
    try:
        return datetime.strptime(date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
    except ValueError:
        pass
    
    # Try DD-Mon-YYYY (e.g., 05-Mar-2024)
    try:
        return datetime.strptime(date_str, '%d-%b-%Y').strftime('%Y-%m-%d')
    except ValueError:
        pass
    
    # Try YYYY/MM/DD
    try:
        return datetime.strptime(date_str, '%Y/%m/%d').strftime('%Y-%m-%d')
    except ValueError:
        pass
    
    # Try 'Month D, YYYY' (e.g., March 5, 2024)
    try:
        return datetime.strptime(date_str, '%B %d, %Y').strftime('%Y-%m-%d')
    except ValueError:
        pass
    
    return None

def clean_data(input_dir, output_dir):
    """Main cleaning function."""
    
    # Read raw CSV
    raw_path = os.path.join(input_dir, 'raw.csv')
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    
    raw_rows = len(df)
    
    # R1: Strip whitespace and standardize missing values
    missing_values = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    for col in df.columns:
        df[col] = df[col].str.strip()
        df[col] = df[col].apply(lambda x: '' if x.lower() in [m.lower() for m in missing_values] else x)
    
    # R2: Remove duplicates based on reading_id (keep first)
    df = df.drop_duplicates(subset=['reading_id'], keep='first')
    
    # R3: Parse reading_date
    df['reading_date'] = df['reading_date'].apply(parse_date)
    df = df[df['reading_date'].notna() & (df['reading_date'] != '')]
    
    # R4: meter_id - convert to upper case, drop missing
    df['meter_id'] = df['meter_id'].str.upper()
    df = df[df['meter_id'] != '']
    
    # R5: building_type - map variants
    building_map = {
        'res': 'Residential',
        'resi': 'Residential',
        'residential': 'Residential',
        'comm': 'Commercial',
        'commercial': 'Commercial',
        'ind': 'Industrial',
        'industrial': 'Industrial'
    }
    
    def map_building_type(val):
        if not val:
            return None
        val_lower = val.lower()
        return building_map.get(val_lower, None)
    
    df['building_type'] = df['building_type'].apply(map_building_type)
    df = df[df['building_type'].notna()]
    
    # R6: tariff - map variants
    def map_tariff(val):
        if not val:
            return None
        val_lower = val.lower().strip()
        if val_lower == 'peak':
            return 'peak'
        elif val_lower in ['off-peak', 'offpeak', 'off peak']:
            return 'off-peak'
        return None
    
    df['tariff'] = df['tariff'].apply(map_tariff)
    df = df[df['tariff'].notna()]
    
    # R7: energy -> energy_kwh
    def parse_energy(val):
        if not val:
            return None
        
        # Remove commas
        val = val.replace(',', '')
        
        # Check for MWh unit
        mwh_match = re.match(r'^([\d.]+)\s*mwh$', val, re.IGNORECASE)
        if mwh_match:
            try:
                return round(float(mwh_match.group(1)) * 1000, 2)
            except ValueError:
                return None
        
        # Check for kWh unit
        kwh_match = re.match(r'^([\d.]+)\s*kwh$', val, re.IGNORECASE)
        if kwh_match:
            try:
                return round(float(kwh_match.group(1)), 2)
            except ValueError:
                return None
        
        # No unit - assume kWh
        try:
            return round(float(val), 2)
        except ValueError:
            return None
    
    df['energy_kwh'] = df['energy'].apply(parse_energy)
    
    # Drop rows with missing, non-numeric, < 0, or > 100000
    df = df[df['energy_kwh'].notna()]
    df = df[(df['energy_kwh'] >= 0) & (df['energy_kwh'] <= 100000)]
    
    # R8: temperature -> temperature_c
    def parse_temperature(val):
        if not val:
            return None
        
        original = val
        
        # Remove degree sign and whitespace
        val = val.replace('°', '').strip()
        
        # Check for Fahrenheit
        f_match = re.match(r'^([\d.-]+)\s*F$', val, re.IGNORECASE)
        if f_match:
            try:
                f_val = float(f_match.group(1))
                c_val = round((f_val - 32) * 5 / 9, 1)
                if -40 <= c_val <= 50:
                    return c_val
                return None
            except ValueError:
                return None
        
        # Check for Celsius or no unit
        c_match = re.match(r'^([\d.-]+)\s*C?$', val, re.IGNORECASE)
        if c_match:
            try:
                c_val = round(float(c_match.group(1)), 1)
                if -40 <= c_val <= 50:
                    return c_val
                return None
            except ValueError:
                return None
        
        return None
    
    df['temperature_c'] = df['temperature'].apply(parse_temperature)
    # Keep rows even if temperature_c is missing (R8 says KEEP the row)
    
    # R9: Select and order columns, sort by reading_id
    output_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
    df = df[output_cols]
    df = df.sort_values('reading_id')
    
    # Write cleaned CSV
    output_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(output_path, index=False)
    
    cleaned_rows = len(df)
    
    # Write cleaning summary
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows
    }
    
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return 'cleaned.csv'

if __name__ == '__main__':
    input_dir = os.environ.get('INPUT_DIR', '.')
    output_dir = os.environ.get('OUTPUT_DIR', '.')
    clean_data(input_dir, output_dir)