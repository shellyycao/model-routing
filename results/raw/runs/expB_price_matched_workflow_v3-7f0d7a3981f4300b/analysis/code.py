import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)
    df["reading_date"] = pd.to_datetime(df["reading_date"], format="%Y-%m-%d")
    energy = df["energy_kwh"].astype(float)
    temp = df["temperature_c"].astype(float)

    findings = {}

    # q1: overall aggregation
    total_kwh = float(energy.sum())
    reading_count = int(len(df))
    findings["total_kwh"] = total_kwh
    findings["reading_count"] = reading_count
    findings["mean_kwh_per_reading"] = total_kwh / reading_count if reading_count else 0.0

    # q2: totals per building type
    by_type = df.groupby("building_type")["energy_kwh"].sum()
    findings["kwh_residential"] = float(by_type.get("Residential", 0.0))
    findings["kwh_commercial"] = float(by_type.get("Commercial", 0.0))
    findings["kwh_industrial"] = float(by_type.get("Industrial", 0.0))

    # q3: quarterly totals (calendar quarters of 2024)
    month = df["reading_date"].dt.month
    quarter = ((month - 1) // 3) + 1
    by_quarter = df.groupby(quarter)["energy_kwh"].sum()
    for q in (1, 2, 3, 4):
        findings["kwh_q%d" % q] = float(by_quarter.get(q, 0.0))

    # q4: half-year totals and percentage change (H2 vs H1)
    h1 = float(df.loc[month <= 6, "energy_kwh"].sum())
    h2 = float(df.loc[month >= 7, "energy_kwh"].sum())
    findings["kwh_h1"] = h1
    findings["kwh_h2"] = h2
    findings["kwh_h2_vs_h1_change_pct"] = (h2 - h1) / h1 * 100.0 if h1 != 0.0 else 0.0

    # q5: commercial load on hot days (temperature >= 25 C, non-missing)
    hot_mask = (df["building_type"] == "Commercial") & temp.notna() & (temp >= 25.0)
    hot = df.loc[hot_mask, "energy_kwh"]
    findings["hot_commercial_reading_count"] = int(hot.shape[0])
    findings["hot_commercial_mean_kwh"] = float(hot.mean()) if hot.shape[0] else 0.0

    # q6: distribution summary
    findings["kwh_median"] = float(energy.median())
    findings["kwh_std"] = float(energy.std(ddof=1))
    findings["temperature_mean"] = float(temp.dropna().mean())
    findings["temperature_missing_count"] = int(temp.isna().sum())
    comm = df.loc[(df["building_type"] == "Commercial") & temp.notna(), ["temperature_c", "energy_kwh"]]
    if comm.shape[0] >= 2:
        corr = float(comm["temperature_c"].corr(comm["energy_kwh"], method="pearson"))
    else:
        corr = 0.0
    findings["commercial_temp_kwh_corr"] = corr

    # q7: tariff and meter usage
    by_tariff = df.groupby("tariff")["energy_kwh"].sum()
    peak = float(by_tariff.get("peak", 0.0))
    off_peak = float(by_tariff.get("off-peak", 0.0))
    findings["kwh_peak"] = peak
    findings["kwh_off_peak"] = off_peak
    findings["peak_kwh_share_pct"] = peak / total_kwh * 100.0 if total_kwh != 0.0 else 0.0
    findings["unique_meter_count"] = int(df["meter_id"].nunique())
    findings["highest_use_meter_kwh"] = float(df.groupby("meter_id")["energy_kwh"].sum().max())

    # guarantee a flat object of finite numbers only
    for key, value in findings.items():
        value = float(value)
        findings[key] = value if np.isfinite(value) else 0.0

    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)


if __name__ == "__main__":
    main()
