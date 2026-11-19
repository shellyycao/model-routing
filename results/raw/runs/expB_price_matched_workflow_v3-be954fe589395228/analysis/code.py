import os
import json
import pandas as pd
import numpy as np

def main():
    # Read cleaned data
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    df = pd.read_csv(input_path)
    
    # Ensure proper dtypes
    df['reading_date'] = pd.to_datetime(df['reading_date'])
    df['energy_kwh'] = df['energy_kwh'].astype(float)
    df['temperature_c'] = pd.to_numeric(df['temperature_c'], errors='coerce')
    
    findings = {}
    
    # Q1: Overall aggregation
    total_kwh = df['energy_kwh'].sum()
    reading_count = len(df)
    mean_kwh_per_reading = total_kwh / reading_count
    findings['total_kwh'] = total_kwh
    findings['reading_count'] = reading_count
    findings['mean_kwh_per_reading'] = mean_kwh_per_reading
    
    # Q2: Building types
    building_totals = df.groupby('building_type')['energy_kwh'].sum()
    findings['kwh_residential'] = building_totals.get('Residential', 0.0)
    findings['kwh_commercial'] = building_totals.get('Commercial', 0.0)
    findings['kwh_industrial'] = building_totals.get('Industrial', 0.0)
    
    # Q3: Quarterly trend
    df['quarter'] = df['reading_date'].dt.quarter
    quarterly_totals = df.groupby('quarter')['energy_kwh'].sum()
    findings['kwh_q1'] = quarterly_totals.get(1, 0.0)
    findings['kwh_q2'] = quarterly_totals.get(2, 0.0)
    findings['kwh_q3'] = quarterly_totals.get(3, 0.0)
    findings['kwh_q4'] = quarterly_totals.get(4, 0.0)
    
    # Q4: Half-year change
    h1 = df[df['reading_date'].dt.month <= 6]['energy_kwh'].sum()
    h2 = df[df['reading_date'].dt.month >= 7]['energy_kwh'].sum()
    findings['kwh_h1'] = h1
    findings['kwh_h2'] = h2
    findings['kwh_h2_vs_h1_change_pct'] = ((h2 - h1) / h1) * 100
    
    # Q5: Hot-day commercial load
    hot_commercial = df[(df['building_type'] == 'Commercial') & (df['temperature_c'] >= 25)]
    findings['hot_commercial_reading_count'] = len(hot_commercial)
    findings['hot_commercial_mean_kwh'] = hot_commercial['energy_kwh'].mean()
    
    # Q6: Distribution summary
    findings['kwh_median'] = df['energy_kwh'].median()
    findings['kwh_std'] = df['energy_kwh'].std(ddof=1)
    temp_valid = df['temperature_c'].dropna()
    findings['temperature_mean'] = temp_valid.mean()
    findings['temperature_missing_count'] = df['temperature_c'].isna().sum()
    commercial_temp_valid = df[(df['building_type'] == 'Commercial') & (df['temperature_c'].notna())]
    if len(commercial_temp_valid) > 1:
        findings['commercial_temp_kwh_corr'] = commercial_temp_valid['temperature_c'].corr(commercial_temp_valid['energy_kwh'])
    else:
        findings['commercial_temp_kwh_corr'] = float('nan')
    
    # Q7: Tariff and meter usage
    tariff_totals = df.groupby('tariff')['energy_kwh'].sum()
    kwh_peak = tariff_totals.get('peak', 0.0)
    kwh_off_peak = tariff_totals.get('off-peak', 0.0)
    findings['kwh_peak'] = kwh_peak
    findings['kwh_off_peak'] = kwh_off_peak
    findings['peak_kwh_share_pct'] = (kwh_peak / total_kwh) * 100
    findings['unique_meter_count'] = df['meter_id'].nunique()
    findings['highest_use_meter_kwh'] = df.groupby('meter_id')['energy_kwh'].sum().max()
    
    # Write findings
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    with open(output_path, 'w') as f:
        json.dump(findings, f)

if __name__ == "__main__":
    main()
