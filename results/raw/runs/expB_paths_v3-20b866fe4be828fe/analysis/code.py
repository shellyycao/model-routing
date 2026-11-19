import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths from environment variables
    input_dir = os.getenv('INPUT_DIR')
    output_dir = os.getenv('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('INPUT_DIR and OUTPUT_DIR environment variables must be set')

    cleaned_path = os.path.join(input_dir, 'cleaned.csv')
    findings_path = os.path.join(output_dir, 'findings.json')

    # Load cleaned data
    df = pd.read_csv(cleaned_path, parse_dates=['reading_date'])

    # ---------------------------------------------------------------------
    # q1 – overall aggregation
    total_kwh = df['energy_kwh'].sum()
    reading_count = len(df)
    mean_kwh_per_reading = total_kwh / reading_count if reading_count else 0.0

    # ---------------------------------------------------------------------
    # q2 – building type totals
    kwh_residential = df.loc[df['building_type'] == 'Residential', 'energy_kwh'].sum()
    kwh_commercial = df.loc[df['building_type'] == 'Commercial', 'energy_kwh'].sum()
    kwh_industrial = df.loc[df['building_type'] == 'Industrial', 'energy_kwh'].sum()

    # ---------------------------------------------------------------------
    # q3 – quarterly trend (calendar quarters of 2024)
    df['quarter'] = df['reading_date'].dt.quarter
    kwh_q1 = df.loc[df['quarter'] == 1, 'energy_kwh'].sum()
    kwh_q2 = df.loc[df['quarter'] == 2, 'energy_kwh'].sum()
    kwh_q3 = df.loc[df['quarter'] == 3, 'energy_kwh'].sum()
    kwh_q4 = df.loc[df['quarter'] == 4, 'energy_kwh'].sum()

    # ---------------------------------------------------------------------
    # q4 – half‑year change
    df['month'] = df['reading_date'].dt.month
    kwh_h1 = df.loc[df['month'].between(1, 6), 'energy_kwh'].sum()
    kwh_h2 = df.loc[df['month'].between(7, 12), 'energy_kwh'].sum()
    if kwh_h1 != 0:
        kwh_h2_vs_h1_change_pct = (kwh_h2 - kwh_h1) / kwh_h1 * 100.0
    else:
        kwh_h2_vs_h1_change_pct = 0.0

    # ---------------------------------------------------------------------
    # q5 – hot‑day commercial load (temperature >= 25°C)
    hot_commercial = df[(df['building_type'] == 'Commercial') & (df['temperature_c'] >= 25)]
    hot_commercial_reading_count = int(hot_commercial.shape[0])
    hot_commercial_mean_kwh = hot_commercial['energy_kwh'].mean()
    if pd.isna(hot_commercial_mean_kwh):
        hot_commercial_mean_kwh = 0.0

    # ---------------------------------------------------------------------
    # q6 – distribution summary
    kwh_median = df['energy_kwh'].median()
    kwh_std = df['energy_kwh'].std(ddof=1)  # sample standard deviation
    temperature_mean = df['temperature_c'].mean()
    if pd.isna(temperature_mean):
        temperature_mean = 0.0
    temperature_missing_count = int(df['temperature_c'].isna().sum())

    # Pearson correlation for Commercial rows with temperature present
    commercial_temp = df[(df['building_type'] == 'Commercial') & df['temperature_c'].notna()]
    if len(commercial_temp) >= 2:
        commercial_temp_kwh_corr = commercial_temp['temperature_c'].corr(commercial_temp['energy_kwh'])
        if pd.isna(commercial_temp_kwh_corr):
            commercial_temp_kwh_corr = 0.0
    else:
        commercial_temp_kwh_corr = 0.0

    # ---------------------------------------------------------------------
    # q7 – tariff and meter usage
    kwh_peak = df.loc[df['tariff'] == 'peak', 'energy_kwh'].sum()
    kwh_off_peak = df.loc[df['tariff'] == 'off-peak', 'energy_kwh'].sum()
    peak_kwh_share_pct = (kwh_peak / total_kwh * 100.0) if total_kwh else 0.0
    unique_meter_count = int(df['meter_id'].nunique())
    highest_use_meter_kwh = df.groupby('meter_id')['energy_kwh'].sum().max()

    # ---------------------------------------------------------------------
    # Assemble findings dictionary – all values are plain Python numbers
    findings = {
        'total_kwh': float(total_kwh),
        'reading_count': int(reading_count),
        'mean_kwh_per_reading': float(mean_kwh_per_reading),
        'kwh_residential': float(kwh_residential),
        'kwh_commercial': float(kwh_commercial),
        'kwh_industrial': float(kwh_industrial),
        'kwh_q1': float(kwh_q1),
        'kwh_q2': float(kwh_q2),
        'kwh_q3': float(kwh_q3),
        'kwh_q4': float(kwh_q4),
        'kwh_h1': float(kwh_h1),
        'kwh_h2': float(kwh_h2),
        'kwh_h2_vs_h1_change_pct': float(kwh_h2_vs_h1_change_pct),
        'hot_commercial_reading_count': hot_commercial_reading_count,
        'hot_commercial_mean_kwh': float(hot_commercial_mean_kwh),
        'kwh_median': float(kwh_median),
        'kwh_std': float(kwh_std),
        'temperature_mean': float(temperature_mean),
        'temperature_missing_count': temperature_missing_count,
        'commercial_temp_kwh_corr': float(commercial_temp_kwh_corr),
        'kwh_peak': float(kwh_peak),
        'kwh_off_peak': float(kwh_off_peak),
        'peak_kwh_share_pct': float(peak_kwh_share_pct),
        'unique_meter_count': unique_meter_count,
        'highest_use_meter_kwh': float(highest_use_meter_kwh)
    }

    # Write findings to JSON file
    with open(findings_path, 'w') as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == '__main__':
    main()
