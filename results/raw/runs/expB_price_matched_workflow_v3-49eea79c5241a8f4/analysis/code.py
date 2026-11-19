import json
import math
import os

import pandas as pd


def finite_number(value, fallback=0.0):
    """Return value as a plain finite Python float (fallback if NaN/inf)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return float(fallback)
    if not math.isfinite(v):
        return float(fallback)
    return v


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(
        input_path,
        dtype={
            "reading_id": str,
            "meter_id": str,
            "building_type": str,
            "tariff": str,
        },
    )
    df["reading_date"] = pd.to_datetime(df["reading_date"], format="%Y-%m-%d", errors="coerce")
    df["energy_kwh"] = pd.to_numeric(df["energy_kwh"], errors="coerce")
    df["temperature_c"] = pd.to_numeric(df["temperature_c"], errors="coerce")

    findings = {}

    # q1: overall aggregation
    total_kwh = df["energy_kwh"].sum()
    reading_count = int(len(df))
    findings["total_kwh"] = finite_number(total_kwh)
    findings["reading_count"] = reading_count
    findings["mean_kwh_per_reading"] = (
        finite_number(total_kwh / reading_count) if reading_count > 0 else 0.0
    )

    # q2: totals per building type
    by_type = df.groupby("building_type")["energy_kwh"].sum()
    findings["kwh_residential"] = finite_number(by_type.get("Residential", 0.0))
    findings["kwh_commercial"] = finite_number(by_type.get("Commercial", 0.0))
    findings["kwh_industrial"] = finite_number(by_type.get("Industrial", 0.0))

    # q3: quarterly trend (calendar quarters of 2024)
    month = df["reading_date"].dt.month
    quarter = ((month - 1) // 3) + 1
    by_quarter = df.groupby(quarter)["energy_kwh"].sum()
    for q in (1, 2, 3, 4):
        findings[f"kwh_q{q}"] = finite_number(by_quarter.get(q, 0.0))

    # q4: half-year totals and percentage change (H2 vs H1)
    kwh_h1 = df.loc[month <= 6, "energy_kwh"].sum()
    kwh_h2 = df.loc[month >= 7, "energy_kwh"].sum()
    findings["kwh_h1"] = finite_number(kwh_h1)
    findings["kwh_h2"] = finite_number(kwh_h2)
    findings["kwh_h2_vs_h1_change_pct"] = (
        finite_number((kwh_h2 - kwh_h1) / kwh_h1 * 100.0) if kwh_h1 else 0.0
    )

    # q5: commercial readings on hot days (temperature_c >= 25, non-missing)
    hot_commercial = df[
        (df["building_type"] == "Commercial")
        & (df["temperature_c"].notna())
        & (df["temperature_c"] >= 25.0)
    ]
    findings["hot_commercial_reading_count"] = int(len(hot_commercial))
    findings["hot_commercial_mean_kwh"] = (
        finite_number(hot_commercial["energy_kwh"].mean()) if len(hot_commercial) > 0 else 0.0
    )

    # q6: distribution summary
    findings["kwh_median"] = finite_number(df["energy_kwh"].median())
    findings["kwh_std"] = finite_number(df["energy_kwh"].std(ddof=1))
    temp_nonmissing = df["temperature_c"].dropna()
    findings["temperature_mean"] = (
        finite_number(temp_nonmissing.mean()) if len(temp_nonmissing) > 0 else 0.0
    )
    findings["temperature_missing_count"] = int(df["temperature_c"].isna().sum())
    commercial_with_temp = df[
        (df["building_type"] == "Commercial") & (df["temperature_c"].notna())
    ]
    if (
        len(commercial_with_temp) >= 2
        and commercial_with_temp["temperature_c"].std(ddof=1) > 0
        and commercial_with_temp["energy_kwh"].std(ddof=1) > 0
    ):
        corr = commercial_with_temp["temperature_c"].corr(
            commercial_with_temp["energy_kwh"], method="pearson"
        )
        findings["commercial_temp_kwh_corr"] = finite_number(corr)
    else:
        findings["commercial_temp_kwh_corr"] = 0.0

    # q7: tariff and meter usage
    by_tariff = df.groupby("tariff")["energy_kwh"].sum()
    kwh_peak = by_tariff.get("peak", 0.0)
    kwh_off_peak = by_tariff.get("off-peak", 0.0)
    findings["kwh_peak"] = finite_number(kwh_peak)
    findings["kwh_off_peak"] = finite_number(kwh_off_peak)
    findings["peak_kwh_share_pct"] = (
        finite_number(kwh_peak / total_kwh * 100.0) if total_kwh else 0.0
    )
    findings["unique_meter_count"] = int(df["meter_id"].nunique())
    by_meter = df.groupby("meter_id")["energy_kwh"].sum()
    findings["highest_use_meter_kwh"] = (
        finite_number(by_meter.max()) if len(by_meter) > 0 else 0.0
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f)


if __name__ == "__main__":
    main()
