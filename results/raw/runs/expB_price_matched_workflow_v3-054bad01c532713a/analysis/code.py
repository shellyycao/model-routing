import os
import json
import pandas as pd
import numpy as np

def main():
    # Define input and output paths
    input_dir = os.environ.get("INPUT_DIR", ".")
    output_dir = os.environ.get("OUTPUT_DIR", ".")
    
    input_file = os.path.join(input_dir, "cleaned.csv")
    output_file = os.path.join(output_dir, "findings.json")
    
    # Read the cleaned data
    # Dates are parsed automatically; types are inferred from the cleaning stage schema
    df = pd.read_csv(input_file, parse_dates=['reading_date'])
    
    # Initialize results dictionary
    results = {}
    
    # --- Q1: Overall Aggregation ---
    total_kwh = df['energy_kwh'].sum()
    reading_count = len(df)
    mean_kwh_per_reading = total_kwh / reading_count
    
    results['total_kwh'] = float(total_kwh)
    results['reading_count'] = float(reading_count)
    results['mean_kwh_per_reading'] = float(mean_kwh_per_reading)
    
    # --- Q2: Building Types ---
    building_totals = df.groupby('building_type')['energy_kwh'].sum()
    results['kwh_residential'] = float(building_totals.get('Residential', 0.0))
    results['kwh_commercial'] = float(building_totals.get('Commercial', 0.0))
    results['kwh_industrial'] = float(building_totals.get('Industrial', 0.0))
    
    # --- Q3: Quarterly Trend ---
    # Extract quarter from date (dates are 2024 per cleaning logic)
    df['quarter'] = df['reading_date'].dt.quarter
    quarterly_totals = df.groupby('quarter')['energy_kwh'].sum()
    results['kwh_q1'] = float(quarterly_totals.get(1, 0.0))
    results['kwh_q2'] = float(quarterly_totals.get(2, 0.0))
    results['kwh_q3'] = float(quarterly_totals.get(3, 0.0))
    results['kwh_q4'] = float(quarterly_totals.get(4, 0.0))
    
    # --- Q4: Half-year Change ---
    df['half'] = np.where(df['reading_date'].dt.month <= 6, 'H1', 'H2')
    half_totals = df.groupby('half')['energy_kwh'].sum()
    kwh_h1 = half_totals.get('H1', 0.0)
    kwh_h2 = half_totals.get('H2', 0.0)
    
    results['kwh_h1'] = float(kwh_h1)
    results['kwh_h2'] = float(kwh_h2)
    
    if kwh_h1 != 0:
        change_pct = (kwh_h2 - kwh_h1) / kwh_h1 * 100
    else:
        change_pct = 0.0  # Avoid division by zero; definition depends on context, 0 is safe default
    results['kwh_h2_vs_h1_change_pct'] = float(change_pct)
    
    # --- Q5: Hot-day Commercial Load ---
    # Filter: Commercial AND temperature_c >= 25 AND temperature_c is not NaN
    hot_commercial_df = df[
        (df['building_type'] == 'Commercial') & 
        (df['temperature_c'] >= 25) & 
        (df['temperature_c'].notna())
    ]
    results['hot_commercial_reading_count'] = float(len(hot_commercial_df))
    if len(hot_commercial_df) > 0:
        results['hot_commercial_mean_kwh'] = float(hot_commercial_df['energy_kwh'].mean())
    else:
        results['hot_commercial_mean_kwh'] = 0.0
    
    # --- Q6: Distribution Summary ---
    # Median and Sample Std of energy_kwh
    results['kwh_median'] = float(df['energy_kwh'].median())
    results['kwh_std'] = float(df['energy_kwh'].std(ddof=1))
    
    # Mean temperature (non-missing)
    valid_temp_df = df[df['temperature_c'].notna()]
    if len(valid_temp_df) > 0:
        results['temperature_mean'] = float(valid_temp_df['temperature_c'].mean())
    else:
        results['temperature_mean'] = 0.0
    
    # Missing temperature count
    results['temperature_missing_count'] = float(df['temperature_c'].isna().sum())
    
    # Pearson correlation for Commercial readings with non-missing temperature
    commercial_valid_temp_df = df[
        (df['building_type'] == 'Commercial') & 
        (df['temperature_c'].notna())
    ]
    if len(commercial_valid_temp_df) >= 2:
        # corr() returns a series/matrix, we extract the scalar
        corr_val = commercial_valid_temp_df['temperature_c'].corr(commercial_valid_temp_df['energy_kwh'], method='pearson')
        results['commercial_temp_kwh_corr'] = float(corr_val)
    else:
        results['commercial_temp_kwh_corr'] = 0.0
    
    # --- Q7: Tariff and Meter Usage ---
    tariff_totals = df.groupby('tariff')['energy_kwh'].sum()
    kwh_peak = tariff_totals.get('peak', 0.0)
    kwh_off_peak = tariff_totals.get('off-peak', 0.0)
    
    results['kwh_peak'] = float(kwh_peak)
    results['kwh_off_peak'] = float(kwh_off_peak)
    
    if total_kwh != 0:
        peak_share = kwh_peak / total_kwh * 100
    else:
        peak_share = 0.0
    results['peak_kwh_share_pct'] = float(peak_share)
    
    results['unique_meter_count'] = float(df['meter_id'].nunique())
    
    meter_totals = df.groupby('meter_id')['energy_kwh'].sum()
    if len(meter_totals) > 0:
        results['highest_use_meter_kwh'] = float(meter_totals.max())
    else:
        results['highest_use_meter_kwh'] = 0.0
    
    # Write results to JSON
    with open(output_file, 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    main()
