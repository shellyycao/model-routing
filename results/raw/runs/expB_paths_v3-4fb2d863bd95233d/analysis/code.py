import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths from environment variables
    input_dir = os.getenv("INPUT_DIR")
    output_dir = os.getenv("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise EnvironmentError("INPUT_DIR and OUTPUT_DIR must be set in the environment")

    cleaned_path = os.path.join(input_dir, "cleaned.csv")
    findings_path = os.path.join(output_dir, "findings.json")

    # Load cleaned data
    df = pd.read_csv(cleaned_path, parse_dates=["reading_date"])

    # ---------- q1: overall aggregation ----------
    total_kwh = float(df["energy_kwh"].sum())
    reading_count = int(len(df))
    mean_kwh_per_reading = total_kwh / reading_count if reading_count else 0.0

    # ---------- q2: building type totals ----------
    kwh_residential = float(df.loc[df["building_type"] == "Residential", "energy_kwh"].sum())
    kwh_commercial = float(df.loc[df["building_type"] == "Commercial", "energy_kwh"].sum())
    kwh_industrial = float(df.loc[df["building_type"] == "Industrial", "energy_kwh"].sum())

    # ---------- q3: quarterly trend ----------
    df["quarter"] = df["reading_date"].dt.quarter
    kwh_q1 = float(df.loc[df["quarter"] == 1, "energy_kwh"].sum())
    kwh_q2 = float(df.loc[df["quarter"] == 2, "energy_kwh"].sum())
    kwh_q3 = float(df.loc[df["quarter"] == 3, "energy_kwh"].sum())
    kwh_q4 = float(df.loc[df["quarter"] == 4, "energy_kwh"].sum())

    # ---------- q4: half‑year change ----------
    df["month"] = df["reading_date"].dt.month
    kwh_h1 = float(df.loc[df["month"] <= 6, "energy_kwh"].sum())
    kwh_h2 = float(df.loc[df["month"] >= 7, "energy_kwh"].sum())
    if kwh_h1 != 0:
        kwh_h2_vs_h1_change_pct = (kwh_h2 - kwh_h1) / kwh_h1 * 100.0
    else:
        kwh_h2_vs_h1_change_pct = 0.0

    # ---------- q5: hot‑day commercial load ----------
    hot_mask = (
        (df["building_type"] == "Commercial") &
        df["temperature_c"].notna() &
        (df["temperature_c"] >= 25)
    )
    hot_commercial_reading_count = int(hot_mask.sum())
    if hot_commercial_reading_count:
        hot_commercial_mean_kwh = float(df.loc[hot_mask, "energy_kwh"].mean())
    else:
        hot_commercial_mean_kwh = 0.0

    # ---------- q6: distribution summary ----------
    kwh_median = float(df["energy_kwh"].median())
    kwh_std = float(df["energy_kwh"].std(ddof=1))
    temperature_mean = float(df["temperature_c"].mean()) if df["temperature_c"].notna().any() else 0.0
    temperature_missing_count = int(df["temperature_c"].isna().sum())

    commercial_temp_mask = (
        (df["building_type"] == "Commercial") & df["temperature_c"].notna()
    )
    if commercial_temp_mask.sum() >= 2:
        commercial_temp_kwh_corr = float(
            df.loc[commercial_temp_mask, "temperature_c"].corr(df.loc[commercial_temp_mask, "energy_kwh"])
        )
    else:
        commercial_temp_kwh_corr = 0.0

    # ---------- q7: tariff and meter usage ----------
    kwh_peak = float(df.loc[df["tariff"] == "peak", "energy_kwh"].sum())
    kwh_off_peak = float(df.loc[df["tariff"] == "off-peak", "energy_kwh"].sum())
    peak_kwh_share_pct = (kwh_peak / total_kwh * 100.0) if total_kwh != 0 else 0.0
    unique_meter_count = int(df["meter_id"].nunique())
    highest_use_meter_kwh = float(df.groupby("meter_id")["energy_kwh"].sum().max())

    # Assemble findings dictionary (flat, numeric values only)
    findings = {
        "total_kwh": total_kwh,
        "reading_count": reading_count,
        "mean_kwh_per_reading": mean_kwh_per_reading,
        "kwh_residential": kwh_residential,
        "kwh_commercial": kwh_commercial,
        "kwh_industrial": kwh_industrial,
        "kwh_q1": kwh_q1,
        "kwh_q2": kwh_q2,
        "kwh_q3": kwh_q3,
        "kwh_q4": kwh_q4,
        "kwh_h1": kwh_h1,
        "kwh_h2": kwh_h2,
        "kwh_h2_vs_h1_change_pct": kwh_h2_vs_h1_change_pct,
        "hot_commercial_reading_count": hot_commercial_reading_count,
        "hot_commercial_mean_kwh": hot_commercial_mean_kwh,
        "kwh_median": kwh_median,
        "kwh_std": kwh_std,
        "temperature_mean": temperature_mean,
        "temperature_missing_count": temperature_missing_count,
        "commercial_temp_kwh_corr": commercial_temp_kwh_corr,
        "kwh_peak": kwh_peak,
        "kwh_off_peak": kwh_off_peak,
        "peak_kwh_share_pct": peak_kwh_share_pct,
        "unique_meter_count": unique_meter_count,
        "highest_use_meter_kwh": highest_use_meter_kwh
    }

    # Write findings to JSON file
    with open(findings_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
