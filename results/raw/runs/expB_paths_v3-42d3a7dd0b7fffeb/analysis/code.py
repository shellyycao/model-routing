import os
import json
import pandas as pd
import numpy as np

def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Load cleaned data
    df = pd.read_csv(input_path, parse_dates=["reading_date"], dtype={
        "reading_id": str,
        "meter_id": str,
        "building_type": "category",
        "tariff": "category",
        "energy_kwh": float,
        "temperature_c": float
    })

    # Ensure temperature column is float with NaNs for missing values
    # (pandas already does this when reading with dtype=float)

    # Basic aggregates
    total_kwh = df["energy_kwh"].sum()
    reading_count = len(df)
    mean_kwh_per_reading = total_kwh / reading_count if reading_count else 0.0

    # Building type totals
    kwh_residential = df.loc[df["building_type"] == "Residential", "energy_kwh"].sum()
    kwh_commercial = df.loc[df["building_type"] == "Commercial", "energy_kwh"].sum()
    kwh_industrial = df.loc[df["building_type"] == "Industrial", "energy_kwh"].sum()

    # Quarterly totals (2024 only)
    df_q = df.copy()
    df_q["quarter"] = df_q["reading_date"].dt.quarter
    kwh_q1 = df_q.loc[df_q["quarter"] == 1, "energy_kwh"].sum()
    kwh_q2 = df_q.loc[df_q["quarter"] == 2, "energy_kwh"].sum()
    kwh_q3 = df_q.loc[df_q["quarter"] == 3, "energy_kwh"].sum()
    kwh_q4 = df_q.loc[df_q["quarter"] == 4, "energy_kwh"].sum()

    # Half‑year totals
    df_h = df.copy()
    df_h["month"] = df_h["reading_date"].dt.month
    kwh_h1 = df_h.loc[df_h["month"] <= 6, "energy_kwh"].sum()
    kwh_h2 = df_h.loc[df_h["month"] >= 7, "energy_kwh"].sum()
    if kwh_h1 != 0:
        kwh_h2_vs_h1_change_pct = (kwh_h2 - kwh_h1) / kwh_h1 * 100.0
    else:
        kwh_h2_vs_h1_change_pct = 0.0

    # Hot‑day commercial load (temperature >= 25°C)
    hot_commercial = df[(df["building_type"] == "Commercial") & (df["temperature_c"].notna()) & (df["temperature_c"] >= 25)]
    hot_commercial_reading_count = len(hot_commercial)
    hot_commercial_mean_kwh = hot_commercial["energy_kwh"].mean() if hot_commercial_reading_count else 0.0

    # Distribution summary
    kwh_median = df["energy_kwh"].median()
    kwh_std = df["energy_kwh"].std(ddof=1)  # sample std
    temperature_mean = df["temperature_c"].mean()
    temperature_missing_count = df["temperature_c"].isna().sum()

    # Correlation for Commercial with temperature present
    commercial_temp = df[(df["building_type"] == "Commercial") & df["temperature_c"].notna()]
    if len(commercial_temp) >= 2:
        commercial_temp_kwh_corr = commercial_temp["temperature_c"].corr(commercial_temp["energy_kwh"]).item()
        if pd.isna(commercial_temp_kwh_corr):
            commercial_temp_kwh_corr = 0.0
    else:
        commercial_temp_kwh_corr = 0.0

    # Tariff totals and share
    kwh_peak = df.loc[df["tariff"] == "peak", "energy_kwh"].sum()
    kwh_off_peak = df.loc[df["tariff"] == "off-peak", "energy_kwh"].sum()
    peak_kwh_share_pct = (kwh_peak / total_kwh * 100.0) if total_kwh else 0.0

    # Meter usage
    unique_meter_count = df["meter_id"].nunique()
    highest_use_meter_kwh = df.groupby("meter_id")["energy_kwh"].sum().max()

    # Assemble findings ensuring all values are finite numbers
    findings = {
        "total_kwh": float(total_kwh),
        "reading_count": int(reading_count),
        "mean_kwh_per_reading": float(mean_kwh_per_reading),
        "kwh_residential": float(kwh_residential),
        "kwh_commercial": float(kwh_commercial),
        "kwh_industrial": float(kwh_industrial),
        "kwh_q1": float(kwh_q1),
        "kwh_q2": float(kwh_q2),
        "kwh_q3": float(kwh_q3),
        "kwh_q4": float(kwh_q4),
        "kwh_h1": float(kwh_h1),
        "kwh_h2": float(kwh_h2),
        "kwh_h2_vs_h1_change_pct": float(kwh_h2_vs_h1_change_pct),
        "hot_commercial_reading_count": int(hot_commercial_reading_count),
        "hot_commercial_mean_kwh": float(hot_commercial_mean_kwh),
        "kwh_median": float(kwh_median),
        "kwh_std": float(kwh_std) if pd.notna(kwh_std) else 0.0,
        "temperature_mean": float(temperature_mean) if pd.notna(temperature_mean) else 0.0,
        "temperature_missing_count": int(temperature_missing_count),
        "commercial_temp_kwh_corr": float(commercial_temp_kwh_corr),
        "kwh_peak": float(kwh_peak),
        "kwh_off_peak": float(kwh_off_peak),
        "peak_kwh_share_pct": float(peak_kwh_share_pct),
        "unique_meter_count": int(unique_meter_count),
        "highest_use_meter_kwh": float(highest_use_meter_kwh)
    }

    # Write findings to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
