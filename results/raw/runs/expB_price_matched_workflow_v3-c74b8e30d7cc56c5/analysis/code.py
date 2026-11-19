import os
import json
import pandas as pd
import numpy as np

# Define paths
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Read cleaned data
df = pd.read_csv(input_path)

# Initialize results dictionary
results = {}

# --- q1: Overall aggregation ---
total_kwh = df['energy_kwh'].sum()
reading_count = len(df)
mean_kwh_per_reading = total_kwh / reading_count

results['total_kwh'] = total_kwh
results['reading_count'] = reading_count
results['mean_kwh_per_reading'] = mean_kwh_per_reading

# --- q2: Building types ---
building_totals = df.groupby('building_type')['energy_kwh'].sum()
results['kwh_residential'] = building_totals.get('Residential', 0.0)
results['kwh_commercial'] = building_totals.get('Commercial', 0.0)
results['kwh_industrial'] = building_totals.get('Industrial', 0.0)

# --- q3: Quarterly trend ---
df['reading_date'] = pd.to_datetime(df['reading_date'])
df['quarter'] = df['reading_date'].dt.quarter
quarterly_totals = df.groupby('quarter')['energy_kwh'].sum()
results['kwh_q1'] = quarterly_totals.get(1, 0.0)
results['kwh_q2'] = quarterly_totals.get(2, 0.0)
results['kwh_q3'] = quarterly_totals.get(3, 0.0)
results['kwh_q4'] = quarterly_totals.get(4, 0.0)

# --- q4: Half-year change ---
df['half_year'] = df['reading_date'].dt.month.map(lambda m: 1 if m <= 6 else 2)
half_year_totals = df.groupby('half_year')['energy_kwh'].sum()
kwh_h1 = half_year_totals.get(1, 0.0)
kwh_h2 = half_year_totals.get(2, 0.0)
results['kwh_h1'] = kwh_h1
results['kwh_h2'] = kwh_h2
if kwh_h1 != 0:
    results['kwh_h2_vs_h1_change_pct'] = (kwh_h2 - kwh_h1) / kwh_h1 * 100
else:
    results['kwh_h2_vs_h1_change_pct'] = 0.0

# --- q5: Hot-day commercial load ---
hot_commercial_df = df[
    (df['building_type'] == 'Commercial') & 
    (df['temperature_c'].notna()) & 
    (df['temperature_c'] >= 25)
]
results['hot_commercial_reading_count'] = len(hot_commercial_df)
if len(hot_commercial_df) > 0:
    results['hot_commercial_mean_kwh'] = hot_commercial_df['energy_kwh'].mean()
else:
    results['hot_commercial_mean_kwh'] = 0.0

# --- q6: Distribution summary ---
results['kwh_median'] = df['energy_kwh'].median()
results['kwh_std'] = df['energy_kwh'].std(ddof=1)

valid_temp_df = df[df['temperature_c'].notna()]
if len(valid_temp_df) > 0:
    results['temperature_mean'] = valid_temp_df['temperature_c'].mean()
else:
    results['temperature_mean'] = 0.0

results['temperature_missing_count'] = df['temperature_c'].isna().sum()

commercial_valid_temp_df = df[
    (df['building_type'] == 'Commercial') & 
    (df['temperature_c'].notna())
]
if len(commercial_valid_temp_df) >= 2:
    results['commercial_temp_kwh_corr'] = commercial_valid_temp_df['temperature_c'].corr(commercial_valid_temp_df['energy_kwh'])
else:
    results['commercial_temp_kwh_corr'] = 0.0

# --- q7: Tariff and meter usage ---
tariff_totals = df.groupby('tariff')['energy_kwh'].sum()
kwh_peak = tariff_totals.get('peak', 0.0)
kwh_off_peak = tariff_totals.get('off-peak', 0.0)
results['kwh_peak'] = kwh_peak
results['kwh_off_peak'] = kwh_off_peak

if total_kwh != 0:
    results['peak_kwh_share_pct'] = kwh_peak / total_kwh * 100
else:
    results['peak_kwh_share_pct'] = 0.0

results['unique_meter_count'] = df['meter_id'].nunique()
meter_totals = df.groupby('meter_id')['energy_kwh'].sum()
results['highest_use_meter_kwh'] = meter_totals.max()

# Write results to JSON
with open(output_path, 'w') as f:
    json.dump(results, f)
