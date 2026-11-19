import os
import json
import pandas as pd
import numpy as np

# Define paths
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Read cleaned data
df = pd.read_csv(input_path)

# Ensure date column is parsed correctly
df['reading_date'] = pd.to_datetime(df['reading_date'])

# Initialize results dictionary
results = {}

# q1: Overall aggregation
total_kwh = df['energy_kwh'].sum()
reading_count = len(df)
mean_kwh_per_reading = total_kwh / reading_count

results['total_kwh'] = total_kwh
results['reading_count'] = reading_count
results['mean_kwh_per_reading'] = mean_kwh_per_reading

# q2: Building types
grouped_building = df.groupby('building_type')['energy_kwh'].sum()
results['kwh_residential'] = grouped_building.get('Residential', 0.0)
results['kwh_commercial'] = grouped_building.get('Commercial', 0.0)
results['kwh_industrial'] = grouped_building.get('Industrial', 0.0)

# q3: Quarterly trend
df['quarter'] = df['reading_date'].dt.quarter
grouped_quarter = df.groupby('quarter')['energy_kwh'].sum()
results['kwh_q1'] = grouped_quarter.get(1, 0.0)
results['kwh_q2'] = grouped_quarter.get(2, 0.0)
results['kwh_q3'] = grouped_quarter.get(3, 0.0)
results['kwh_q4'] = grouped_quarter.get(4, 0.0)

# q4: Half-year change
df['half_year'] = np.where(df['reading_date'].dt.month <= 6, 'H1', 'H2')
grouped_half = df.groupby('half_year')['energy_kwh'].sum()
kwh_h1 = grouped_half.get('H1', 0.0)
kwh_h2 = grouped_half.get('H2', 0.0)
results['kwh_h1'] = kwh_h1
results['kwh_h2'] = kwh_h2
if kwh_h1 != 0:
    results['kwh_h2_vs_h1_change_pct'] = (kwh_h2 - kwh_h1) / kwh_h1 * 100
else:
    results['kwh_h2_vs_h1_change_pct'] = 0.0

# q5: Hot-day commercial load
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

# q6: Distribution summary
results['kwh_median'] = df['energy_kwh'].median()
results['kwh_std'] = df['energy_kwh'].std(ddof=1)

valid_temp_df = df[df['temperature_c'].notna()]
if len(valid_temp_df) > 0:
    results['temperature_mean'] = valid_temp_df['temperature_c'].mean()
else:
    results['temperature_mean'] = 0.0

results['temperature_missing_count'] = df['temperature_c'].isna().sum()

commercial_temp_df = df[
    (df['building_type'] == 'Commercial') & 
    (df['temperature_c'].notna())
]
if len(commercial_temp_df) >= 2:
    results['commercial_temp_kwh_corr'] = commercial_temp_df['temperature_c'].corr(commercial_temp_df['energy_kwh'])
else:
    results['commercial_temp_kwh_corr'] = 0.0

# q7: Tariff and meter usage
grouped_tariff = df.groupby('tariff')['energy_kwh'].sum()
kwh_peak = grouped_tariff.get('peak', 0.0)
kwh_off_peak = grouped_tariff.get('off-peak', 0.0)
results['kwh_peak'] = kwh_peak
results['kwh_off_peak'] = kwh_off_peak

if total_kwh != 0:
    results['peak_kwh_share_pct'] = kwh_peak / total_kwh * 100
else:
    results['peak_kwh_share_pct'] = 0.0

results['unique_meter_count'] = df['meter_id'].nunique()
results['highest_use_meter_kwh'] = df.groupby('meter_id')['energy_kwh'].sum().max()

# Write results to JSON
with open(output_path, 'w') as f:
    json.dump(results, f)
