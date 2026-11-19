import os
import json
import pandas as pd
import numpy as np

def run_analysis():
    # Define paths
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    
    # Read cleaned data
    # Schema: reading_id, reading_date, meter_id, building_type, tariff, energy_kwh, temperature_c
    df = pd.read_csv(input_path)
    
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
    # Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
    df['quarter'] = df['reading_date'].dt.quarter
    quarterly_totals = df.groupby('quarter')['energy_kwh'].sum()
    results['kwh_q1'] = quarterly_totals.get(1, 0.0)
    results['kwh_q2'] = quarterly_totals.get(2, 0.0)
    results['kwh_q3'] = quarterly_totals.get(3, 0.0)
    results['kwh_q4'] = quarterly_totals.get(4, 0.0)
    
    # --- Q4: Half-year Change ---
    # H1: Jan-Jun, H2: Jul-Dec
    h1_mask = df['reading_date'].dt.month <= 6
    kwh_h1 = df.loc[h1_mask, 'energy_kwh'].sum()
    kwh_h2 = df.loc[~h1_mask, 'energy_kwh'].sum()
    
    # Percentage change: (H2 - H1) / H1 * 100
    kwh_h2_vs_h1_change_pct = ((kwh_h2 - kwh_h1) / kwh_h1) * 100
    
    results['kwh_h1'] = kwh_h1
    results['kwh_h2'] = kwh_h2
    results['kwh_h2_vs_h1_change_pct'] = kwh_h2_vs_h1_change_pct
    
    # --- Q5: Hot-day Commercial Load ---
    # Commercial readings with temperature_c >= 25 (non-missing)
    hot_commercial_df = df[
        (df['building_type'] == 'Commercial') & 
        (df['temperature_c'].notna()) & 
        (df['temperature_c'] >= 25)
    ]
    hot_commercial_reading_count = len(hot_commercial_df)
    hot_commercial_mean_kwh = hot_commercial_df['energy_kwh'].mean()
    
    results['hot_commercial_reading_count'] = hot_commercial_reading_count
    results['hot_commercial_mean_kwh'] = hot_commercial_mean_kwh
    
    # --- Q6: Distribution Summary ---
    # Median and Sample Std of energy_kwh
    results['kwh_median'] = df['energy_kwh'].median()
    results['kwh_std'] = df['energy_kwh'].std(ddof=1) # sample std
    
    # Mean temperature (non-missing)
    valid_temp_df = df[df['temperature_c'].notna()]
    results['temperature_mean'] = valid_temp_df['temperature_c'].mean()
    
    # Missing temperature count
    results['temperature_missing_count'] = df['temperature_c'].isna().sum()
    
    # Pearson correlation for Commercial readings with non-missing temperature
    commercial_valid_temp = df[
        (df['building_type'] == 'Commercial') & 
        (df['temperature_c'].notna())
    ]
    # corr() returns a series, we extract the specific value
    # It handles cases with 0 variance gracefully (returns NaN), but we assume valid data exists
    if len(commercial_valid_temp) > 1:
        corr_matrix = commercial_valid_temp[['temperature_c', 'energy_kwh']].corr(method='pearson')
        results['commercial_temp_kwh_corr'] = corr_matrix.loc['temperature_c', 'energy_kwh']
    else:
        results['commercial_temp_kwh_corr'] = np.nan # Should not happen based on data size
    
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
    
    # --- Output ---
    # Convert numpy types to native python types for JSON serialization
    # round-trip through json.dumps/loads handles numpy floats/ints automatically
    # but explicit casting is safer for NaNs if they existed (though prompt says no NaNs in output)
    # We rely on default json encoder behavior for numpy types in recent pandas/numpy versions or simple float() cast
    # However, json.dumps does not handle numpy types natively in older python versions.
    # We convert explicitly.
    
    clean_results = {}
    for k, v in results.items():
        if isinstance(v, (np.floating, float)):
            # Check for NaN/Inf just in case, though prompt forbids it
            if np.isfinite(v):
                clean_results[k] = float(v)
            else:
                # Fallback if logic produces NaN (should not happen per prompt)
                clean_results[k] = 0.0 
        elif isinstance(v, (np.integer, int)):
            clean_results[k] = int(v)
        else:
            clean_results[k] = v
            
    with open(output_path, 'w') as f:
        json.dump(clean_results, f)

if __name__ == "__main__":
    run_analysis()
