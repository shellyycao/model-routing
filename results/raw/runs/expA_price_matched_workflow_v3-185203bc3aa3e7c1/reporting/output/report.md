# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 smart-meter readings for 2024 shows total consumption of 1,207,700 kWh across 12 meters. Industrial sites dominate usage, Q4 was the highest-consumption quarter, and the second half of the year grew 4.7% over the first. Peak and off-peak tariffs are nearly balanced, and commercial buildings show a moderate negative correlation between temperature and consumption.

## Key findings
- [q1] Across all 1,428 readings, total electricity consumption reached 1,207,700 kWh, yielding a mean of approximately 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.728263
- [q2] Industrial buildings consumed the most energy at 995,362 kWh (82.4% of total), followed by Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Q4 (Oct–Dec) was the highest-consumption quarter at 352,882 kWh, followed by Q1 (319,678 kWh), Q2 (270,277 kWh), and Q3 (264,863 kWh), indicating a mid-year trough with a strong year-end rebound.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh) by 4.7%, representing an increase of approximately 27,790 kWh.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710512
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), 19 commercial readings were recorded with a mean consumption of 415.3 kWh per reading, suggesting moderate load levels under high-temperature conditions.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.293684
- [q6] The median consumption across all readings is 406.8 kWh with a standard deviation of 913.4 kWh, indicating high variability. The mean recorded temperature is 11.6 °C, with 62 readings missing temperature data. Commercial buildings show a moderate negative Pearson correlation of −0.64 between temperature and consumption, suggesting higher commercial usage in cooler periods.
  - Reported values: kwh_median=406.8, kwh_std=913.438516, temperature_mean=11.612299, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636
- [q7] Off-peak tariff consumption (608,076 kWh) slightly exceeded peak tariff consumption (599,624 kWh), with peak accounting for 49.7% of total usage. Across 12 distinct meters, the highest single-meter total reached 252,241 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.650086, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings (4.3% of the dataset) are missing temperature data, which may introduce bias in temperature-related analyses including the commercial correlation and hot-day filtering.
- The hot-day commercial sample is small (19 readings), limiting the statistical reliability of the hot-day mean consumption estimate.
- Only 12 distinct meters are present; findings may not generalise to a broader meter population or different geographic regions.
- The dataset covers a single year (2024), so seasonal patterns and half-year trends cannot be validated against prior-year baselines.
- Residential consumption is very low relative to other building types, which may reflect under-representation of residential meters rather than true consumption differences.

## Conclusion
Industrial sites drive the vast majority of 2024 electricity consumption. Demand dipped in mid-year before recovering strongly in Q4, and the second half outpaced the first by 4.7%. Peak and off-peak tariff loads are nearly equal, offering limited arbitrage opportunity. The negative temperature–consumption correlation in commercial buildings warrants further investigation into heating-driven demand. Addressing missing temperature records and expanding the meter sample would strengthen future analyses.
