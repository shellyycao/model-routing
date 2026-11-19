import os
import pandas as pd
import numpy as np
from datetime import datetime

# Define the input and output directories
input_dir = os.environ['INPUT_DIR']
output_dir = os.environ['OUTPUT_DIR']

# Read the raw data
raw_data = pd.read_csv(os.path.join(input_dir, 'raw.csv'), dtype=str)

# R1: Strip whitespace and treat specified values as missing
missing_values = ['', 'NA', 'N/A', 'null', 'None', '-']
raw_data.replace(missing_values, np.nan, inplace=True)
raw_data = raw_data.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# R2: Remove duplicate records based on reading_id
raw_data.drop_duplicates(subset='reading_id', keep='first', inplace=True)

# R3: Parse reading_date and drop rows with invalid dates
date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%Y/%m/%d', '%B %d, %Y']
raw_data['reading_date'] = pd.to_datetime(raw_data['reading_date'], errors='coerce', format=date_formats)
raw_data.dropna(subset=['reading_date'], inplace=True)
raw_data['reading_date'] = raw_data['reading_date'].dt.strftime('%Y-%m-%d')

# R4: Convert meter_id to upper case and drop rows with missing meter_id
raw_data['meter_id'] = raw_data['meter_id'].str.upper()
raw_data.dropna(subset=['meter_id'], inplace=True)

# R5: Map building_type to specified categories and drop invalid types
building_type_map = {'res': 'Residential','resi': 'Residential', 'commercial': 'Commercial', 'comm': 'Commercial', 'industrial': 'Industrial', 'ind': 'Industrial'}
raw_data['building_type'] = raw_data['building_type'].str.lower().map(building_type_map)
raw_data.dropna(subset=['building_type'], inplace=True)

# R6: Map tariff to specified categories and drop invalid tariffs
tariff_map = {'peak': 'peak', 'off-peak': 'off-peak', 'offpeak': 'off-peak', 'off peak': 'off-peak'}
raw_data['tariff'] = raw_data['tariff'].str.lower().map(tariff_map)
raw_data.dropna(subset=['tariff'], inplace=True)

# R7: Convert energy to kWh and drop invalid values
def convert_energy(energy):
    energy = energy.replace(',', '').strip()
    if energy.endswith('MWh'):
        return float(energy[:-3]) * 1000
    elif energy.endswith('kWh'):
        return float(energy[:-3])
    else:
        return float(energy)

raw_data['energy_kwh'] = raw_data['energy'].apply(convert_energy)
raw_data = raw_data[(raw_data['energy_kwh'] >= 0) & (raw_data['energy_kwh'] <= 100000)]
raw_data['energy_kwh'] = raw_data['energy_kwh'].round(2)

# R8: Convert temperature to Celsius and handle invalid values
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

raw_data['temperature_c'] = raw_data['temperature'].apply(convert_temperature)
raw_data.loc[(raw_data['temperature_c'] < -40) | (raw_data['temperature_c'] > 50), 'temperature_c'] = np.nan

# Select and order the required columns
cleaned_data = raw_data[['reading_id','reading_date','meter_id', 'building_type', 'tariff', 'energy_kwh', 'temperature_c']]
cleaned_data.sort_values(by='reading_id', inplace=True)

# Write the cleaned data to CSV
output_filename = 'cleaned.csv'
cleaned_data.to_csv(os.path.join(output_dir, output_filename), index=False)

# Create cleaning summary
cleaning_summary = {
    'raw_rows': len(raw_data),
    'cleaned_rows': len(cleaned_data),
    'dropped_duplicates': raw_data.shape[0] - cleaned_data.shape[0],
    'dropped_invalid_dates': len(raw_data) - len(cleaned_data),
    'dropped_missing_meter_id': len(raw_data) - len(cleaned_data),
    'dropped_invalid_building_type': len(raw_data) - len(cleaned_data),
    'dropped_invalid_tariff': len(raw_data) - len(cleaned_data),
    'dropped_invalid_energy': len(raw_data) - len(cleaned_data),
    'dropped_invalid_temperature': len(raw_data) - len(cleaned_data)
}

with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
    json.dump(cleaning_summary, f)

