import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
INPUT_FILE = os.path.join(os.environ['INPUT_DIR'], 'raw.csv')
OUTPUT_FILE = os.path.join(os.environ['OUTPUT_DIR'], 'cleaned.csv')
SUMMARY_FILE = os.path.join(os.environ['OUTPUT_DIR'], 'cleaning_summary.json')

# Read the raw data
df = pd.read_csv(INPUT_FILE, dtype=str)

# R1: Strip whitespace and treat certain values as missing
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
missing_values = ['', 'NA', 'N/A', 'null', 'None', '-']
df.replace(to_replace=missing_values, value=np.nan, inplace=True)

# R2: Remove duplicate records
df.drop_duplicates(subset=['reading_id'], keep='first', inplace=True)

# R3: Parse reading_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
df['reading_date'] = df['reading_date'].apply(lambda x: pd.to_datetime(x, errors='coerce', format=date_formats).strftime('%Y-%m-%d') if pd.notna(x) else np.nan)
df.dropna(subset=['reading_date'], inplace=True)

# R4: Convert meter_id to upper case
df['meter_id'] = df['meter_id'].str.upper()
df.dropna(subset=['meter_id'], inplace=True)

# R5: Map building_type
building_type_map = {'res': 'Residential','resi': 'Residential', 'commercial': 'Commercial', 'comm': 'Commercial', 'industrial': 'Industrial', 'ind': 'Industrial'}
df['building_type'] = df['building_type'].str.lower().map(building_type_map)
df.dropna(subset=['building_type'], inplace=True)

# R6: Map tariff
tariff_map = {'peak': 'peak', 'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'}
df['tariff'] = df['tariff'].str.lower().map(tariff_map)
df.dropna(subset=['tariff'], inplace=True)

# R7: Convert energy to energy_kwh
df['energy'] = df['energy'].str.replace(',', '').str.replace('MWh', '', case=False).str.replace('kWh', '', case=False)
df['energy_kwh'] = df['energy'].apply(lambda x: float(x) * 1000 if 'mwh' in x.lower() else float(x) if 'kwh' in x.lower() else float(x))
df = df[df['energy_kwh'].between(0, 100000)]
df['energy_kwh'] = df['energy_kwh'].round(2)
df.drop(columns=['energy'], inplace=True)

# R8: Convert temperature to temperature_c
df['temperature'] = df['temperature'].str.replace('°', '').str.replace('F', '', case=False).str.replace('C', '', case=False)
df['temperature_c'] = df['temperature'].apply(lambda x: (float(x) - 32) * 5 / 9 if 'f' in x.lower() else float(x))
df.loc[df['temperature_c'].between(-40, 50), 'temperature_c'] = df['temperature_c'].round(1)
df['temperature_c'] = df['temperature_c'].where(df['temperature_c'].between(-40, 50), np.nan)
df.drop(columns=['temperature'], inplace=True)

# R9: Select and order columns
df = df[['reading_id','reading_date','meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']]
df.sort_values(by='reading_id', inplace=True)

# Write the cleaned data to CSV
df.to_csv(OUTPUT_FILE, index=False)

# Create cleaning summary
summary = {
    'raw_rows': len(pd.read_csv(INPUT_FILE)),
    'cleaned_rows': len(df),
    'dropped_duplicates': len(pd.read_csv(INPUT_FILE)) - df['reading_id'].nunique(),
    'dropped_missing_reading_date': len(pd.read_csv(INPUT_FILE)) - len(df[pd['reading_date'].notna()]),
    'dropped_missing_meter_id': len(pd.read_csv(INPUT_FILE)) - len(df[df['meter_id'].notna()]),
    'dropped_invalid_building_type': len(pd.read_csv(INPUT_FILE)) - len(df[df['building_type'].notna()]),
    'dropped_invalid_tariff': len(pd.read_csv(INPUT_FILE)) - len(df[df['tariff'].notna()]),
    'dropped_invalid_energy_kwh': len(pd.read_csv(INPUT_FILE)) - len(df[df['energy_kwh'].between(0, 100000)]),
    'dropped_invalid_temperature_c': len(pd.read_csv(INPUT_FILE)) - len(df[df['temperature_c'].between(-40, 50)])
}

with open(SUMMARY_FILE, 'w') as f:
    json.dump(summary, f)
