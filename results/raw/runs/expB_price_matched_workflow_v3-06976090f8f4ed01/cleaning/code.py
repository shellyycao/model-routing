import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime

def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    # Read raw data
    raw_path = os.path.join(input_dir, "raw.csv")
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df)
    
    # Initialize summary stats
    stats = {
        'raw_rows': raw_rows,
        'duplicates_removed': 0,
        'rows_dropped_date': 0,
        'rows_dropped_meter': 0,
        'rows_dropped_building': 0,
        'rows_dropped_tariff': 0,
        'rows_dropped_energy': 0,
        'temperature_set_missing': 0
    }
    
    # R1: Strip whitespace and standardize missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    for col in df.columns:
        df[col] = df[col].str.strip()
        df[col] = df[col].replace(missing_vals, np.nan)
    
    # R2: Remove duplicates based on reading_id
    before_dedup = len(df)
    df = df.drop_duplicates(subset='reading_id', keep='first')
    stats['duplicates_removed'] = before_dedup - len(df)
    
    # R3: Parse reading_date
    def parse_date(val):
        if pd.isna(val):
            return None
        val = str(val).strip()
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d-%b-%Y',
            '%Y/%m/%d',
            '%B %d, %Y'
        ]
        for fmt in formats:
            try:
                return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None
    
    df['reading_date'] = df['reading_date'].apply(parse_date)
    before_drop = len(df)
    df = df[df['reading_date'].notna()]
    stats['rows_dropped_date'] = before_drop - len(df)
    
    # R4: meter_id - uppercase and drop missing
    df['meter_id'] = df['meter_id'].str.upper()
    before_drop = len(df)
    df = df[df['meter_id'].notna()]
    stats['rows_dropped_meter'] = before_drop - len(df)
    
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
    
    def map_building(val):
        if pd.isna(val):
            return None
        return building_map.get(str(val).lower(), None)
    
    df['building_type'] = df['building_type'].apply(map_building)
    before_drop = len(df)
    df = df[df['building_type'].notna()]
    stats['rows_dropped_building'] = before_drop - len(df)
    
    # R6: tariff mapping
    def map_tariff(val):
        if pd.isna(val):
            return None
        val_lower = str(val).lower().replace('-', '').replace(' ', '')
        if val_lower == 'peak':
            return 'peak'
        elif val_lower in ['offpeak', 'off peak']:
            return 'off-peak'
        return None
    
    df['tariff'] = df['tariff'].apply(map_tariff)
    before_drop = len(df)
    df = df[df['tariff'].notna()]
    stats['rows_dropped_tariff'] = before_drop - len(df)
    
    # R7: energy -> energy_kwh
    def parse_energy(val):
        if pd.isna(val):
            return None
        val = str(val).replace(',', '').strip()
        val_lower = val.lower()
        multiplier = 1
        if val_lower.endswith('mwh'):
            val = val[:-3].strip()
            multiplier = 1000
        elif val_lower.endswith('kwh'):
            val = val[:-3].strip()
        try:
            num = float(val) * multiplier
            if num < 0 or num > 100000:
                return None
            return round(num, 2)
        except ValueError:
            return None
    
    df['energy_kwh'] = df['energy'].apply(parse_energy)
    before_drop = len(df)
    df = df[df['energy_kwh'].notna()]
    stats['rows_dropped_energy'] = before_drop - len(df)
    
    # R8: temperature -> temperature_c
    def parse_temp(val):
        if pd.isna(val):
            return np.nan
        val = str(val).strip()
        # Remove degree sign
        val = val.replace('°', '')
        val_lower = val.lower()
        is_fahrenheit = False
        if val_lower.endswith('f'):
            val = val[:-1].strip()
            is_fahrenheit = True
        elif val_lower.endswith('c'):
            val = val[:-1].strip()
        try:
            num = float(val)
            if is_fahrenheit:
                num = (num - 32) * 5 / 9
            num = round(num, 1)
            if num < -40 or num > 50:
                return np.nan
            return num
        except ValueError:
            return np.nan
    
    df['temperature_c'] = df['temperature'].apply(parse_temp)
    stats['temperature_set_missing'] = df['temperature_c'].isna().sum()
    
    # R9: Select columns and sort
    final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
    df = df[final_cols].sort_values('reading_id')
    
    # Write cleaned CSV
    output_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(output_path, index=False)
    
    # Write summary JSON
    stats['cleaned_rows'] = len(df)
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(stats, f, indent=2)

if __name__ == "__main__":
    main()
