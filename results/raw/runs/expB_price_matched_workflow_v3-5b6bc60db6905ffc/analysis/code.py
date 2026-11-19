import os
import json
import pandas as pd
import numpy as np

def run_analysis():
    # Define paths
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    
    # Read cleaned data
    # reading_date is parsed as dates. building_type and tariff are categorical.
    df = pd.read_csv(
        input_path, 
        parse_dates=['reading_date'],
        dtype={'building_type': 'category', 'tariff': 'category'}
    )
    
    findings = {}
    
    # --- Q1: Overall ---
    total_kwh = df['energy_kwh'].sum()
    reading_count = len(df)
    mean_kwh_per_reading = total_kwh / reading_count
    
    findings['total_kwh'] = total_kwh
    findings['reading_count'] = reading_count
    findings['mean_kwh_per_reading'] = mean_kwh_per_reading
    
    # --- Q2: Building types ---
    building_totals = df.groupby('building_type', observed=False)['energy_kwh'].sum()
    findings['kwh_residential'] = building_totals.get('Residential', 0.0)
    findings['kwh_commercial'] = building_totals.get('Commercial', 0.0)
    findings['kwh_industrial'] = building_totals.get('Industrial', 0.0)
    
    # --- Q3: Quarterly trend ---
    # Extract quarter from date (Q1=1, Q2=2, etc.)
    df['quarter'] = df['reading_date'].dt.quarter
    quarterly_totals = df.groupby('quarter')['energy_kwh'].sum()
    findings['kwh_q1'] = quarterly_totals.get(1, 0.0)
    findings['kwh_q2'] = quarterly_totals.get(2, 0.0)
    findings['kwh_q3'] = quarterly_totals.get(3, 0.0)
    findings['kwh_q4'] = quarterly_totals.get(4, 0.0)
    
    # --- Q4: Half-year change ---
    # H1: Jan-Jun (months 1-6), H2: Jul-Dec (months 7-12)
    df['half'] = np.where(df['reading_date'].dt.month <= 6, 'H1', 'H2')
    half_totals = df.groupby('half')['energy_kwh'].sum()
    kwh_h1 = half_totals.get('H1', 0.0)
    kwh_h2 = half_totals.get('H2', 0.0)
    kwh_h2_vs_h1_change_pct = ((kwh_h2 - kwh_h1) / kwh_h1) * 100
    
    findings['kwh_h1'] = kwh_h1
    findings['kwh_h2'] = kwh_h2
    findings['kwh_h2_vs_h1_change_pct'] = kwh_h2_vs_h1_change_pct
    
    # --- Q5: Hot-day commercial load ---
    # Commercial readings with temperature_c >= 25
    hot_commercial_df = df[
        (df['building_type'] == 'Commercial') & 
        (df['temperature_c'] >= 25)
    ]
    hot_commercial_reading_count = len(hot_commercial_df)
    hot_commercial_mean_kwh = hot_commercial_df['energy_kwh'].mean() if hot_commercial_reading_count > 0 else 0.0
    
    findings['hot_commercial_reading_count'] = hot_commercial_reading_count
    findings['hot_commercial_mean_kwh'] = hot_commercial_mean_kwh
    
    # --- Q6: Distribution summary ---
    # Median and sample std of energy_kwh
    findings['kwh_median'] = df['energy_kwh'].median()
    findings['kwh_std'] = df['energy_kwh'].std(ddof=1) # sample std (n-1)
    
    # Mean temperature (non-missing)
    temp_valid = df['temperature_c'].dropna()
    findings['temperature_mean'] = temp_valid.mean()
    
    # Missing temperature count
    findings['temperature_missing_count'] = df['temperature_c'].isna().sum()
    
    # Pearson correlation for Commercial readings with non-missing temperature
    commercial_df = df[df['building_type'] == 'Commercial']
    commercial_valid_temp = commercial_df.dropna(subset=['temperature_c', 'energy_kwh'])
    
    if len(commercial_valid_temp) >= 2:
        corr = commercial_valid_temp['temperature_c'].corr(commercial_valid_temp['energy_kwh'])
        findings['commercial_temp_kwh_corr'] = corr
    else:
        findings['commercial_temp_kwh_corr'] = 0.0
    
    # --- Q7: Tariff and meter usage ---
    # Peak and off-peak totals
    tariff_totals = df.groupby('tariff', observed=False)['energy_kwh'].sum()
    kwh_peak = tariff_totals.get('peak', 0.0)
    kwh_off_peak = tariff_totals.get('off-peak', 0.0)
    peak_kwh_share_pct = (kwh_peak / total_kwh) * 100
    
    findings['kwh_peak'] = kwh_peak
    findings['kwh_off_peak'] = kwh_off_peak
    findings['peak_kwh_share_pct'] = peak_kwh_share_pct
    
    # Unique meter count
    findings['unique_meter_count'] = df['meter_id'].nunique()
    
    # Highest use meter
    meter_totals = df.groupby('meter_id')['energy_kwh'].sum()
    findings['highest_use_meter_kwh'] = meter_totals.max()
    
    # Write findings to JSON
    # Ensure all values are standard Python types (float/int) for JSON serialization
    # Pandas/NumPy types are generally handled, but explicit casting is safer.
    clean_findings = {k: float(v) if isinstance(v, (np.floating, np.integer)) else v for k, v in findings.items()}
    # Handle numpy booleans if any (none expected here, but good practice)
    clean_findings = {k: bool(v) if isinstance(v, np.bool_) else v for k, v in clean_findings.items()}
    
    with open(output_path, 'w') as f:
        json.dump(clean_findings, f)

if __name__ == "__main__":
    run_analysis()
