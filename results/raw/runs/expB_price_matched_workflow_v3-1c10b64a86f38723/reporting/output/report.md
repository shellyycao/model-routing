# 2024 Smart-Meter Electricity Consumption — Verified Findings for Business Stakeholders

In 2024 the metered portfolio consumed 1,207,699.96 kWh across 1,428 readings from 12 meters, averaging 845.73 kWh per reading. Industrial buildings dominate consumption (995,362.16 kWh); demand peaks in the winter quarters (Q4: 352,881.81 kWh; Q3 lowest: 264,863.12 kWh), and second-half usage was 4.71% higher than the first half. Peak and off-peak tariffs are almost evenly split (peak share 49.65%), while commercial consumption correlates negatively with temperature (r = -0.64).

## Key findings
- [q1] The cleaned 2024 dataset contains 1,428 smart-meter readings totalling 1,207,699.96 kWh, an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings dominate consumption with 995,362.16 kWh (82.42% of the annual total), far ahead of Commercial at 196,367.15 kWh (16.26%) and Residential at 15,970.65 kWh (1.32%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16, total_kwh=1207699.96
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.42
  - Derived share(kwh_commercial, total_kwh): 16.26
  - Derived share(kwh_residential, total_kwh): 1.32
- [q3] Consumption followed a winter-peaking pattern: Q4 was the highest quarter (352,881.81 kWh), followed by Q1 (319,677.67 kWh), Q2 (270,277.36 kWh) and Q3 as the low point (264,863.12 kWh), before a 33.23% rebound from Q3 to Q4.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
  - Derived pct_change(kwh_q4, kwh_q3): 33.23
- [q4] Second-half consumption (617,744.93 kWh) increased by 4.71% over the first half (589,955.03 kWh), a gain of 27,789.90 kWh.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] Only 19 Commercial readings met the hot-day criterion (temperature >= 25 C); their average consumption was 415.29 kWh per reading.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] Per-reading consumption is strongly right-skewed: the mean of 845.73 kWh is about 2.08x the median of 406.8 kWh, with a large standard deviation of 913.44 kWh. Mean temperature was 11.61 C, with 62 readings missing temperature; Commercial consumption correlates negatively with temperature (r = -0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442, mean_kwh_per_reading=845.7282633053221
  - Derived ratio(mean_kwh_per_reading, kwh_median): 2.08
- [q7] Tariff usage is almost evenly split: off-peak 608,075.89 kWh versus peak 599,624.07 kWh (peak share 49.65%), a difference of 8,451.82 kWh. Twelve unique meters were active, and the highest-use meter alone consumed 252,241.26 kWh, 20.89% of the annual total.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26, total_kwh=1207699.96
  - Ranking: off-peak, peak
  - Derived difference(kwh_off_peak, kwh_peak): 8451.82
  - Derived share(highest_use_meter_kwh, total_kwh): 20.89

## Limitations
- Temperature is missing for 62 of the 1,428 readings, which weakens all temperature-based analyses.
- Only 19 Commercial readings qualify as hot-day (>= 25 C), so the hot-day mean of 415.29 kWh rests on a very small sample.
- The data cover a single year; the 4.71% second-half increase and the quarterly pattern may reflect seasonality rather than underlying growth, with no prior-year baseline for comparison.
- Correlation is not causation: the negative Commercial temperature-consumption correlation (r = -0.64) likely reflects heating-driven demand and other unmeasured confounders.
- Totals are not normalised for building size or count, so the small Residential total (15,970.65 kWh) may simply reflect few residential meters rather than efficiency.

## Conclusion
The 2024 data show an industrially dominated, winter-peaking load with nearly balanced peak and off-peak tariff usage and moderate growth from the first to the second half of the year. Recommended actions: target efficiency measures at industrial sites and the highest-use meter (252,241.26 kWh), investigate why Commercial consumption rises as temperature falls, and improve temperature data capture before deepening the hot-day analysis.
