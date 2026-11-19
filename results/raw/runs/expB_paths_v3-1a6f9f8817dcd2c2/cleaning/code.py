import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ['', 'NA', 'N/A', 'null', 'None', '-']
DATE_FORMATS = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
BUILDING_TYPE_MAP = {'res': 'Residential','resi': 'Residential', 'comm': 'Commercial', 'ind': 'Industrial'}
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
def parse_date(date_str):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return np.nan
df['reading_date'] = df['reading_date'].apply(parse_date)
df.dropna(subset=['reading_date'], inplace=True)
df['reading_date'] = pd.to_datetime(df['reading_date']).dt.date

# R4: Convert meter_id to upper case
df['meter_id'] = df['meter_id'].str.upper()
df.dropna(subset=['meter_id'], inplace=True)

# R5: Map building_type
df['building_type'] = df['building_type'].str.lower().map(lambda x: BUILDING_TYPE_MAP.get(x, x)).str.title()
df = df[df['building_type'].isin(['Residential', 'Commercial', 'Industrial']) & df['building_type'].notna()]

# R6: Map tariff
df['tariff'] = df['tariff'].str.lower().map(TARIFF_MAP)
df.dropna(subset=['tariff'], inplace=True)
df = df[df['tariff'].isin(['peak', 'off-peak']) & df['tariff'].notna()]

# R7: Convert energy to kWh
def convert_energy(energy_str):
    energy_str = energy_str.replace(',', '').replace('MWh', '').replace('kWh', '')
    if energy_str.endswith('MWh'):
        energy_str = energy_str[:-3]
        value = float(energy_str) * 1000
    elif energy_str.endswith('kWh'):
        energy_str = energy_str[:-3]
        value = float(energy_str)
    else:
        value = float(energy_str)
    if 0 <= value <= 100000:
        return round(value, 2)
    return np.nan
df['energy_kwh'] = df['energy'].apply(convert_energy)
df.dropna(subset=['energy_kwh'], inplace=True)
df = df[df['energy_kwh'].between(0, 100000)]

# R8: Convert temperature to Celsius
def convert_temperature(temp_str):
    temp_str = temp_str.replace('°', '').replace('F', '').replace('C', '')
    if temp_str.endswith('F'):
        value = (float(temp_str[:-1]) - 32) * 5 / 9
    elif temp_str.endswith('C'):
        value = float(temp_str[:-1])
    else:
        value = float(temp_str)
    if -40 <= value <= 50:
        return round(value, 1)
    return np.nan
df['temperature_c'] = df['temperature'].apply(convert_temperature)
df['temperature_c'] = df['temperature_c'].where(df['temperature_c'].notna(), '')

# R9: Select and order columns
df = df[['reading_id','reading_date','meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']]
df.sort_values(by='reading_id', inplace=True)

# Write output
output_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaned.csv')
df.to_csv(output_file, index=False)

# Cleaning summary
cleaning_summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'dropped_duplicates': len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['reading_id'], keep='first')),
    'dropped_missing_reading_date': len(pd.read_csv(input_file)) - len(df.dropna(subset=['reading_date']),
    'dropped_missing_meter_id': len(pd.read_csv(input_file)) - len(df.dropna(subset=['meter_id']),
    'dropped_invalid_building_type': len(pd.read_csv(input_file)) - len(df[df['building_type'].isin(['Residential', 'Commercial', 'Industrial']) & df['building_type'].notna()]),
    'dropped_invalid_tariff': len(pd.read_csv(input_file)) - len(df[df['tariff'].isin(['peak', 'off-peak']) & df['tariff'].notna()]),
    'dropped_invalid_energy': len(pd.read_csv(input_file)) - len(df[df['energy_kwh'].between(0, 100000)]),
    'dropped_invalid_temperature': len(pd.read_csv(input_file)) - len(df[df['temperature_c'].notna() & (df['temperature_c'].between(-40, 50))])
}

summary_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaning_summary.json')
with open(summary_file, 'w') as f:
    f.write(json.dumps(cleaning_summary, indent=2))