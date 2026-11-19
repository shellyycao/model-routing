import os
import pandas as pd
import numpy as np
from datetime import datetime

# Constants
MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]
DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
BUILDING_TYPE_MAP = {'Res': 'Residential', 'Resi': 'Residential', 'Comm': 'Commercial', 'Ind': 'Industrial'}
TARIFF_MAP = {'peak': 'peak', 'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'}

# Read input
input_file = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
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
df['building_type'] = df['building_type'].str.lower().replace(BUILDING_TYPE_MAP, regex=True).str.title()
df.dropna(subset=['building_type'], inplace=True)
df['building_type'] = df['building_type'].astype('category')

# R6: Map tariff
df['tariff'] = df['tariff'].str.lower().replace(TARIFF_MAP)
df.dropna(subset=['tariff'], inplace=True)
df['tariff'] = df['tariff'].astype('category')

# R7: Convert energy to energy_kwh
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
    if value < 0 or value > 100000:
        return np.nan
    return round(value, 2)
df['energy_kwh'] = df['energy'].apply(convert_energy)
df.dropna(subset=['energy_kwh'], inplace=True)
df['energy_kwh'] = df['energy_kwh'].astype(float)

# R8: Convert temperature to temperature_c
def convert_temperature(temp_str):
    if pd.isna(temp_str):
        return np.nan
    temp_str = temp_str.replace('°', '').replace('F', '').replace('C', '')
    if temp_str.endswith('F'):
        value = (float(temp_str[:-1]) - 32) * 5 / 9
    elif temp_str.endswith('C'):
        value = float(temp_str[:-1])
    else:
        value = float(temp_str)
    if value < -40 or value > 50:
        return np.nan
    return round(value, 1)
df['temperature_c'] = df['temperature'].apply(convert_temperature)
df['temperature_c'] = df['temperature_c'].astype(float)

# R9: Select and order columns, sort by reading_id
df = df[['reading_id','reading_date','meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']]
df.sort_values(by='reading_id', inplace=True)

# Write output
output_file = os.path.join(os.environ["OUTPUT_DIR"], "cleaned.csv")
df.to_csv(output_file, index=False)

# Cleaning summary
cleaning_summary = {
    'raw_rows': len(pd.read_csv(input_file)),
    'cleaned_rows': len(df),
    'dropped_duplicates': len(pd.read_csv(input_file)) - len(df.drop_duplicates(subset=['reading_id'], keep='first')),
    'dropped_missing_reading_date': len(pd.read_csv(input_file)) - len(df.dropna(subset=['reading_date']),
    'dropped_missing_meter_id': len(pd.read_csv(input_file)) - len(df.dropna(subset=['meter_id']),
    'dropped_invalid_building_type': len(pd.read_csv(input_file)) - len(df.dropna(subset=['building_type']),
    'dropped_invalid_tariff': len(pd.read_csv(input_file)) - len(df.dropna(subset=['tariff']),
    'dropped_invalid_energy': len(pd.read_csv(input_file)) - len(df.dropna(subset=['energy_kwh']),
    'dropped_invalid_temperature': len(pd.read_csv(input_file)) - len(df.dropna(subset=['temperature_c'])
}

with open(os.path.join(os.environ["OUTPUT_DIR"], "cleaning_summary.json"), 'w') as f:
    json.dump(cleaning_summary, f)

output_filename = "cleaned.csv"
cleaning_logic = "The script reads the raw CSV, strips whitespace, treats specified values as missing, removes duplicates, parses dates, converts meter_id to upper case, maps building_type and tariff, converts energy to kWh, converts temperature to Celsius, selects and orders columns, and writes the cleaned CSV and cleaning summary."