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

    # Basic aggregates
    total_kwh = df["energy_kwh"].sum()
    reading_count = len(df)
    mean_kwh_per_reading = total_kwh / reading_count if reading_count else 0.0

    # Building type totals
    kwh_by_type = df.groupby("building_type")["energy_kwh"].sum()
    kwh_residential = kwh_by_type.get("Residential", 0.0)
    kwh_commercial = kwh_by_type.get("Commercial", 0.0)
    kwh_industrial = kwh_by_type.get("Industrial", 0.0)

    # Quarterly totals
    df["quarter"] = df["reading_date"].dt.quarter
    kwh_by_quarter = df.groupby("quarter")["energy_kwh"].sum()
    kwh_q1 = kwh_by_quarter.get(1, 0.0)
    kwh_q2 = kwh_by_quarter.get(2, 0.0)
    kwh_q3 = kwh_by_quarter.get(3, 0.0)
    kwh_q4 = kwh_by_quarter.get(4, 0.0)

    # Half‑year totals and change percentage
    df["half"] = np.where(df["reading_date"].dt.month <= 6, 1, 2)
    kwh_by_half = df.groupby("half")["energy_kwh"].sum()
    kwh_h1 = kwh_by_half.get(1, 0.0)
    kwh_h2 = kwh_by_half.get(2, 0.0)
    if kwh_h1 != 0:
        kwh_h2_vs_h1_change_pct = (kwh_h2 - kwh_h1) / kwh_h1 * 100.0
    else:
        kwh_h2_vs_h1_change_pct = 0.0

    # Hot‑day commercial load
    hot_commercial = df[(df["building_type"] == "Commercial") & (df["temperature_c"].notna()) & (df["temperature_c"] >= 25)]
    hot_commercial_reading_count = int(len(hot_commercial))
    hot_commercial_mean_kwh = hot_commercial["energy_kwh"].mean() if hot_commercial_reading_count else 0.0

    # Distribution summary
    kwh_median = df["energy_kwh"].median()
    kwh_std = df["energy_kwh"].std(ddof=1)  # sample std
    temperature_mean = df["temperature_c"].mean()
    temperature_missing_count = int(df["temperature_c"].isna().sum())
    commercial_temp = df[(df["building_type"] == "Commercial") & df["temperature_c"].notna()]
    if len(commercial_temp) >= 2:
        commercial_temp_kwh_corr = commercial_temp["temperature_c"].corr(commercial_temp["energy_kwh"])
        if pd.isna(commercial_temp_kwh_corr):
            commercial_temp_kwh_corr = 0.0
    else:
        commercial_temp_kwh_corr = 0.0

    # Tariff and meter usage
    kwh_peak = df.loc[df["tariff"] == "peak", "energy_kwh"].sum()
    kwh_off_peak = df.loc[df["tariff"] == "off-peak", "energy_kwh"].sum()
    peak_kwh_share_pct = (kwh_peak / total_kwh * 100.0) if total_kwh else 0.0
    unique_meter_count = int(df["meter_id"].nunique())
    kwh_by_meter = df.groupby("meter_id")["energy_kwh"].sum()
    highest_use_meter_kwh = kwh_by_meter.max() if not kwh_by_meter.empty else 0.0

    # Assemble findings ensuring plain Python scalars
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
        "kwh_std": float(kwh_std),
        "temperature_mean": float(temperature_mean) if not pd.isna(temperature_mean) else 0.0,
        "temperature_missing_count": int(temperature_missing_count),
        "commercial_temp_kwh_corr": float(commercial_temp_kwh_corr),
        "kwh_peak": float(kwh_peak),
        "kwh_off_peak": float(kwh_off_peak),
        "peak_kwh_share_pct": float(peak_kwh_share_pct),
        "unique_meter_count": int(unique_meter_count),
        "highest_use_meter_kwh": float(highest_use_meter_kwh)
    }

    # Write findings
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
