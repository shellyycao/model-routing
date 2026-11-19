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
    
    # R1: Read as text, strip whitespace
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    raw_rows = len(df)
    
    # R1: Standardize missing values
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    def standardize_missing(x):
        if isinstance(x, str) and x.strip().lower() in [v.lower() for v in missing_vals]:
            return np.nan
        return x
    df = df.applymap(standardize_missing)
    
    # R2: Remove duplicates
    df = df.drop_duplicates(subset=['reading_id'], keep='first')
    
    # R3: Parse reading_date
    def parse_date(val):
        if pd.isna(val): return np.nan
        val = str(val).strip()
        formats = [
            ('%Y-%m-%d', None),
            ('%m/%d/%Y', None),
            ('%d-%b-%Y', None),
            ('%Y/%m/%d', None),
            ('%B %d, %Y', None),
            ('%B %d,%Y', None) # Handle missing space after comma just in case
        ]
        for fmt, _ in formats:
            try:
                return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return np.nan
    
    df['reading_date'] = df['reading_date'].apply(parse_date)
    df = df.dropna(subset=['reading_date'])
    
    # R4: meter_id
    df['meter_id'] = df['meter_id'].str.upper()
    df = df.dropna(subset=['meter_id'])
    
    # R5: building_type
    btype_map = {
        'res': 'Residential', 'resi': 'Residential', 'residential': 'Residential',
        'comm': 'Commercial', 'commercial': 'Commercial',
        'ind': 'Industrial', 'industrial': 'Industrial'
    }
    def map_building_type(val):
        if pd.isna(val): return np.nan
        return btype_map.get(str(val).strip().lower(), np.nan)
    df['building_type'] = df['building_type'].apply(map_building_type)
    df = df.dropna(subset=['building_type'])
    
    # R6: tariff
    tariff_map = {
        'peak': 'peak',
        'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'
    }
    def map_tariff(val):
        if pd.isna(val): return np.nan
        return tariff_map.get(str(val).strip().lower(), np.nan)
    df['tariff'] = df['tariff'].apply(map_tariff)
    df = df.dropna(subset=['tariff'])
    
    # R7: energy -> energy_kwh
    def clean_energy(val):
        if pd.isna(val): return np.nan
        val = str(val).replace(',', '').strip()
        multiplier = 1
        # Check for MWh
        mwh_match = re.search(r'\s*mwh$', val, re.IGNORECASE)
        if mwh_match:
            val = val[:mwh_match.start()]
            multiplier = 1000
        else:
            # Check for kWh
            kwh_match = re.search(r'\s*kwh$', val, re.IGNORECASE)
            if kwh_match:
                val = val[:kwh_match.start()]
        try:
            num = float(val) * multiplier
            return round(num, 2)
        except ValueError:
            return np.nan
    
    df['energy_kwh'] = df['energy'].apply(clean_energy)
    df = df.dropna(subset=['energy_kwh'])
    df = df[(df['energy_kwh'] >= 0) & (df['energy_kwh'] <= 100000)]
    
    # R8: temperature -> temperature_c
    def clean_temp(val):
        if pd.isna(val): return np.nan
        val = str(val).strip()
        is_fahrenheit = False
        
        # Check for F
        f_match = re.search(r'(°?f)$', val, re.IGNORECASE)
        if f_match:
            is_fahrenheit = True
            val = val[:f_match.start()]
        else:
            # Check for C
            c_match = re.search(r'(°?c)$', val, re.IGNORECASE)
            if c_match:
                val = val[:c_match.start()]
        
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
            
    df['temperature_c'] = df['temperature'].apply(clean_temp)
    # Note: R8 says keep row if temp is missing, so no dropna here.
    
    # R9: Output formatting
    final_cols = ['reading_id', 'reading_date', 'meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']
    df = df[final_cols]
    df = df.sort_values('reading_id')
    
    cleaned_rows = len(df)
    
    # Write cleaned CSV
    output_csv_path = os.path.join(output_dir, "cleaned.csv")
    # Handle NaN representation for temperature_c as empty string
    df.to_csv(output_csv_path, index=False, na_rep='')
    
    # Write summary JSON
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()