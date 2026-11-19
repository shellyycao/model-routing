# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 smart-meter readings across 2024 shows total consumption of 1,207,700 kWh at a mean of 846 kWh per reading. Industrial sites dominate usage, accounting for over 82% of total energy. Consumption dipped mid-year before recovering strongly in Q4, and the second half of the year outpaced the first by 4.7%. Tariff split is near-even, and a moderate negative correlation between temperature and commercial energy use on hot days warrants further investigation.

## Key findings
- [q1] Across 1,428 readings, total electricity consumption reached 1,207,700 kWh, yielding a mean of approximately 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed the most energy at 995,362 kWh (82.4% of total), followed by Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Quarterly consumption peaked in Q4 at 352,882 kWh, followed by Q1 at 319,678 kWh. Mid-year quarters were lower: Q2 at 270,277 kWh and Q3 at 264,863 kWh, indicating a U-shaped seasonal pattern.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh), representing an increase of 4.7% from H1 to H2.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), 19 commercial readings were recorded with a mean consumption of 415.3 kWh per reading, suggesting elevated but moderate load under high-temperature conditions.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption was 406.8 kWh with a sample standard deviation of 913.4 kWh, indicating high variability. The mean recorded temperature was 11.6 °C, with 62 readings missing temperature data. Among commercial readings with valid temperatures, the Pearson correlation between temperature and energy was -0.64, suggesting that commercial sites use less electricity on warmer days.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff consumption (608,076 kWh) marginally exceeded peak tariff consumption (599,624 kWh), with peak accounting for 49.7% of total energy. Across 12 distinct meters, the highest-consuming single meter recorded 252,241 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings have missing temperature data, which may bias temperature-based analyses including the hot-day commercial filter and the temperature-energy correlation.
- The hot-day commercial subset contains only 19 readings, making the mean and any derived trends statistically fragile.
- With only 12 distinct meters, meter-level conclusions may not generalise to a broader portfolio.
- The dataset covers a single calendar year (2024); multi-year comparisons are not possible from this export alone.
- Residential consumption is very low relative to other segments, which may reflect under-representation of residential meters rather than actual low usage.

## Conclusion
Industrial sites drive the vast majority of electricity consumption, and a clear U-shaped seasonal pattern—lower mid-year, higher at year-ends—warrants attention for capacity planning. The modest H2 increase of 4.7% and the near-even peak/off-peak split suggest stable tariff utilisation. The negative temperature-commercial energy correlation and the small hot-day sample size should be investigated further with richer data before drawing operational conclusions.
