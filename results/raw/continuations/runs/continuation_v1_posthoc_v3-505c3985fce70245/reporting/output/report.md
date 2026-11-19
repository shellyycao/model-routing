# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 smart-meter readings across 2024 reveals total consumption of 1,207,700 kWh. Industrial buildings dominate usage, Q4 was the highest-consumption quarter, and the second half of the year saw a modest 4.7% increase over the first. Tariff split is near-even, and a negative temperature–commercial-load correlation suggests cooling is not a primary commercial driver.

## Key findings
- [q1] Across all 1,428 readings in 2024, total electricity consumption reached 1,207,700 kWh, with a mean of 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed 995,362 kWh (82.4% of total), far exceeding Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%).
  - Reported values: kwh_residential=15970.650000000001, kwh_commercial=196367.15000000002, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Q4 was the highest-consumption quarter at 352,882 kWh, followed by Q1 (319,678 kWh), Q2 (270,277 kWh), and Q3 (264,863 kWh), indicating elevated demand at the year's start and end.
  - Reported values: kwh_q1=319677.67000000004, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81000000006
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh) by 4.7%, representing an increase of approximately 27,790 kWh.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), 19 commercial readings were recorded with a mean consumption of 415.3 kWh per reading.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median reading was 406.8 kWh with a standard deviation of 913.4 kWh, indicating high variability. Mean temperature across valid readings was 11.6 °C; 62 readings had missing temperature data. The Pearson correlation between temperature and commercial energy use was −0.64, suggesting higher temperatures are associated with lower commercial consumption.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.6376362398654432
- [q7] Off-peak tariff accounted for 608,076 kWh versus 599,624 kWh at peak (49.7% of total), an almost equal split. Across 12 distinct meters, the highest single-meter consumption was 252,241 kWh.
  - Reported values: kwh_peak=599624.0700000001, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251176, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings have missing temperature_c values, which may introduce bias into temperature-based analyses and the commercial correlation estimate.
- Only 19 hot-day commercial readings (temperature ≥ 25 °C) were available, making the hot-day commercial load estimate statistically fragile.
- The dataset covers only 12 distinct meters, limiting generalisability across a broader meter population.
- Building-type classification is taken as given from the cleaned export; any misclassification in the source data would propagate into all segment-level findings.
- The analysis covers a single calendar year (2024), so year-on-year trend comparisons are not possible.

## Conclusion
Industrial sites drive the overwhelming majority of electricity demand. Consumption peaks in Q4 and Q1, consistent with heating-season patterns, and the second half of 2024 saw a modest 4.7% uplift over the first. The near-even peak/off-peak tariff split offers limited scope for tariff-shift savings without behavioural change. The negative temperature–commercial correlation warrants further investigation to understand whether mild weather reduces commercial operating hours or equipment use.
