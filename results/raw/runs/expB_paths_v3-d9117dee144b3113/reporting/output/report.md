# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 cleaned smart-meter readings for 2024 shows total consumption of 1,207,700 kWh across 12 meters. Industrial buildings dominate usage, accounting for over 82% of all consumption. Consumption dipped mid-year before recovering strongly in Q4, and the second half of the year was 4.7% higher than the first. Peak and off-peak tariffs are nearly evenly split. Commercial buildings show a moderate negative correlation between temperature and energy use on hot days.

## Key findings
- [q1] The dataset contains 1,428 readings with a combined consumption of 1,207,700 kWh and a mean of 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed the most energy at 995,362 kWh (82.4% of total), followed by Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Quarterly consumption peaked in Q4 (352,882 kWh), followed by Q1 (319,678 kWh), Q2 (270,277 kWh), and Q3 (264,863 kWh), indicating a mid-year trough and a strong year-end recovery.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh) by 4.7%, representing an increase of approximately 27,790 kWh.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), 19 commercial readings were recorded with a mean consumption of 415.3 kWh per reading.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption across all readings is 406.8 kWh with a sample standard deviation of 913.4 kWh, indicating high variability. The mean recorded temperature is 11.6 °C, with 62 readings missing temperature data. For commercial buildings, the Pearson correlation between temperature and consumption is -0.64, suggesting that higher temperatures are associated with lower commercial energy use.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff consumption (608,076 kWh) slightly exceeds peak tariff consumption (599,624 kWh); peak usage accounts for 49.7% of total consumption. Across 12 distinct meters, the highest-consuming single meter recorded 252,241 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings are missing temperature data, which may introduce bias into temperature-based analyses, particularly the commercial correlation and hot-day filtering.
- The residential segment contains only 15,971 kWh across very few readings, making building-type comparisons unbalanced and residential insights less reliable.
- With only 12 distinct meters, meter-level findings (e.g., highest-use meter) may not generalise to a broader portfolio.
- Hot-day commercial analysis is based on just 19 readings, limiting statistical confidence in the mean consumption estimate.
- The analysis covers a single calendar year (2024); year-on-year trend comparisons are not possible without prior-year data.

## Conclusion
Industrial consumption dominates the portfolio and should be the primary focus for efficiency initiatives. The Q4 surge and H2 uplift of 4.7% warrant investigation into seasonal or operational drivers. The near-equal peak/off-peak split suggests limited tariff optimisation opportunity, though the highest single-meter usage of 252,241 kWh merits targeted review. Addressing missing temperature records would strengthen future thermal-load modelling.
