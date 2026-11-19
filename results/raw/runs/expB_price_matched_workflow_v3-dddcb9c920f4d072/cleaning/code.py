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
    
    # R1: Read as text, strip whitespace
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # Strip whitespace
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    
    # Define missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    def is_missing(val):
        if pd.isna(val): return True
        if not isinstance(val, str): return False
        return val.strip() in missing_vals or val.strip().lower() in [v.lower() for v in missing_vals]
    
    # Replace missing values with NaN for easier handling
    df = df.applymap(lambda x: np.nan if is_missing(x) else x)
    
    # R2: Remove duplicates (keep first occurrence)
    rows_before_dedup = len(df)
    df = df.drop_duplicates(subset=['reading_id'], keep='first')
    duplicates_removed = rows_before_dedup - len(df)
    
    # R3: Parse reading_date
    def parse_date(val):
        if pd.isna(val): return None
        val = str(val).strip()
        
        # Try YYYY-MM-DD
        try: return datetime.strptime(val, '%Y-%m-%d').strftime('%Y-%m-%d')
        except: pass
        
        # Try MM/DD/YYYY
        try: return datetime.strptime(val, '%m/%d/%Y').strftime('%Y-%m-%d')
        except: pass
        
        # Try DD-Mon-YYYY (e.g., 05-Mar-2024)
        try: return datetime.strptime(val, '%d-%b-%Y').strftime('%Y-%m-%d')
        except: pass
        
        # Try YYYY/MM/DD
        try: return datetime.strptime(val, '%Y/%m/%d').strftime('%Y-%m-%d')
        except: pass
        
        # Try 'Month D, YYYY' (e.g., March 5, 2024)
        try: return datetime.strptime(val, '%B %d, %Y').strftime('%Y-%m-%d')
        except: pass
        
        return None
    
    df['reading_date'] = df['reading_date'].apply(parse_date)
    rows_before_r3 = len(df)
    df = df[df['reading_date'].notna()]
    r3_dropped = rows_before_r3 - len(df)
    
    # R4: meter_id to upper case, drop missing
    df['meter_id'] = df['meter_id'].apply(lambda x: str(x).upper() if pd.notna(x) else None)
    rows_before_r4 = len(df)
    df = df[df['meter_id'].notna()]
    r4_dropped = rows_before_r4 - len(df)
    
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
    
    def map_building_type(val):
        if pd.isna(val): return None
        val_lower = str(val).strip().lower()
        return building_map.get(val_lower, None)
    
    df['building_type'] = df['building_type'].apply(map_building_type)
    rows_before_r5 = len(df)
    df = df[df['building_type'].notna()]
    r5_dropped = rows_before_r5 - len(df)
    
    # R6: tariff mapping
    def map_tariff(val):
        if pd.isna(val): return None
        val_lower = str(val).strip().lower()
        if val_lower == 'peak':
            return 'peak'
        elif val_lower in ['off-peak', 'offpeak', 'off peak']:
            return 'off-peak'
        return None
    
    df['tariff'] = df['tariff'].apply(map_tariff)
    rows_before_r6 = len(df)
    df = df[df['tariff'].notna()]
    r6_dropped = rows_before_r6 - len(df)
    
    # R7: energy -> energy_kwh
    def parse_energy(val):
        if pd.isna(val): return None
        val = str(val).strip()
        
        # Remove commas
        val = val.replace(',', '')
        
        multiplier = 1
        val_lower = val.lower()
        
        # Check for MWh
        mwh_match = re.search(r'\s*mwh$', val_lower)
        if mwh_match:
            val = val[:mwh_match.start()]
            multiplier = 1000
        else:
            # Check for kWh
            kwh_match = re.search(r'\s*kwh$', val_lower)
            if kwh_match:
                val = val[:kwh_match.start()]
        
        try:
            num = float(val.strip())
            result = num * multiplier
            if result < 0 or result > 100000:
                return None
            return round(result, 2)
        except:
            return None
    
    df['energy_kwh'] = df['energy'].apply(parse_energy)
    rows_before_r7 = len(df)
    df = df[df['energy_kwh'].notna()]
    r7_dropped = rows_before_r7 - len(df)
    
    # R8: temperature -> temperature_c
    def parse_temperature(val):
        if pd.isna(val): return None
        val = str(val).strip()
        
        # Remove degree sign and unit
        val_clean = val.replace('°', '')
        val_lower = val_clean.lower()
        
        is_fahrenheit = False
        
        # Check for F
        f_match = re.search(r'\s*f$', val_lower)
        if f_match:
            is_fahrenheit = True
            val_clean = val_clean[:f_match.start()]
        else:
            # Check for C
            c_match = re.search(r'\s*c$', val_lower)
            if c_match:
                val_clean = val_clean[:c_match.start()]
        
        try:
            num = float(val_clean.strip())
            if is_fahrenheit:
                num = (num - 32) * 5 / 9
            
            result = round(num, 1)
            
            # Check range -40 to 50
            if result < -40 or result > 50:
                return None
            return result
        except:
            return None
    
    df['temperature_c'] = df['temperature'].apply(parse_temperature)
    # R8: Keep rows even if temperature is missing (no row drop)
    
    # R9: Select columns and sort
    output_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
    df = df[output_cols]
    df = df.sort_values('reading_id')
    
    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False)
    
    # Write cleaning summary
    cleaned_rows = len(df)
    summary = {
        'raw_rows': raw_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed': duplicates_removed,
        'r3_date_parse_failures': r3_dropped,
        'r4_meter_id_missing': r4_dropped,
        'r5_building_type_invalid': r5_dropped,
        'r6_tariff_invalid': r6_dropped,
        'r7_energy_invalid': r7_dropped
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()