import os
import pandas as pd
import numpy as np

# Read the cleaned data
input_dir = os.environ['INPUT_DIR']
output_dir = os.environ['OUTPUT_DIR']
cleaned_data_path = os.path.join(input_dir, 'cleaned.csv')
df = pd.read_csv(cleaned_data_path, parse_dates=['reading_date'])

# Analysis
total_kwh = df['energy_kwh'].sum()
reading_count = len(df)
mean_kwh_per_reading = total_kwh / reading_count

kwh_residential = df[df['building_type'] == 'Residential']['energy_kwh'].sum()
kwh_commercial = df[df['building_type'] == 'Commercial']['energy_kwh'].sum()
kwh_industrial = df[df['building_type'] == 'Industrial']['energy_kwh'].sum()

df['quarter'] = df['reading_date'].dt.to_period('Q')
kwh_q1 = df[df['quarter'] == '2024Q1']['energy_kwh'].sum()
kwh_q2 = df[df['quarter'] == '2024Q2']['energy_kwh'].sum()
kwh_q3 = df[df['quarter'] == '2024Q3']['energy_kwh'].sum()
kwh_q4 = df[df['quarter'] == '2024Q4']['energy_kwh'].sum()

df['half'] = df['reading_date'].dt.to_period('H')
kwh_h1 = df[df['half'] == '2024H1']['energy_kwh'].sum()
kwh_h2 = df[df['half'] == '2024H2']['energy_kwh'].sum()
kwh_h2_vs_h1_change_pct = ((kwh_h2 - kwh_h1) / kwh_h1) * 100 if kwh_h1!= 0 else 0

hot_commercial_df = df[(df['building_type'] == 'Commercial') & (df['temperature_c'].notna()) & (df['temperature_c'] >= 25)]
hot_commercial_reading_count = len(hot_commercial_df)
hot_commercial_mean_kwh = hot_commercial_df['energy_kwh'].mean()

kwh_median = df['energy_kwh'].median()
kwh_std = df['energy_kwh'].std()
temperature_mean = df[df['temperature_c'].notna()]['temperature_c'].mean()
temperature_missing_count = df['temperature_c'].isna().sum()
commercial_temp_kwh_corr = df[(df['building_type'] == 'Commercial') & (df['temperature_c'].notna())][['temperature_c', 'energy_kwh']].corr().iloc[0, 1]

kwh_peak = df[df['tariff'] == 'peak']['energy_kwh'].sum()
kwh_off_peak = df[df['tariff'] == 'off-peak']['energy_kwh'].sum()
peak_kwh_share_pct = (kwh_peak / total_kwh) * 100
unique_meter_count = df['meter_id'].nunique()
highest_use_meter_kwh = df.groupby('meter_id')['energy_kwh'].sum().max()

# Prepare findings
findings = {
    'total_kwh': total_kwh,
   'reading_count': reading_count,
    'mean_kwh_per_reading': mean_kwh_per_reading,
    'kwh_residential': kwh_residential,
    'kwh_commercial': kwh_commercial,
    'kwh_industrial': kwh_industrial,
    'kwh_q1': kwh_q1,
    'kwh_q2': kwh_q2,
    'kwh_q3': kwh_q3,
    'kwh_q4': kwh_q4,
    'kwh_h1': kwh_h1,
    'kwh_h2': kwh_h2,
    'kwh_h2_vs_h1_change_pct': kwh_h2_vs_h1_change_pct,
    'hot_commercial_reading_count': hot_commercial_reading_count,
    'hot_commercial_mean_kwh': hot_commercial_mean_kwh,
    'kwh_median': kwh_median,
    'kwh_std': kwh_std,
    'temperature_mean': temperature_mean,
    'temperature_missing_count': temperature_missing_count,
    'commercial_temp_kwh_corr': commercial_temp_kwh_corr,
    'kwh_peak': kwh_peak,
    'kwh_off_peak': kwh_off_peak,
    'peak_kwh_share_pct': peak_kwh_share_pct,
    'unique_meter_count': unique_meter_count,
    'highest_use_meter_kwh': highest_use_meter_kwh
}

# Write findings to JSON
findings_path = os.path.join(output_dir, 'findings.json')
with open(findings_path, 'w') as f:
    json.dump(findings, f)

