import os
import json
import pandas as pd
import numpy as np

# Define paths
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Read cleaned data
df = pd.read_csv(input_path)

# Ensure correct dtypes
df['reading_date'] = pd.to_datetime(df['reading_date'])
df['energy_kwh'] = df['energy_kwh'].astype(float)

# Initialize results dictionary
results = {}

# --- q1: Overall ---
total_kwh = df['energy_kwh'].sum()
reading_count = len(df)
mean_kwh_per_reading = total_kwh / reading_count

results['total_kwh'] = total_kwh
results['reading_count'] = float(reading_count)
results['mean_kwh_per_reading'] = mean_kwh_per_reading

# --- q2: Building types ---
building_totals = df.groupby('building_type')['energy_kwh'].sum()
results['kwh_residential'] = building_totals.get('Residential', 0.0)
results['kwh_commercial'] = building_totals.get('Commercial', 0.0)
results['kwh_industrial'] = building_totals.get('Industrial', 0.0)

# --- q3: Quarterly trend ---
df['quarter'] = df['reading_date'].dt.quarter
quarterly_totals = df.groupby('quarter')['energy_kwh'].sum()
results['kwh_q1'] = quarterly_totals.get(1, 0.0)
results['kwh_q2'] = quarterly_totals.get(2, 0.0)
results['kwh_q3'] = quarterly_totals.get(3, 0.0)
results['kwh_q4'] = quarterly_totals.get(4, 0.0)

# --- q4: Half-year change ---
kwh_h1 = df[df['reading_date'].dt.month <= 6]['energy_kwh'].sum()
kwh_h2 = df[df['reading_date'].dt.month >= 7]['energy_kwh'].sum()
results['kwh_h1'] = kwh_h1
results['kwh_h2'] = kwh_h2
results['kwh_h2_vs_h1_change_pct'] = ((kwh_h2 - kwh_h1) / kwh_h1) * 100

# --- q5: Hot-day commercial load ---
hot_commercial_df = df[(df['building_type'] == 'Commercial') & (df['temperature_c'] >= 25)]
results['hot_commercial_reading_count'] = float(len(hot_commercial_df))
results['hot_commercial_mean_kwh'] = hot_commercial_df['energy_kwh'].mean()

# --- q6: Distribution summary ---
results['kwh_median'] = df['energy_kwh'].median()
results['kwh_std'] = df['energy_kwh'].std(ddof=1)

valid_temp_df = df[df['temperature_c'].notna()]
results['temperature_mean'] = valid_temp_df['temperature_c'].mean()
results['temperature_missing_count'] = float(df['temperature_c'].isna().sum())

commercial_temp_df = df[(df['building_type'] == 'Commercial') & (df['temperature_c'].notna())]
if len(commercial_temp_df) > 1:
    results['commercial_temp_kwh_corr'] = commercial_temp_df['temperature_c'].corr(commercial_temp_df['energy_kwh'])
else:
    results['commercial_temp_kwh_corr'] = float('nan')

# --- q7: Tariff and meter usage ---
tariff_totals = df.groupby('tariff')['energy_kwh'].sum()
kwh_peak = tariff_totals.get('peak', 0.0)
kwh_off_peak = tariff_totals.get('off-peak', 0.0)
results['kwh_peak'] = kwh_peak
results['kwh_off_peak'] = kwh_off_peak
results['peak_kwh_share_pct'] = (kwh_peak / total_kwh) * 100

results['unique_meter_count'] = float(df['meter_id'].nunique())
results['highest_use_meter_kwh'] = df.groupby('meter_id')['energy_kwh'].sum().max()

# Write results to JSON
with open(output_path, 'w') as f:
    json.dump(results, f)
