import os
import json
import re
import pandas as pd
import numpy as np
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
    stats = {"raw_rows": raw_rows}
    
    # R1: Strip whitespace and standardize missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    def clean_value(x):
        if pd.isna(x): return ''
        s = str(x).strip()
        if s.lower() in [v.lower() for v in missing_vals]: return ''
        return s
    
    for col in df.columns:
        df[col] = df[col].apply(clean_value)
    
    # R2: Remove duplicates (keep first)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['reading_id'], keep='first')
    stats['duplicates_removed'] = before_dedup - len(df)
    
    # R3: Parse reading_date
    month_map = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    full_month_map = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                      'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}
    
    def parse_date(s):
        if not s: return None
        # YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
            return s
        # YYYY/MM/DD
        if re.match(r'^\d{4}/\d{2}/\d{2}$', s):
            parts = s.split('/')
            return f"{parts[0]}-{parts[1]}-{parts[2]}"
        # MM/DD/YYYY
        if re.match(r'^\d{2}/\d{2}/\d{4}$', s):
            parts = s.split('/')
            return f"{parts[2]}-{parts[0]}-{parts[1]}"
        # DD-Mon-YYYY
        m = re.match(r'^(\d{2})-([A-Za-z]{3})-(\d{4})$', s)
        if m:
            day, mon, year = m.groups()
            mon_num = month_map.get(mon.title())
            if mon_num:
                return f"{year}-{mon_num:02d}-{int(day):02d}"
        # Month D, YYYY
        m = re.match(r'^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})$', s)
        if m:
            mon_name, day, year = m.groups()
            mon_num = full_month_map.get(mon_name)
            if mon_num:
                return f"{year}-{mon_num:02d}-{int(day):02d}"
        return None
    
    df['reading_date'] = df['reading_date'].apply(parse_date)
    before = len(df)
    df = df[df['reading_date'].notna() & (df['reading_date'] != '')]
    stats['dropped_invalid_dates'] = before - len(df)
    
    # R4: meter_id uppercase, drop missing
    df['meter_id'] = df['meter_id'].str.upper()
    before = len(df)
    df = df[df['meter_id'] != '']
    stats['dropped_missing_meter_id'] = before - len(df)
    
    # R5: building_type mapping
    btype_map = {
        'residential': 'Residential', 'res': 'Residential', 'resi': 'Residential',
        'commercial': 'Commercial', 'comm': 'Commercial',
        'industrial': 'Industrial', 'ind': 'Industrial'
    }
    df['building_type'] = df['building_type'].str.lower().map(btype_map)
    before = len(df)
    df = df[df['building_type'].notna()]
    stats['dropped_invalid_building_type'] = before - len(df)
    
    # R6: tariff mapping
    tariff_map = {
        'peak': 'peak',
        'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'
    }
    df['tariff'] = df['tariff'].str.lower().map(tariff_map)
    before = len(df)
    df = df[df['tariff'].notna()]
    stats['dropped_invalid_tariff'] = before - len(df)
    
    # R7: energy -> energy_kwh
    def parse_energy(s):
        if not s: return None
        s = s.replace(',', '')
        s_lower = s.lower().strip()
        multiplier = 1
        if s_lower.endswith('mwh'):
            s = s[:-3].strip()
            multiplier = 1000
        elif s_lower.endswith('kwh'):
            s = s[:-3].strip()
        try:
            val = float(s) * multiplier
            if val < 0 or val > 100000:
                return None
            return round(val, 2)
        except:
            return None
    
    df['energy_kwh'] = df['energy'].apply(parse_energy)
    before = len(df)
    df = df[df['energy_kwh'].notna()]
    stats['dropped_invalid_energy'] = before - len(df)
    
    # R8: temperature -> temperature_c
    def parse_temp(s):
        if not s: return ''
        s = s.strip()
        # Remove degree sign
        s = s.replace('°', '')
        s_lower = s.lower()
        is_fahrenheit = False
        if s_lower.endswith('f'):
            is_fahrenheit = True
            s = s[:-1].strip()
        elif s_lower.endswith('c'):
            s = s[:-1].strip()
        try:
            val = float(s)
            if is_fahrenheit:
                val = (val - 32) * 5 / 9
            val = round(val, 1)
            if val < -40 or val > 50:
                return ''
            return val
        except:
            return ''
    
    df['temperature_c'] = df['temperature'].apply(parse_temp)
    # R8: Keep rows even if temperature is missing (no drop)
    
    # R9: Select columns and sort
    output_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
    df = df[output_cols]
    df = df.sort_values('reading_id')
    
    stats['cleaned_rows'] = len(df)
    
    # Write cleaned CSV
    df.to_csv(cleaned_path, index=False)
    
    # Write summary JSON
    with open(summary_path, 'w') as f:
        json.dump(stats, f, indent=2)

if __name__ == "__main__":
    clean_data()