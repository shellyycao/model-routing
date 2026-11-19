import os
import json
import pandas as pd
import numpy as np

# Define input and output paths
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Read the cleaned data
df = pd.read_csv(input_path)

# Ensure date is parsed correctly
df['reading_date'] = pd.to_datetime(df['reading_date'])

# Initialize results dictionary
results = {}

# --- Q1: Overall Aggregation ---
total_kwh = df['energy_kwh'].sum()
reading_count = len(df)
mean_kwh_per_reading = total_kwh / reading_count

results['total_kwh'] = total_kwh
results['reading_count'] = float(reading_count)
results['mean_kwh_per_reading'] = mean_kwh_per_reading

# --- Q2: Building Types ---
building_totals = df.groupby('building_type')['energy_kwh'].sum()
results['kwh_residential'] = building_totals.get('Residential', 0.0)
results['kwh_commercial'] = building_totals.get('Commercial', 0.0)
results['kwh_industrial'] = building_totals.get('Industrial', 0.0)

# --- Q3: Quarterly Trend ---
df['quarter'] = df['reading_date'].dt.quarter
quarterly_totals = df.groupby('quarter')['energy_kwh'].sum()
results['kwh_q1'] = quarterly_totals.get(1, 0.0)
results['kwh_q2'] = quarterly_totals.get(2, 0.0)
results['kwh_q3'] = quarterly_totals.get(3, 0.0)
results['kwh_q4'] = quarterly_totals.get(4, 0.0)

# --- Q4: Half-year Change ---
kwh_h1 = df[df['reading_date'].dt.month <= 6]['energy_kwh'].sum()
kwh_h2 = df[df['reading_date'].dt.month >= 7]['energy_kwh'].sum()
results['kwh_h1'] = kwh_h1
results['kwh_h2'] = kwh_h2
if kwh_h1 != 0:
    results['kwh_h2_vs_h1_change_pct'] = ((kwh_h2 - kwh_h1) / kwh_h1) * 100
else:
    results['kwh_h2_vs_h1_change_pct'] = 0.0

# --- Q5: Hot-day Commercial Load ---
hot_commercial_df = df[
    (df['building_type'] == 'Commercial') & 
    (df['temperature_c'].notna()) & 
    (df['temperature_c'] >= 25)
]
results['hot_commercial_reading_count'] = float(len(hot_commercial_df))
if len(hot_commercial_df) > 0:
    results['hot_commercial_mean_kwh'] = hot_commercial_df['energy_kwh'].mean()
else:
    results['hot_commercial_mean_kwh'] = 0.0

# --- Q6: Distribution Summary ---
results['kwh_median'] = df['energy_kwh'].median()
results['kwh_std'] = df['energy_kwh'].std(ddof=1)

valid_temp_df = df[df['temperature_c'].notna()]
if len(valid_temp_df) > 0:
    results['temperature_mean'] = valid_temp_df['temperature_c'].mean()
else:
    results['temperature_mean'] = 0.0

results['temperature_missing_count'] = float(df['temperature_c'].isna().sum())

commercial_temp_df = df[
    (df['building_type'] == 'Commercial') & 
    (df['temperature_c'].notna())
]
if len(commercial_temp_df) >= 2:
    # Pearson correlation requires at least 2 data points
    results['commercial_temp_kwh_corr'] = commercial_temp_df['temperature_c'].corr(commercial_temp_df['energy_kwh'])
else:
    results['commercial_temp_kwh_corr'] = 0.0

# --- Q7: Tariff and Meter Usage ---
tariff_totals = df.groupby('tariff')['energy_kwh'].sum()
results['kwh_peak'] = tariff_totals.get('peak', 0.0)
results['kwh_off_peak'] = tariff_totals.get('off-peak', 0.0)

if total_kwh != 0:
    results['peak_kwh_share_pct'] = (results['kwh_peak'] / total_kwh) * 100
else:
    results['peak_kwh_share_pct'] = 0.0

results['unique_meter_count'] = float(df['meter_id'].nunique())
results['highest_use_meter_kwh'] = df.groupby('meter_id')['energy_kwh'].sum().max()

# Write results to JSON
with open(output_path, 'w') as f:
    json.dump(results, f)
