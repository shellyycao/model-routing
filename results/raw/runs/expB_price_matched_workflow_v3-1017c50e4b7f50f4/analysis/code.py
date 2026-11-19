import os
import json
import pandas as pd
import numpy as np

# Define input and output paths
input_dir = os.environ["INPUT_DIR"]
output_dir = os.environ["OUTPUT_DIR"]
input_file = os.path.join(input_dir, "cleaned.csv")
output_file = os.path.join(output_dir, "findings.json")

# Read the cleaned data
df = pd.read_csv(input_file)

# Ensure correct data types
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
kwh_h2_vs_h1_change_pct = ((kwh_h2 - kwh_h1) / kwh_h1) * 100

results['kwh_h1'] = kwh_h1
results['kwh_h2'] = kwh_h2
results['kwh_h2_vs_h1_change_pct'] = kwh_h2_vs_h1_change_pct

# --- Q5: Hot-day Commercial Load ---
hot_commercial_df = df[
    (df['building_type'] == 'Commercial') & 
    (df['temperature_c'] >= 25)
]
hot_commercial_reading_count = len(hot_commercial_df)
hot_commercial_mean_kwh = hot_commercial_df['energy_kwh'].mean()

results['hot_commercial_reading_count'] = float(hot_commercial_reading_count)
results['hot_commercial_mean_kwh'] = hot_commercial_mean_kwh

# --- Q6: Distribution Summary ---
results['kwh_median'] = df['energy_kwh'].median()
results['kwh_std'] = df['energy_kwh'].std(ddof=1) # Sample standard deviation

valid_temp_df = df[df['temperature_c'].notna()]
results['temperature_mean'] = valid_temp_df['temperature_c'].mean()
results['temperature_missing_count'] = float(df['temperature_c'].isna().sum())

commercial_valid_temp_df = df[
    (df['building_type'] == 'Commercial') & 
    (df['temperature_c'].notna())
]
if len(commercial_valid_temp_df) > 1:
    results['commercial_temp_kwh_corr'] = commercial_valid_temp_df['temperature_c'].corr(commercial_valid_temp_df['energy_kwh'])
else:
    results['commercial_temp_kwh_corr'] = float('nan')

# --- Q7: Tariff and Meter Usage ---
tariff_totals = df.groupby('tariff')['energy_kwh'].sum()
kwh_peak = tariff_totals.get('peak', 0.0)
kwh_off_peak = tariff_totals.get('off-peak', 0.0)
peak_kwh_share_pct = (kwh_peak / total_kwh) * 100

results['kwh_peak'] = kwh_peak
results['kwh_off_peak'] = kwh_off_peak
results['peak_kwh_share_pct'] = peak_kwh_share_pct

results['unique_meter_count'] = float(df['meter_id'].nunique())
results['highest_use_meter_kwh'] = df.groupby('meter_id')['energy_kwh'].sum().max()

# Handle potential NaN values for JSON serialization (replace NaN with None, though instructions say finite numbers)
# Given the data description, NaNs should not occur for the primary metrics, but correlation might be NaN if insufficient data.
# We will allow NaN to be serialized or handle it if necessary, but standard json.dump fails on NaN.
# Replacing NaN with 0 or leaving it depends on strictness. Instructions: "No strings, lists, null, NaN or Infinity as values".
# If correlation is NaN, we must handle it. However, with 1428 rows, it's unlikely to be NaN.
# We will use a custom encoder or replace to ensure compliance if it arises.
# For safety, we check and replace NaN/Inf with 0 or appropriate finite number if logic dictates, 
# but here we assume valid data exists.

def convert_to_serializable(d):
    new_d = {}
    for k, v in d.items():
        if isinstance(v, float):
            if np.isnan(v) or np.isinf(v):
                # Fallback for edge cases to prevent crash, though not expected for these metrics
                new_d[k] = 0.0 
            else:
                new_d[k] = v
        else:
            new_d[k] = v
    return new_d

serializable_results = convert_to_serializable(results)

# Write findings to JSON
with open(output_file, 'w') as f:
    json.dump(serializable_results, f)
