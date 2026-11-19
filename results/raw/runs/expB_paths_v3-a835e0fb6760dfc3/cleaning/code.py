import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ['', 'NA', 'N/A', 'null', 'None', '-']
BUILDING_TYPE_MAPPING = {'Res': 'Residential', 'Resi': 'Residential', 'Comm': 'Commercial', 'Ind': 'Industrial'}
TARIFF_MAPPING = {'peak': 'peak', 'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'}

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
df['building_type'] = df['building_type'].str.lower().replace(BUILDING_TYPE_MAPPING, regex=True).str.title()
df.dropna(subset=['building_type'], inplace=True)
df['building_type'] = pd.Categorical(df['building_type'], categories=['Residential', 'Commercial', 'Industrial'])

# R6: Map tariff
df['tariff'] = df['tariff'].str.lower().replace(TARIFF_MAPPING)
df.dropna(subset=['tariff'], inplace=True)
df['tariff'] = pd.Categorical(df['tariff'], categories=['peak', 'off-peak'])

# R7: Convert energy to energy_kwh
df['energy'] = df['energy'].str.replace(',', '').str.replace('MWh', '', regex=False).str.replace('kWh', '', regex=False)
df['energy_kwh'] = df['energy'].apply(lambda x: float(x) * 1000 if x.endswith('MWh') else float(x) if x.endswith('kWh') else float(x))
df.drop(columns=['energy'], inplace=True)
df = df[df['energy_kwh'].between(0, 100000)]
df['energy_kwh'] = df['energy_kwh'].round(2)

# R8: Convert temperature to temperature_c
df['temperature'] = df['temperature'].str.replace('[°CF]', '', regex=True)
df['temperature_c'] = df['temperature'].apply(lambda x: (float(x) - 32) * 5 / 9 if x.endswith('F') else float(x))
df['temperature_c'] = df['temperature_c'].round(1)
df.loc[~df['temperature_c'].between(-40, 50), 'temperature_c'] = np.nan
df.drop(columns=['temperature'], inplace=True)

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
    'dropped_missing_reading_date': len(df) - len(df.dropna(subset=['reading_date']),
    'dropped_missing_meter_id': len(df) - len(df.dropna(subset=['meter_id']),
    'dropped_invalid_building_type': len(df) - len(df.dropna(subset=['building_type']),
    'dropped_invalid_tariff': len(df) - len(df.dropna(subset=['tariff']),
    'dropped_invalid_energy': len(df) - len(df[df['energy_kwh'].between(0, 100000)]),
    'dropped_invalid_temperature': len(df) - len(df[df['temperature_c'].between(-40, 50)])
}
summary_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaning_summary.json')
with open(summary_file, 'w') as f:
    json.dump(summary, f)

output_filename = 'cleaned.csv'
cleaning_logic = 'The script reads the raw CSV, strips whitespace, treats specified values as missing, removes duplicates, parses dates, converts meter IDs to upper case, maps building types and tariffs, converts energy to kWh, converts temperature to Celsius, selects and orders columns, sorts by reading ID, and writes the cleaned CSV and a cleaning summary JSON.'