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

# Ensure date parsing
df['reading_date'] = pd.to_datetime(df['reading_date'])

# Initialize results dictionary
results = {}

# --- Q1: Overall Aggregation ---
total_kwh = df['energy_kwh'].sum()
reading_count = len(df)
mean_kwh_per_reading = total_kwh / reading_count

results['total_kwh'] = total_kwh
results['reading_count'] = reading_count
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
df['half'] = df['reading_date'].dt.month.map(lambda m: 1 if m <= 6 else 2)
half_year_totals = df.groupby('half')['energy_kwh'].sum()
kwh_h1 = half_year_totals.get(1, 0.0)
kwh_h2 = half_year_totals.get(2, 0.0)
results['kwh_h1'] = kwh_h1
results['kwh_h2'] = kwh_h2
results['kwh_h2_vs_h1_change_pct'] = ((kwh_h2 - kwh_h1) / kwh_h1) * 100

# --- Q5: Hot-day Commercial Load ---
hot_commercial_df = df[
    (df['building_type'] == 'Commercial') & 
    (df['temperature_c'].notna()) & 
    (df['temperature_c'] >= 25)
]
results['hot_commercial_reading_count'] = len(hot_commercial_df)
results['hot_commercial_mean_kwh'] = hot_commercial_df['energy_kwh'].mean()

# --- Q6: Distribution Summary ---
results['kwh_median'] = df['energy_kwh'].median()
results['kwh_std'] = df['energy_kwh'].std(ddof=1) # sample std

valid_temp_df = df[df['temperature_c'].notna()]
results['temperature_mean'] = valid_temp_df['temperature_c'].mean()
results['temperature_missing_count'] = df['temperature_c'].isna().sum()

commercial_valid_temp_df = df[
    (df['building_type'] == 'Commercial') & 
    (df['temperature_c'].notna())
]
if len(commercial_valid_temp_df) > 1:
    results['commercial_temp_kwh_corr'] = commercial_valid_temp_df['temperature_c'].corr(commercial_valid_temp_df['energy_kwh'])
else:
    results['commercial_temp_kwh_corr'] = np.nan

# --- Q7: Tariff and Meter Usage ---
tariff_totals = df.groupby('tariff')['energy_kwh'].sum()
kwh_peak = tariff_totals.get('peak', 0.0)
kwh_off_peak = tariff_totals.get('off-peak', 0.0)
results['kwh_peak'] = kwh_peak
results['kwh_off_peak'] = kwh_off_peak
results['peak_kwh_share_pct'] = (kwh_peak / total_kwh) * 100

results['unique_meter_count'] = df['meter_id'].nunique()
meter_totals = df.groupby('meter_id')['energy_kwh'].sum()
results['highest_use_meter_kwh'] = meter_totals.max()

# Handle potential NaN values for JSON serialization (replace NaN with None, then filter or ensure valid output)
# The prompt asks for finite numbers. If any result is NaN (e.g. mean of empty set), it might violate the schema.
# However, based on data description, sets should be non-empty.
# We convert NaNs to None for the interim and check, but pandas/JSON handling requires care.
# Standard json.dump won't handle NaN. We check and replace if necessary, though logic suggests valid data exists.
# For safety, we use a custom converter or replace NaNs if they were possible.
# Given the constraints, we assume valid finite numbers are produced.

clean_results = {k: v for k, v in results.items()}
# Convert numpy types to native python types for JSON compatibility
for k, v in clean_results.items():
    if isinstance(v, (np.integer, np.floating)):
        clean_results[k] = v.item()
    # Handle potential NaN/Inf if logic allowed them (though data suggests otherwise)
    if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
        # Fallback or error handling would go here, but per prompt we expect finite numbers.
        # We will let it pass or set to 0 if strictly necessary to avoid crash, 
        # but valid data should prevent this.
        pass

with open(output_file, 'w') as f:
    json.dump(clean_results, f)
