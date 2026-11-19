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
df.replace(missing_values, np.nan, inplace=True)

# R2: Remove duplicate records
df.drop_duplicates(subset=['reading_id'], keep='first', inplace=True)

# R3: Parse reading_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
df['reading_date'] = pd.to_datetime(df['reading_date'], errors='coerce', format=date_formats)
df.dropna(subset=['reading_date'], inplace=True)
df['reading_date'] = df['reading_date'].dt.strftime('%Y-%m-%d')

# R4: Convert meter_id to upper case
df['meter_id'] = df['meter_id'].str.upper()
df.dropna(subset=['meter_id'], inplace=True)

# R5: Map building_type
building_type_map = {
    'residential': 'Residential','res': 'Residential','resi': 'Residential',
    'commercial': 'Commercial', 'comm': 'Commercial',
    'industrial': 'Industrial', 'ind': 'Industrial'
}
df['building_type'] = df['building_type'].str.lower().map(building_type_map)
df.dropna(subset=['building_type'], inplace=True)
df['building_type'] = df['building_type'].astype('category')

# R6: Map tariff
tariff_map = {
    'peak': 'peak',
    'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'
}
df['tariff'] = df['tariff'].str.lower().map(tariff_map)
df.dropna(subset=['tariff'], inplace=True)
df['tariff'] = df['tariff'].astype('category')

# R7: Convert energy to energy_kwh
def convert_energy(energy):
    energy = energy.replace(',', '').strip()
    if energy.endswith('MWh'):
        return float(energy[:-3]) * 1000
    elif energy.endswith('kWh'):
        return float(energy[:-3])
    else:
        return float(energy)
df['energy_kwh'] = df['energy'].apply(convert_energy)
df = df[(df['energy_kwh'] >= 0) & (df['energy_kwh'] <= 100000)]
df['energy_kwh'] = df['energy_kwh'].round(2)

# R8: Convert temperature to temperature_c
def convert_temperature(temp):
    if pd.isna(temp):
        return np.nan
    temp = temp.replace('°', '').strip()
    if temp.endswith('F'):
        return round((float(temp[:-1]) - 32) * 5 / 9, 1)
    elif temp.endswith('C'):
        return round(float(temp[:-1]), 1)
    else:
        return round(float(temp), 1)
df['temperature_c'] = df['temperature'].apply(convert_temperature)
df.loc[(df['temperature_c'] < -40) | (df['temperature_c'] > 50), 'temperature_c'] = np.nan

# Select and order columns
df = df[['reading_id','reading_date','meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']]
df.sort_values(by='reading_id', inplace=True)

# Write the cleaned data to CSV
df.to_csv(OUTPUT_FILE, index=False)

# Write the cleaning summary
summary = {
    'raw_rows': len(pd.read_csv(INPUT_FILE)),
    'cleaned_rows': len(df),
    'dropped_duplicates': len(pd.read_csv(INPUT_FILE)) - len(df.drop_duplicates(subset=['reading_id'], keep='first')),
    'dropped_missing_reading_date': len(pd.read_csv(INPUT_FILE)) - len(df.dropna(subset=['reading_date']))
}
with open(SUMMARY_FILE, 'w') as f:
    f.write(json.dumps(summary, indent=2))