import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths provided by the workflow environment
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Load cleaned data – dates are already in ISO format
    df = pd.read_csv(input_path, parse_dates=["reading_date"])

    # ---------------------------------------------------------------------
    # q1 – overall aggregation
    # ---------------------------------------------------------------------
    total_kwh = df["energy_kwh"].sum()
    reading_count = len(df)
    mean_kwh_per_reading = total_kwh / reading_count if reading_count else 0.0

    # ---------------------------------------------------------------------
    # q2 – building‑type totals
    # ---------------------------------------------------------------------
    building_totals = df.groupby("building_type")["energy_kwh"].sum()
    kwh_residential = building_totals.get("Residential", 0.0)
    kwh_commercial = building_totals.get("Commercial", 0.0)
    kwh_industrial = building_totals.get("Industrial", 0.0)

    # ---------------------------------------------------------------------
    # q3 – quarterly trend (calendar quarters of 2024)
    # ---------------------------------------------------------------------
    df["quarter"] = df["reading_date"].dt.quarter
    quarterly_totals = df.groupby("quarter")["energy_kwh"].sum()
    kwh_q1 = quarterly_totals.get(1, 0.0)
    kwh_q2 = quarterly_totals.get(2, 0.0)
    kwh_q3 = quarterly_totals.get(3, 0.0)
    kwh_q4 = quarterly_totals.get(4, 0.0)

    # ---------------------------------------------------------------------
    # q4 – half‑year change
    # ---------------------------------------------------------------------
    df["month"] = df["reading_date"].dt.month
    kwh_h1 = df[df["month"] <= 6]["energy_kwh"].sum()
    kwh_h2 = df[df["month"] >= 7]["energy_kwh"].sum()
    if kwh_h1 != 0:
        kwh_h2_vs_h1_change_pct = (kwh_h2 - kwh_h1) / kwh_h1 * 100
    else:
        kwh_h2_vs_h1_change_pct = 0.0

    # ---------------------------------------------------------------------
    # q5 – hot‑day commercial load (temperature ≥ 25 °C)
    # ---------------------------------------------------------------------
    hot_commercial = df[(df["building_type"] == "Commercial") &
                        df["temperature_c"].notna() &
                        (df["temperature_c"] >= 25)]
    hot_commercial_reading_count = len(hot_commercial)
    hot_commercial_mean_kwh = hot_commercial["energy_kwh"].mean() if hot_commercial_reading_count else 0.0

    # ---------------------------------------------------------------------
    # q6 – distribution summary & correlation
    # ---------------------------------------------------------------------
    kwh_median = df["energy_kwh"].median()
    kwh_std = df["energy_kwh"].std(ddof=1)
    temperature_missing_count = df["temperature_c"].isna().sum()
    temperature_mean = df["temperature_c"].mean(skipna=True)

    commercial_temp = df[(df["building_type"] == "Commercial") & df["temperature_c"].notna()]
    if len(commercial_temp) >= 2:
        commercial_temp_kwh_corr = commercial_temp["temperature_c"].corr(commercial_temp["energy_kwh"])
        if pd.isna(commercial_temp_kwh_corr):
            commercial_temp_kwh_corr = 0.0
    else:
        commercial_temp_kwh_corr = 0.0

    # ---------------------------------------------------------------------
    # q7 – tariff & meter usage
    # ---------------------------------------------------------------------
    tariff_totals = df.groupby("tariff")["energy_kwh"].sum()
    kwh_peak = tariff_totals.get("peak", 0.0)
    kwh_off_peak = tariff_totals.get("off-peak", 0.0)
    peak_kwh_share_pct = (kwh_peak / total_kwh * 100) if total_kwh else 0.0
    unique_meter_count = df["meter_id"].nunique()
    meter_totals = df.groupby("meter_id")["energy_kwh"].sum()
    highest_use_meter_kwh = meter_totals.max() if not meter_totals.empty else 0.0

    # ---------------------------------------------------------------------
    # Assemble flat JSON with plain Python numbers (no NaN/Inf)
    # ---------------------------------------------------------------------
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

    # Write results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
