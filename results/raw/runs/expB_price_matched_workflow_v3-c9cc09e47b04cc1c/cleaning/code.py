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

    # Replace missing indicators with NaN for easier processing
    # We apply this logic specifically where needed or globally first
    # R1 says treat as missing. We will handle this in specific column logic.
    
    # R2: Remove duplicates based on reading_id
    # Keep first occurrence
    rows_before_dedup = len(df)
    df = df.drop_duplicates(subset=['reading_id'], keep='first')
    duplicates_removed = rows_before_dedup - len(df)
    
    # R3: reading_date parsing
    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
        'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    
    def parse_date(val):
        if is_missing(val): return None
        val = val.strip()
        
        # YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', val):
            return val
        
        # YYYY/MM/DD
        if re.match(r'^\d{4}/\d{2}/\d{2}$', val):
            return val.replace('/', '-')
        
        # MM/DD/YYYY
        m = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', val)
        if m:
            return f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
        
        # DD-Mon-YYYY
        m = re.match(r'^(\d{2})-([A-Za-z]{3})-(\d{4})$', val)
        if m:
            day, mon, year = m.groups()
            month_num = month_map.get(mon.capitalize())
            if month_num:
                return f"{year}-{month_num:02d}-{int(day):02d}"
        
        # Month D, YYYY
        m = re.match(r'^([A-Za-z]+) (\d{1,2}), (\d{4})$', val)
        if m:
            mon, day, year = m.groups()
            month_num = month_map.get(mon)
            if month_num:
                return f"{year}-{month_num:02d}-{int(day):02d}"
        
        return None

    df['reading_date'] = df['reading_date'].apply(parse_date)
    df = df[df['reading_date'].notna()]
    
    # R4: meter_id
    df['meter_id'] = df['meter_id'].apply(lambda x: str(x).upper() if not is_missing(x) else None)
    df = df[df['meter_id'].notna()]
    
    # R5: building_type
    def map_building_type(val):
        if is_missing(val): return None
        val_lower = str(val).lower().strip()
        if val_lower in ['res', 'resi', 'residential']: return 'Residential'
        if val_lower in ['comm', 'commercial']: return 'Commercial'
        if val_lower in ['ind', 'industrial']: return 'Industrial'
        return None
    
    df['building_type'] = df['building_type'].apply(map_building_type)
    df = df[df['building_type'].notna()]
    
    # R6: tariff
    def map_tariff(val):
        if is_missing(val): return None
        val_lower = str(val).lower().strip()
        if val_lower == 'peak': return 'peak'
        if val_lower in ['off-peak', 'offpeak', 'off peak']: return 'off-peak'
        return None
    
    df['tariff'] = df['tariff'].apply(map_tariff)
    df = df[df['tariff'].notna()]
    
    # R7: energy -> energy_kwh
    def parse_energy(val):
        if is_missing(val): return None
        val = str(val).strip()
        val = val.replace(',', '') # Remove commas
        
        is_mwh = False
        # Check for MWh (case insensitive)
        if val.lower().endswith('mwh'):
            is_mwh = True
            val = val[:-3].strip()
        elif val.lower().endswith('kwh'):
            val = val[:-3].strip()
        
        try:
            num = float(val)
            if is_mwh:
                num *= 1000
            return num
        except ValueError:
            return None
    
    df['energy_kwh'] = df['energy'].apply(parse_energy)
    # Drop missing/invalid
    df = df[df['energy_kwh'].notna()]
    # Range check
    df = df[(df['energy_kwh'] >= 0) & (df['energy_kwh'] <= 100000)]
    df['energy_kwh'] = df['energy_kwh'].round(2)
    
    # R8: temperature -> temperature_c
    def parse_temp(val):
        if is_missing(val): return np.nan
        val = str(val).strip()
        
        # Remove degree sign
        val = val.replace('°', '')
        
        is_f = False
        if val.upper().endswith('F'):
            is_f = True
            val = val[:-1].strip()
        elif val.upper().endswith('C'):
            val = val[:-1].strip()
        
        try:
            num = float(val)
            if is_f:
                num = (num - 32) * 5 / 9
            
            # Range check -40 to 50
            if num < -40 or num > 50:
                return np.nan
            return round(num, 1)
        except ValueError:
            return np.nan
            
    df['temperature_c'] = df['temperature'].apply(parse_temp)
    # R8 says KEEP the row even if temp is missing, so no drop here.
    
    # R9: Output formatting
    # Select columns
    final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
    df = df[final_cols]
    
    # Sort by reading_id
    df = df.sort_values(by='reading_id')
    
    # Write CSV
    # temperature_c NaN should be empty string
    df.to_csv(cleaned_path, index=False)
    
    cleaned_rows = len(df)
    
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows,
        "duplicates_removed": duplicates_removed
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()