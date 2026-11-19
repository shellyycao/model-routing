import os
import pandas as pd
import numpy as np

# Read the cleaned data
input_file = os.path.join(os.environ['INPUT_DIR'], 'cleaned.csv')
df = pd.read_csv(input_file, parse_dates=['reading_date'], dayfirst=True)

# Analysis
total_kwh = df['energy_kwh'].sum()
reading_count = len(df)
mean_kwh_per_reading = total_kwh / reading_count

kwh_residential = df[df['building_type'] == 'Residential']['energy_kwh'].sum()
kwh_commercial = df[df['building_type'] == 'Commercial']['energy_kwh'].sum()
kwh_industrial = df[df['building_type'] == 'Industrial']['energy_kwh'].sum()

kwh_q1 = df[df['reading_date'].dt.quarter == 1]['energy_kwh'].sum()
kwh_q2 = df[df['reading_date'].dt.quarter == 2]['energy_kwh'].sum()
kwh_q3 = df[df['reading_date'].dt.quarter == 3]['energy_kwh'].sum()
kwh_q4 = df[df['reading_date'].dt.quarter == 4]['energy_kwh'].sum()

kwh_h1 = df[df['reading_date'].dt.month.isin(range(1, 7))]['energy_kwh'].sum()
kwh_h2 = df[df['reading_date'].dt.month.isin(range(7, 13))]['energy_kwh'].sum()
kwh_h2_vs_h1_change_pct = ((kwh_h2 - kwh_h1) / kwh_h1) * 100 if kwh_h1!= 0 else 0

hot_commercial_readings = df[(df['building_type'] == 'Commercial') & (df['temperature_c'].notna()) & (df['temperature_c'] >= 25)]
hot_commercial_reading_count = len(hot_commercial_readings)
hot_commercial_mean_kwh = hot_commercial_readings['energy_kwh'].mean() if not hot_commercial_readings.empty else 0

kwh_median = df['energy_kwh'].median()
kwh_std = df['energy_kwh'].std()
temperature_mean = df[df['temperature_c'].notna()]['temperature_c'].mean()
temperature_missing_count = df['temperature_c'].isna().sum()
commercial_temp_kwh_corr = df[(df['building_type'] == 'Commercial') & (df['temperature_c'].notna())][['temperature_c', 'energy_kwh']].corr().iloc[0, 1]

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

# Expected artifacts
expected_artifacts = ['findings.json']

# Methods description
methods_description = 'This script performs a comprehensive analysis of energy consumption data, calculating various metrics such as total and per-building-type usage, quarterly trends, half-year changes, hot-day commercial load, and distribution summaries. It also examines tariff and meter usage, providing insights into energy consumption patterns and correlations with temperature.'
