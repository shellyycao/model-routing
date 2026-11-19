import os
import json
import pandas as pd
import numpy as np

def main():
    # Define paths
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    
    # Read cleaned data
    df = pd.read_csv(input_path)
    
    # Ensure correct data types
    df['reading_date'] = pd.to_datetime(df['reading_date'])
    df['energy_kwh'] = pd.to_numeric(df['energy_kwh'])
    df['temperature_c'] = pd.to_numeric(df['temperature_c'])
    
    # Initialize results dictionary
    results = {}
    
    # Q1: Overall aggregation
    results['total_kwh'] = df['energy_kwh'].sum()
    results['reading_count'] = len(df)
    results['mean_kwh_per_reading'] = results['total_kwh'] / results['reading_count']
    
    # Q2: Building types
    building_totals = df.groupby('building_type')['energy_kwh'].sum()
    results['kwh_residential'] = building_totals.get('Residential', 0.0)
    results['kwh_commercial'] = building_totals.get('Commercial', 0.0)
    results['kwh_industrial'] = building_totals.get('Industrial', 0.0)
    
    # Q3: Quarterly trend
    df['quarter'] = df['reading_date'].dt.quarter
    quarterly_totals = df.groupby('quarter')['energy_kwh'].sum()
    results['kwh_q1'] = quarterly_totals.get(1, 0.0)
    results['kwh_q2'] = quarterly_totals.get(2, 0.0)
    results['kwh_q3'] = quarterly_totals.get(3, 0.0)
    results['kwh_q4'] = quarterly_totals.get(4, 0.0)
    
    # Q4: Half-year change
    df['half_year'] = np.where(df['reading_date'].dt.month <= 6, 'H1', 'H2')
    half_year_totals = df.groupby('half_year')['energy_kwh'].sum()
    results['kwh_h1'] = half_year_totals.get('H1', 0.0)
    results['kwh_h2'] = half_year_totals.get('H2', 0.0)
    if results['kwh_h1'] != 0:
        results['kwh_h2_vs_h1_change_pct'] = (results['kwh_h2'] - results['kwh_h1']) / results['kwh_h1'] * 100
    else:
        results['kwh_h2_vs_h1_change_pct'] = 0.0
    
    # Q5: Hot-day commercial load
    hot_commercial_df = df[(df['building_type'] == 'Commercial') & (df['temperature_c'] >= 25)]
    results['hot_commercial_reading_count'] = len(hot_commercial_df)
    if results['hot_commercial_reading_count'] > 0:
        results['hot_commercial_mean_kwh'] = hot_commercial_df['energy_kwh'].mean()
    else:
        results['hot_commercial_mean_kwh'] = 0.0
    
    # Q6: Distribution summary
    results['kwh_median'] = df['energy_kwh'].median()
    results['kwh_std'] = df['energy_kwh'].std(ddof=1)
    
    temp_valid = df['temperature_c'].dropna()
    results['temperature_mean'] = temp_valid.mean()
    results['temperature_missing_count'] = df['temperature_c'].isna().sum()
    
    commercial_df = df[df['building_type'] == 'Commercial']
    commercial_valid_temp = commercial_df.dropna(subset=['temperature_c', 'energy_kwh'])
    if len(commercial_valid_temp) >= 2:
        results['commercial_temp_kwh_corr'] = commercial_valid_temp['temperature_c'].corr(commercial_valid_temp['energy_kwh'])
    else:
        results['commercial_temp_kwh_corr'] = 0.0
    
    # Q7: Tariff and meter usage
    tariff_totals = df.groupby('tariff')['energy_kwh'].sum()
    results['kwh_peak'] = tariff_totals.get('peak', 0.0)
    results['kwh_off_peak'] = tariff_totals.get('off-peak', 0.0)
    
    if results['total_kwh'] != 0:
        results['peak_kwh_share_pct'] = results['kwh_peak'] / results['total_kwh'] * 100
    else:
        results['peak_kwh_share_pct'] = 0.0
    
    results['unique_meter_count'] = df['meter_id'].nunique()
    meter_totals = df.groupby('meter_id')['energy_kwh'].sum()
    results['highest_use_meter_kwh'] = meter_totals.max()
    
    # Write results to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    main()
