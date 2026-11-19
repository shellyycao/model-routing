import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ['', 'NA', 'N/A', 'null', 'None', '-']
DATE_FORMATS = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
BUILDING_TYPE_MAP = {'Res': 'Residential', 'Resi': 'Residential', 'Comm': 'Commercial', 'Ind': 'Industrial'}
TARIFF_MAP = {'peak': 'peak', 'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'}

# Read input
input_file = os.path.join(os.environ['INPUT_DIR'], 'raw.csv')
df = pd.read_csv(input_file, dtype=str)

# R1: Strip whitespace and treat specified values as missing
df = df.applymap(lambda x: x.strip() if pd.notna(x) else x)
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

# R4: Convert meter_id to upper case
df['meter_id'] = df['meter_id'].str.upper()
df.dropna(subset=['meter_id'], inplace=True)

# R5: Map building_type
df['building_type'] = df['building_type'].str.lower().replace(BUILDING_TYPE_MAP, regex=True)
df['building_type'] = df['building_type'].str.title()
df.dropna(subset=['building_type'], inplace=True)

# R6: Map tariff
df['tariff'] = df['tariff'].str.lower().replace(TARIFF_MAP)
df.dropna(subset=['tariff'], inplace=True)

# R7: Convert energy to energy_kwh
def convert_energy(energy_str):
    energy_str = energy_str.replace(',', '')
    if energy_str.lower().endswith('mwh'):
        energy_str = energy_str[:-3]
        energy_value = float(energy_str) * 1000
    elif energy_str.lower().endswith('kwh'):
        energy_str = energy_str[:-3]
        energy_value = float(energy_str)
    else:
        energy_value = float(energy_str)
    if energy_value < 0 or energy_value > 100000:
        return np.nan
    return round(energy_value, 2)
df['energy_kwh'] = df['energy'].apply(convert_energy)
df.dropna(subset=['energy_kwh'], inplace=True)

# R8: Convert temperature to temperature_c
def convert_temperature(temp_str):
    if pd.isna(temp_str):
        return np.nan
    temp_str = temp_str.replace('°', '').strip()
    if temp_str.lower().endswith('f'):
        temp_value = (float(temp_str[:-1]) - 32) * 5 / 9
    elif temp_str.lower().endswith('c'):
        temp_value = float(temp_str[:-1])
    else:
        temp_value = float(temp_str)
    if temp_value < -40 or temp_value > 50:
        return np.nan
    return round(temp_value, 1)
df['temperature_c'] = df['temperature'].apply(convert_temperature)

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
    'dropped_missing_reading_date': len(pd.read_csv(input_file)) - len(df.dropna(subset=['reading_date'])) - (len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['reading_id'], keep='first'))),
    'dropped_missing_meter_id': len(df.dropna(subset=['reading_date'])) - len(df.dropna(subset=['meter_id'])),
    'dropped_invalid_building_type': len(df.dropna(subset=['meter_id'])) - len(df.dropna(subset=['building_type'])) - (len(df.dropna(subset=['meter_id'])) - len(df.dropna(subset=['reading_date']))),
    'dropped_invalid_tariff': len(df.dropna(subset=['building_type'])) - len(df.dropna(subset=['tariff'])) - (len(df.dropna(subset=['building_type'])) - len(df.dropna(subset=['meter_id']))),
    'dropped_invalid_energy': len(df.dropna(subset=['tariff'])) - len(df.dropna(subset=['energy_kwh'])) - (len(df.dropna(subset=['tariff'])) - len(df.dropna(subset=['building_type']))),
    'dropped_invalid_temperature': len(df.dropna(subset=['energy_kwh'])) - len(df.dropna(subset=['temperature_c'])) - (len(df.dropna(subset=['energy_kwh'])) - len(df.dropna(subset=['tariff'])))
}
summary_file = os.path.join(os.environ['OUTPUT_DIR'], 'cleaning_summary.json')
with open(summary_file, 'w') as f:
    f.write(json.dumps(summary, indent=2))