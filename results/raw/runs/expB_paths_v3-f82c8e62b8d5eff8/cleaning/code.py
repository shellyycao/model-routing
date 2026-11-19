import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]
BUILDING_TYPE_MAP = {'Res': 'Residential', 'Resi': 'Residential', 'Comm': 'Commercial', 'Ind': 'Industrial'}
TARIFF_MAP = {'peak': 'peak', 'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'}

# Read input
input_file = os.path.join(os.environ['INPUT_DIR'], 'raw.csv')
df = pd.read_csv(input_file, dtype=str)

# R1: Strip whitespace and treat specified values as missing
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
df.replace(MISSING_VALUES, np.nan, inplace=True)

# R2: Remove duplicate records
df.drop_duplicates(subset=['reading_id'], keep='first', inplace=True)

# R3: Parse reading_date
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
df['reading_date'] = pd.to_datetime(df['reading_date'], format=date_formats, errors='coerce')
df.dropna(subset=['reading_date'], inplace=True)
df['reading_date'] = df['reading_date'].dt.strftime('%Y-%m-%d')

# R4: Convert meter_id to upper case
df['meter_id'] = df['meter_id'].str.upper()
df.dropna(subset=['meter_id'], inplace=True)

# R5: Map building_type
df['building_type'] = df['building_type'].str.lower().map(lambda x: BUILDING_TYPE_MAP.get(x, x)).str.title()
df = df[df['building_type'].isin(['Residential', 'Commercial', 'Industrial']) & df['building_type'].notna()]

# R6: Map tariff
df['tariff'] = df['tariff'].str.lower().map(TARIFF_MAP)
df.dropna(subset=['tariff'], inplace=True)

# R7: Clean energy -> energy_kwh
df['energy'] = df['energy'].str.replace(',', '').str.replace('MWh', '', case=False).str.replace('kWh', '', case=False)
df['energy_kwh'] = df['energy'].apply(lambda x: float(x) * 1000 if 'mwh' in x.lower() else float(x) if 'kwh' in x.lower() else float(x))
df = df[(df['energy_kwh'].between(0, 100000)) & df['energy_kwh'].notna()]
df['energy_kwh'] = df['energy_kwh'].round(2)

# R8: Clean temperature -> temperature_c
df['temperature'] = df['temperature'].str.replace('[°CF]', '', case=False, regex=True)
df['temperature_c'] = df.apply(lambda row: (float(row['temperature']) - 32) * 5 / 9 if row['temperature'].endswith('F') else float(row['temperature']), axis=1)
df['temperature_c'] = df['temperature_c'].round(1)
df.loc[(df['temperature_c'] < -40) | (df['temperature_c'] > 50), 'temperature_c'] = np.nan

# R9: Select and order columns, sort by reading_id
df = df[['reading_id','reading_date','meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']]
df.sort_values(by='reading_id', inplace=True)

# Write output
output_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaned.csv')
df.to_csv(output_file, index=False)

# Write cleaning summary
summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'dropped_duplicates': len(df) - len(df.drop_duplicates(subset=['reading_id'], keep='first')),
    'dropped_missing_reading_date': len(pd.read_csv(input_file)) - len(df.dropna(subset=['reading_date']),
    'dropped_missing_meter_id': len(df.dropna(subset=['meter_id']),
    'dropped_invalid_building_type': len(df[df['building_type'].isin(['Residential', 'Commercial', 'Industrial']) & df['building_type'].notna()],
    'dropped_invalid_tariff': len(df.dropna(subset=['tariff']),
    'dropped_invalid_energy_kwh': len(df[(df['energy_kwh'].between(0, 100000)) & df['energy_kwh'].notna()],
    'dropped_invalid_temperature_c': len(df[(df['temperature_c'].between(-40, 50)) & df['temperature_c'].notna()],
}
with open(os.path.join(os.environ['OUTPUT_DIR'], 'cleaning_summary.json'), 'w') as f:
    json.dump(summary, f)

output_filename = 'cleaned.csv'
cleaning_logic = 'The script reads the raw CSV, strips whitespace, treats specified values as missing, removes duplicates, parses dates, converts meter IDs to upper case, maps building types and tariffs, cleans energy and temperature values, selects and orders columns, and writes the cleaned data to a CSV file. It also writes a cleaning summary to a JSON file.'