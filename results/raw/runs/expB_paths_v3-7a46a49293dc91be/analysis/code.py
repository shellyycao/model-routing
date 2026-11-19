import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths
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

    # ---------- q1: overall aggregation ----------
    total_kwh = df["energy_kwh"].sum()
    reading_count = len(df)
    mean_kwh_per_reading = total_kwh / reading_count if reading_count else 0.0

    # ---------- q2: building type totals ----------
    building_sums = df.groupby("building_type")["energy_kwh"].sum()
    kwh_residential = building_sums.get("Residential", 0.0)
    kwh_commercial = building_sums.get("Commercial", 0.0)
    kwh_industrial = building_sums.get("Industrial", 0.0)

    # ---------- q3: quarterly trend ----------
    df["quarter"] = df["reading_date"].dt.quarter
    quarter_sums = df.groupby("quarter")["energy_kwh"].sum()
    kwh_q1 = quarter_sums.get(1, 0.0)
    kwh_q2 = quarter_sums.get(2, 0.0)
    kwh_q3 = quarter_sums.get(3, 0.0)
    kwh_q4 = quarter_sums.get(4, 0.0)

    # ---------- q4: half‑year change ----------
    df["month"] = df["reading_date"].dt.month
    h1_mask = df["month"].between(1, 6)
    h2_mask = df["month"].between(7, 12)
    kwh_h1 = df.loc[h1_mask, "energy_kwh"].sum()
    kwh_h2 = df.loc[h2_mask, "energy_kwh"].sum()
    if kwh_h1 != 0:
        kwh_h2_vs_h1_change_pct = (kwh_h2 - kwh_h1) / kwh_h1 * 100.0
    else:
        kwh_h2_vs_h1_change_pct = 0.0

    # ---------- q5: hot‑day commercial load ----------
    hot_commercial = df[(df["building_type"] == "Commercial") & (df["temperature_c"].notna()) & (df["temperature_c"] >= 25)]
    hot_commercial_reading_count = len(hot_commercial)
    hot_commercial_mean_kwh = hot_commercial["energy_kwh"].mean() if hot_commercial_reading_count else 0.0

    # ---------- q6: distribution summary ----------
    kwh_median = df["energy_kwh"].median()
    kwh_std = df["energy_kwh"].std(ddof=1)  # sample std
    temperature_mean = df["temperature_c"].mean()
    temperature_missing_count = df["temperature_c"].isna().sum()
    commercial_temp = df[(df["building_type"] == "Commercial") & df["temperature_c"].notna()]
    if len(commercial_temp) >= 2:
        commercial_temp_kwh_corr = commercial_temp["temperature_c"].corr(commercial_temp["energy_kwh"]).item()
    else:
        commercial_temp_kwh_corr = 0.0
    # Replace possible NaN with 0.0 to satisfy JSON finiteness
    temperature_mean = 0.0 if pd.isna(temperature_mean) else temperature_mean
    kwh_median = 0.0 if pd.isna(kwh_median) else kwh_median
    kwh_std = 0.0 if pd.isna(kwh_std) else kwh_std
    commercial_temp_kwh_corr = 0.0 if pd.isna(commercial_temp_kwh_corr) else commercial_temp_kwh_corr

    # ---------- q7: tariff and meter usage ----------
    tariff_sums = df.groupby("tariff")["energy_kwh"].sum()
    kwh_peak = tariff_sums.get("peak", 0.0)
    kwh_off_peak = tariff_sums.get("off-peak", 0.0)
    peak_kwh_share_pct = (kwh_peak / total_kwh * 100.0) if total_kwh else 0.0
    unique_meter_count = df["meter_id"].nunique()
    meter_sums = df.groupby("meter_id")["energy_kwh"].sum()
    highest_use_meter_kwh = meter_sums.max() if not meter_sums.empty else 0.0

    # Assemble findings
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

    # Write findings to JSON (flat, numeric values only)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
