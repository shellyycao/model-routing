import os
import pandas as pd
import numpy as np

# Read the cleaned data
input_file = os.path.join(os.environ['INPUT_DIR'], 'cleaned.csv')
df = pd.read_csv(input_file)

# Analysis
total_kwh = df['energy_kwh'].sum()
reading_count = len(df)
mean_kwh_per_reading = total_kwh / reading_count

kwh_residential = df[df['building_type'] == 'Residential']['energy_kwh'].sum()
kwh_commercial = df[df['building_type'] == 'Commercial']['energy_kwh'].sum()
kwh_industrial = df[df['building_type'] == 'Industrial']['energy_kwh'].sum()

df['quarter'] = df['reading_date'].apply(lambda x: (pd.to_datetime(x).month - 1) // 3 + 1)
kwh_q1 = df[df['quarter'] == 1]['energy_kwh'].sum()
kwh_q2 = df[df['quarter'] == 2]['energy_kwh'].sum()
kwh_q3 = df[df['quarter'] == 3]['energy_kwh'].sum()
kwh_q4 = df[df['quarter'] == 4]['energy_kwh'].sum()

h1_mask = df['reading_date'].between('2024-01-01', '2024-06-30')
h2_mask = df['reading_date'].between('2024-07-01', '2024-12-31')
kwh_h1 = df[h1_mask]['energy_kwh'].sum()
kwh_h2 = df[h2_mask]['energy_kwh'].sum()
kwh_h2_vs_h1_change_pct = ((kwh_h2 - kwh_h1) / kwh_h1) * 100 if kwh_h1!= 0 else 0

hot_commercial_mask = (df['building_type'] == 'Commercial') & (df['temperature_c'].notna()) & (df['temperature_c'] >= 25)
hot_commercial_reading_count = df[hot_commercial_mask].shape[0]
hot_commercial_mean_kwh = df[hot_commercial_mask]['energy_kwh'].mean()

kwh_median = df['energy_kwh'].median()
kwh_std = df['energy_kwh'].std()
temperature_mean = df['temperature_c'].mean()
temperature_missing_count = df['temperature_c'].isna().sum()
commercial_temp_kwh_corr = df.loc[(df['building_type'] == 'Commercial') & df['temperature_c'].notna(), ['temperature_c', 'energy_kwh']].corr().iloc[0, 1]

kwh_peak = df[df['tariff'] == 'peak']['energy_kwh'].sum()
kwh_off_peak = df[df['tariff'] == 'off-peak']['energy_kwh'].sum()
peak_kwh_share_pct = (kwh_peak / total_kwh) * 100 if total_kwh!= 0 else 0
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
output_file = os.path.join(os.environ['OUTPUT_DIR'], 'findings.json')
with open(output_file, 'w') as f:
    import json
    json.dump(findings, f)
