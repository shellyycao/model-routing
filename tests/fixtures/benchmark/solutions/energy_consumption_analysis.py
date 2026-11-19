# SYNTHETIC_FIXTURE - test solution, not a model output and not a result.
"""pandas analysis for energy_consumption written ONLY from project.json analysis_questions.
Bugs: spearman_not_pearson, hot_gt_not_ge, h2_base"""

import json
import os
import sys

import pandas as pd


def analyze(df: pd.DataFrame, bug: str | None = None) -> dict:
    d = pd.to_datetime(df["reading_date"])
    k = df["energy_kwh"]
    m = {"total_kwh": k.sum(), "reading_count": len(df)}
    m["mean_kwh_per_reading"] = m["total_kwh"] / m["reading_count"]
    for t in ["Residential", "Commercial", "Industrial"]:
        m[f"kwh_{t.lower()}"] = k[df["building_type"] == t].sum()
    for q in range(1, 5):
        m[f"kwh_q{q}"] = k[(d.dt.year == 2024) & (d.dt.quarter == q)].sum()
    m["kwh_h1"] = k[d.dt.month <= 6].sum()
    m["kwh_h2"] = k[d.dt.month >= 7].sum()
    base = m["kwh_h2"] if bug == "h2_base" else m["kwh_h1"]
    m["kwh_h2_vs_h1_change_pct"] = (m["kwh_h2"] - m["kwh_h1"]) / base * 100
    comm = df[(df["building_type"] == "Commercial") & df["temperature_c"].notna()]
    hot = comm[comm["temperature_c"] > 25] if bug == "hot_gt_not_ge" else comm[comm["temperature_c"] >= 25]
    m["hot_commercial_reading_count"] = len(hot)
    m["hot_commercial_mean_kwh"] = hot["energy_kwh"].mean()
    m["kwh_median"] = k.median()
    m["kwh_std"] = k.std()
    m["temperature_mean"] = df["temperature_c"].mean()
    m["temperature_missing_count"] = int(df["temperature_c"].isna().sum())
    if bug == "spearman_not_pearson":
        m["commercial_temp_kwh_corr"] = comm["temperature_c"].rank().corr(comm["energy_kwh"].rank())
    else:
        m["commercial_temp_kwh_corr"] = comm["temperature_c"].corr(comm["energy_kwh"])
    by_tariff = df.groupby("tariff")["energy_kwh"].sum()
    m["kwh_peak"] = by_tariff.get("peak", 0.0)
    m["kwh_off_peak"] = by_tariff.get("off-peak", 0.0)
    m["peak_kwh_share_pct"] = m["kwh_peak"] / m["total_kwh"] * 100
    by_meter = df.groupby("meter_id")["energy_kwh"].sum()
    m["unique_meter_count"] = df["meter_id"].nunique()
    m["highest_use_meter_kwh"] = by_meter.max()
    return {key: float(v) for key, v in m.items()}


def main():
    df = pd.read_csv(os.path.join(os.environ["INPUT_DIR"], "cleaned.csv"))
    with open(os.path.join(os.environ["OUTPUT_DIR"], "findings.json"), "w") as fh:
        json.dump(analyze(df, sys.argv[1] if len(sys.argv) > 1 else None), fh, indent=2)


if __name__ == "__main__":
    main()
