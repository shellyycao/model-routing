import os
import json
import pandas as pd
import numpy as np

def run_analysis():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    
    # Read cleaned data
    # Dates are ISO format YYYY-MM-DD from cleaning stage
    df = pd.read_csv(input_path, parse_dates=['reading_date'])
    
    findings = {}
    
    # --- Q1: Overall ---
    total_kwh = df['energy_kwh'].sum()
    reading_count = len(df)
    mean_kwh_per_reading = total_kwh / reading_count
    
    findings['total_kwh'] = total_kwh
    findings['reading_count'] = reading_count
    findings['mean_kwh_per_reading'] = mean_kwh_per_reading
    
    # --- Q2: Building types ---
    building_totals = df.groupby('building_type')['energy_kwh'].sum()
    findings['kwh_residential'] = building_totals.get('Residential', 0.0)
    findings['kwh_commercial'] = building_totals.get('Commercial', 0.0)
    findings['kwh_industrial'] = building_totals.get('Industrial', 0.0)
    
    # --- Q3: Quarterly trend ---
    # Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
    df['quarter'] = df['reading_date'].dt.quarter
    quarterly_totals = df.groupby('quarter')['energy_kwh'].sum()
    findings['kwh_q1'] = quarterly_totals.get(1, 0.0)
    findings['kwh_q2'] = quarterly_totals.get(2, 0.0)
    findings['kwh_q3'] = quarterly_totals.get(3, 0.0)
    findings['kwh_q4'] = quarterly_totals.get(4, 0.0)
    
    # --- Q4: Half-year change ---
    # H1: Jan-Jun (months 1-6), H2: Jul-Dec (months 7-12)
    h1_mask = df['reading_date'].dt.month <= 6
    h2_mask = df['reading_date'].dt.month >= 7
    
    kwh_h1 = df.loc[h1_mask, 'energy_kwh'].sum()
    kwh_h2 = df.loc[h2_mask, 'energy_kwh'].sum()
    
    findings['kwh_h1'] = kwh_h1
    findings['kwh_h2'] = kwh_h2
    findings['kwh_h2_vs_h1_change_pct'] = ((kwh_h2 - kwh_h1) / kwh_h1) * 100
    
    # --- Q5: Hot-day commercial load ---
    # Commercial readings with temperature_c >= 25
    hot_commercial = df[(df['building_type'] == 'Commercial') & (df['temperature_c'] >= 25)]
    findings['hot_commercial_reading_count'] = len(hot_commercial)
    findings['hot_commercial_mean_kwh'] = hot_commercial['energy_kwh'].mean()
    
    # --- Q6: Distribution summary ---
    findings['kwh_median'] = df['energy_kwh'].median()
    findings['kwh_std'] = df['energy_kwh'].std(ddof=1)  # sample std (n-1)
    
    temp_valid = df['temperature_c'].dropna()
    findings['temperature_mean'] = temp_valid.mean()
    findings['temperature_missing_count'] = df['temperature_c'].isna().sum()
    
    # Pearson correlation for Commercial readings with non-missing temperature
    commercial_temp_valid = df[(df['building_type'] == 'Commercial') & (df['temperature_c'].notna())]
    if len(commercial_temp_valid) > 1:
        findings['commercial_temp_kwh_corr'] = commercial_temp_valid['temperature_c'].corr(commercial_temp_valid['energy_kwh'])
    else:
        findings['commercial_temp_kwh_corr'] = float('nan')
    
    # --- Q7: Tariff and meter usage ---
    tariff_totals = df.groupby('tariff')['energy_kwh'].sum()
    kwh_peak = tariff_totals.get('peak', 0.0)
    kwh_off_peak = tariff_totals.get('off-peak', 0.0)
    
    findings['kwh_peak'] = kwh_peak
    findings['kwh_off_peak'] = kwh_off_peak
    findings['peak_kwh_share_pct'] = (kwh_peak / total_kwh) * 100
    
    findings['unique_meter_count'] = df['meter_id'].nunique()
    
    meter_totals = df.groupby('meter_id')['energy_kwh'].sum()
    findings['highest_use_meter_kwh'] = meter_totals.max()
    
    # Write findings to JSON
    with open(output_path, 'w') as f:
        json.dump(findings, f)

if __name__ == "__main__":
    run_analysis()
