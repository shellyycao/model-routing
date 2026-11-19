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
df['reading_date'] = pd.to_datetime(df['reading_date'], errors='coerce', format=date_formats)
df.dropna(subset=['reading_date'], inplace=True)
df['reading_date'] = df['reading_date'].dt.strftime('%Y-%m-%d')

# R4: Convert meter_id to upper case
df['meter_id'] = df['meter_id'].str.upper()
df.dropna(subset=['meter_id'], inplace=True)

# R5: Map building_type
df['building_type'] = df['building_type'].str.lower().replace(BUILDING_TYPE_MAP, regex=True).str.title()
df.dropna(subset=['building_type'], inplace=True)
df['building_type'] = pd.Categorical(df['building_type'], categories=['Residential', 'Commercial', 'Industrial'])

# R6: Map tariff
df['tariff'] = df['tariff'].str.lower().replace(TARIFF_MAP)
df.dropna(subset=['tariff'], inplace=True)
df['tariff'] = pd.Categorical(df['tariff'], categories=['peak', 'off-peak'])

# R7: Convert energy to energy_kwh
df['energy'] = df['energy'].str.replace(',', '').str.replace('MWh', '', regex=False).str.replace('kWh', '', regex=False)
df['energy_kwh'] = df['energy'].str.contains('MWh', regex=False, na=False).astype(int) * 1000 + df['energy'].astype(float)
df['energy_kwh'] = df['energy_kwh'].round(2)
df.drop(columns=['energy'], inplace=True)
df.dropna(subset=['energy_kwh'], inplace=True)
df = df[(df['energy_kwh'] >= 0) & (df['energy_kwh'] <= 100000)]

# R8: Convert temperature to temperature_c
df['temperature'] = df['temperature'].str.replace('°F', 'F', regex=False).str.replace('°C', 'C', regex=False).str.replace('F', '', regex=False).str.replace('C', '', regex=False)
df['temperature_c'] = df['temperature'].apply(lambda x: (float(x) - 32) * 5 / 9 if x.endswith('F') else float(x) if x.endswith('C') or not x.endswith('F') else np.nan)
df['temperature_c'] = df['temperature_c'].round(1)
df.loc[(df['temperature_c'] < -40) | (df['temperature_c'] > 50), 'temperature_c'] = np.nan
df.drop(columns=['temperature'], inplace=True)

# R9: Select and order columns
df = df[['reading_id','reading_date','meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']]
df.sort_values(by='reading_id', inplace=True)

# Write output
output_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaned.csv')
df.to_csv(output_file, index=False)

# Write cleaning summary
summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'dropped_duplicates': len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['reading_id'], keep='first')),
    'dropped_missing_reading_date': len(df) - len(df.dropna(subset=['reading_date']))
}
summary_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaning_summary.json')
with open(summary_file, 'w') as f:
    f.write(json.dumps(summary, indent=2))

# Output filename
output_filename = 'cleaned.csv'

# Cleaning logic explanation
cleaning_logic = 'The script performs the following cleaning steps: 1) Reads every column as text and strips whitespace. 2) Treats specified values as missing. 3) Removes duplicate records. 4) Parses reading_date and converts to YYYY-MM-DD format. 5) Converts meter_id to upper case. 6) Maps building_type to Residential, Commercial, or Industrial. 7) Maps tariff to peak or off-peak. 8) Converts energy to energy_kwh and removes invalid values. 9) Converts temperature to temperature_c and removes invalid values. 10) Selects and orders the required columns. 11) Writes the cleaned data to cleaned.csv and a summary to cleaning_summary.json.'
