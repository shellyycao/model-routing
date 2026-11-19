import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def clean_data():
    input_dir = os.environ.get('INPUT_DIR', '.')
    output_dir = os.environ.get('OUTPUT_DIR', '.')
    
    # R1: Read and strip whitespace, handle missing values
    raw_path = os.path.join(input_dir, 'raw.csv')
    
    # Read as text to strip whitespace properly
    with open(raw_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Parse CSV manually to handle whitespace stripping
    header = [h.strip() for h in lines[0].strip().split(',')]
    data_rows = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        # Handle quoted fields
        if '"' in line:
            # Simple CSV parsing with quotes
            parts = []
            in_quote = False
            current = ''
            for char in line:
                if char == '"':
                    in_quote = not in_quote
                elif char == ',' and not in_quote:
                    parts.append(current.strip())
                    current = ''
                else:
                    current += char
            parts.append(current.strip())
            row = parts
        else:
            row = [v.strip() for v in line.split(',')]
        data_rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data_rows, columns=header)
    raw_rows = len(df)
    
    # R1: Treat values as missing
    missing_values = ['', 'NA', 'N/A', 'null', 'None', '-']
    for col in df.columns:
        df[col] = df[col].apply(lambda x: '' if str(x).strip().lower() in [m.lower() for m in missing_values] else x)
    
    # R2: Remove duplicates based on reading_id
    before_r2 = len(df)
    df = df.drop_duplicates(subset=['reading_id'], keep='first')
    r2_removed = before_r2 - len(df)
    
    # R3: Parse reading_date
    def parse_date(val):
        if not val:
            return None
        val = str(val).strip()
        
        # Try YYYY-MM-DD
        try:
            return datetime.strptime(val, '%Y-%m-%d').strftime('%Y-%m-%d')
        except:
            pass
        
        # Try MM/DD/YYYY
        try:
            return datetime.strptime(val, '%m/%d/%Y').strftime('%Y-%m-%d')
        except:
            pass
        
        # Try DD-Mon-YYYY
        try:
            return datetime.strptime(val, '%d-%b-%Y').strftime('%Y-%m-%d')
        except:
            pass
        
        # Try YYYY/MM/DD
        try:
            return datetime.strptime(val, '%Y/%m/%d').strftime('%Y-%m-%d')
        except:
            pass
        
        # Try 'Month D, YYYY'
        try:
            return datetime.strptime(val, '%B %d, %Y').strftime('%Y-%m-%d')
        except:
            pass
        
        return None
    
    df['reading_date'] = df['reading_date'].apply(parse_date)
    before_r3 = len(df)
    df = df[df['reading_date'].notna()]
    r3_removed = before_r3 - len(df)
    
    # R4: meter_id uppercase and drop missing
    df['meter_id'] = df['meter_id'].apply(lambda x: str(x).upper() if x else '')
    before_r4 = len(df)
    df = df[df['meter_id'] != '']
    r4_removed = before_r4 - len(df)
    
    # R5: building_type mapping
    def map_building_type(val):
        if not val:
            return None
        val = str(val).strip().lower()
        if val in ['res', 'resi', 'residential']:
            return 'Residential'
        elif val in ['comm', 'commercial']:
            return 'Commercial'
        elif val in ['ind', 'industrial']:
            return 'Industrial'
        return None
    
    df['building_type'] = df['building_type'].apply(map_building_type)
    before_r5 = len(df)
    df = df[df['building_type'].notna()]
    r5_removed = before_r5 - len(df)
    
    # R6: tariff mapping
    def map_tariff(val):
        if not val:
            return None
        val = str(val).strip().lower()
        if val == 'peak':
            return 'peak'
        elif val in ['off-peak', 'offpeak', 'off peak']:
            return 'off-peak'
        return None
    
    df['tariff'] = df['tariff'].apply(map_tariff)
    before_r6 = len(df)
    df = df[df['tariff'].notna()]
    r6_removed = before_r6 - len(df)
    
    # R7: energy -> energy_kwh
    def parse_energy(val):
        if not val:
            return None
        val = str(val).strip()
        val = val.replace(',', '')
        
        # Check for MWh
        mwh_match = re.match(r'^([\d.]+)\s*MWh$', val, re.IGNORECASE)
        if mwh_match:
            try:
                return float(mwh_match.group(1)) * 1000
            except:
                return None
        
        # Check for kWh
        kwh_match = re.match(r'^([\d.]+)\s*kWh$', val, re.IGNORECASE)
        if kwh_match:
            try:
                return float(kwh_match.group(1))
            except:
                return None
        
        # No unit, assume kWh
        try:
            return float(val)
        except:
            return None
    
    df['energy_kwh'] = df['energy'].apply(parse_energy)
    before_r7 = len(df)
    df = df[df['energy_kwh'].notna()]
    df = df[(df['energy_kwh'] >= 0) & (df['energy_kwh'] <= 100000)]
    df['energy_kwh'] = df['energy_kwh'].round(2)
    r7_removed = before_r7 - len(df)
    
    # R8: temperature -> temperature_c
    def parse_temperature(val):
        if not val:
            return None
        val = str(val).strip()
        
        # Remove degree sign and unit
        val_clean = re.sub(r'[°\s]', '', val)
        
        # Check for Fahrenheit
        f_match = re.match(r'^([\d.-]+)F$', val_clean, re.IGNORECASE)
        if f_match:
            try:
                f_val = float(f_match.group(1))
                c_val = (f_val - 32) * 5 / 9
                return round(c_val, 1)
            except:
                return None
        
        # Check for Celsius or no unit
        c_match = re.match(r'^([\d.-]+)C?$', val_clean, re.IGNORECASE)
        if c_match:
            try:
                return round(float(c_match.group(1)), 1)
            except:
                return None
        
        return None
    
    df['temperature_c'] = df['temperature'].apply(parse_temperature)
    # R8: Set out-of-range temperature to missing but keep row
    df.loc[(df['temperature_c'] < -40) | (df['temperature_c'] > 50), 'temperature_c'] = np.nan
    r8_set_missing = df['temperature_c'].isna().sum()
    
    # R9: Select columns and sort
    df = df[['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']]
    df = df.sort_values('reading_id')
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    output_path = os.path.join(output_dir, 'cleaned.csv')
    df.to_csv(output_path, index=False)
    
    # Write cleaning summary
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'r2_duplicates_removed': r2_removed,
        'r3_invalid_dates_removed': r3_removed,
        'r4_missing_meter_id_removed': r4_removed,
        'r5_invalid_building_type_removed': r5_removed,
        'r6_invalid_tariff_removed': r6_removed,
        'r7_invalid_energy_removed': r7_removed,
        'r8_temperature_set_missing': r8_set_missing
    }
    
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()