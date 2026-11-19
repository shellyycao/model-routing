import os
import json
import pandas as pd
import numpy as np

# Define input and output paths
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Read the cleaned data
# As per schema: reading_date is a date string (YYYY-MM-DD), others are strings or categories
# Pandas infers types, but we ensure reading_date is parsed
df = pd.read_csv(input_path, parse_dates=['reading_date'])

# Initialize results dictionary
results = {}

# --- Q1: Overall Aggregation ---
results['total_kwh'] = df['energy_kwh'].sum()
results['reading_count'] = len(df)
results['mean_kwh_per_reading'] = df['energy_kwh'].mean()

# --- Q2: Building Types ---
building_groups = df.groupby('building_type')['energy_kwh'].sum()
results['kwh_residential'] = building_groups.get('Residential', 0.0)
results['kwh_commercial'] = building_groups.get('Commercial', 0.0)
results['kwh_industrial'] = building_groups.get('Industrial', 0.0)

# --- Q3: Quarterly Trend ---
# Extract quarter from date
df['quarter'] = df['reading_date'].dt.quarter
quarter_groups = df.groupby('quarter')['energy_kwh'].sum()
results['kwh_q1'] = quarter_groups.get(1, 0.0)
results['kwh_q2'] = quarter_groups.get(2, 0.0)
results['kwh_q3'] = quarter_groups.get(3, 0.0)
results['kwh_q4'] = quarter_groups.get(4, 0.0)

# --- Q4: Half-year Change ---
# H1: Jan-Jun (Months 1-6), H2: Jul-Dec (Months 7-12)
df['month'] = df['reading_date'].dt.month
kwh_h1 = df[df['month'] <= 6]['energy_kwh'].sum()
kwh_h2 = df[df['month'] > 6]['energy_kwh'].sum()
results['kwh_h1'] = kwh_h1
results['kwh_h2'] = kwh_h2
if kwh_h1 != 0:
    results['kwh_h2_vs_h1_change_pct'] = ((kwh_h2 - kwh_h1) / kwh_h1) * 100
else:
    results['kwh_h2_vs_h1_change_pct'] = 0.0 # Or handle as appropriate, assuming non-zero based on data

# --- Q5: Hot-day Commercial Load ---
# Filter: building_type == 'Commercial' AND temperature_c >= 25 (non-missing handled by comparison)
hot_commercial_df = df[(df['building_type'] == 'Commercial') & (df['temperature_c'] >= 25)]
results['hot_commercial_reading_count'] = len(hot_commercial_df)
if len(hot_commercial_df) > 0:
    results['hot_commercial_mean_kwh'] = hot_commercial_df['energy_kwh'].mean()
else:
    results['hot_commercial_mean_kwh'] = 0.0

# --- Q6: Distribution Summary ---
results['kwh_median'] = df['energy_kwh'].median()
results['kwh_std'] = df['energy_kwh'].std(ddof=1) # Sample standard deviation

# Temperature mean over non-missing
temp_valid = df['temperature_c'].dropna()
results['temperature_mean'] = temp_valid.mean()

# Count missing temperature
results['temperature_missing_count'] = df['temperature_c'].isna().sum()

# Correlation for Commercial readings with non-missing temperature
commercial_valid_temp = df[(df['building_type'] == 'Commercial') & (df['temperature_c'].notna())]
if len(commercial_valid_temp) > 1:
    # Pearson correlation
    results['commercial_temp_kwh_corr'] = commercial_valid_temp['temperature_c'].corr(commercial_valid_temp['energy_kwh'])
else:
    results['commercial_temp_kwh_corr'] = 0.0

# --- Q7: Tariff and Meter Usage ---
tariff_groups = df.groupby('tariff')['energy_kwh'].sum()
kwh_peak = tariff_groups.get('peak', 0.0)
kwh_off_peak = tariff_groups.get('off-peak', 0.0)
results['kwh_peak'] = kwh_peak
results['kwh_off_peak'] = kwh_off_peak

if results['total_kwh'] != 0:
    results['peak_kwh_share_pct'] = (kwh_peak / results['total_kwh']) * 100
else:
    results['peak_kwh_share_pct'] = 0.0

results['unique_meter_count'] = df['meter_id'].nunique()

meter_groups = df.groupby('meter_id')['energy_kwh'].sum()
results['highest_use_meter_kwh'] = meter_groups.max()

# Write results to JSON
with open(output_path, 'w') as f:
    json.dump(results, f)
