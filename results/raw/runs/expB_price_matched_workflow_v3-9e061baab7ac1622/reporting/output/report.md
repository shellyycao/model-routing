# 2024 Smart-Meter Electricity Consumption — Verified Findings Report

The cleaned 2024 export contains 1,428 smart-meter readings totalling 1,207,699.96 kWh (average 845.73 kWh per reading). Industrial sites dominate consumption, accounting for 995,362.16 kWh (about 82.4% of the total). Demand rose in the second half of the year: H2 exceeded H1 by 4.71%, and Q4 was the strongest quarter while Q3 was the weakest. Peak and off-peak usage are nearly balanced, with a 49.65% peak share. Commercial consumption on hot days (>=25°C, 19 readings) averaged 415.29 kWh, and commercial usage shows a strong negative correlation (-0.64) with temperature. Twelve distinct meters are present; the busiest single meter recorded 252,241.26 kWh.

## Key findings
- [q1] The cleaned 2024 dataset holds 1,428 readings totalling 1,207,699.96 kWh, an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
  - Direction: not_applicable
- [q2] Industrial buildings consumed 995,362.16 kWh (about 82.4% of total consumption), far ahead of Commercial at 196,367.15 kWh and Residential at 15,970.65 kWh.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Direction: not_applicable
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
- [q3] Quarterly 2024 totals were Q4 352,881.81 kWh (highest), Q1 319,677.67 kWh, Q2 270,277.36 kWh and Q3 264,863.12 kWh (lowest); Q4 exceeded Q3 by 88,018.69 kWh, indicating a year-end rebound after a mid-year dip.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Direction: not_applicable
  - Ranking: Q4, Q1, Q2, Q3
  - Derived difference(kwh_q4, kwh_q3): 88018.69
- [q4] Second-half (Jul-Dec) consumption of 617,744.93 kWh was 27,789.90 kWh higher than the first half's 589,955.03 kWh, a 4.71% increase.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] There were 19 Commercial readings with a non-missing temperature of at least 25°C, and their mean consumption was 415.29 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
  - Direction: not_applicable
- [q6] Consumption per reading is highly variable: median 406.8 kWh with a sample standard deviation of 913.44 kWh. Mean temperature was 11.61°C, with 62 readings missing temperature. Commercial consumption correlates strongly and negatively with temperature (-0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
  - Direction: not_applicable
- [q7] Off-peak consumption (608,075.89 kWh, about 50.35% of total) slightly exceeded peak consumption (599,624.07 kWh), giving a 49.65% peak share. The network comprises 12 distinct meters; the highest-use single meter totalled 252,241.26 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Direction: not_applicable
  - Ranking: off-peak, peak
  - Derived share(kwh_off_peak, total_kwh): 50.35

## Limitations
- 62 readings lack temperature data, narrowing the temperature-based analyses; the hot-day commercial subset is small (19 readings), so its mean is sensitive to outliers.
- The commercial temperature-consumption correlation (-0.64) covers only Commercial readings and is associational, not causal.
- Consumption is highly skewed (median 406.8 kWh vs standard deviation 913.44 kWh), so the mean of 845.73 kWh per reading is pulled up by large industrial readings.
- Findings reflect only the cleaned 2024 export (1,428 readings, 12 meters); no weather normalisation, occupancy adjustment or tariff-rate cost analysis was performed.

## Conclusion
2024 consumption totalled 1,207,699.96 kWh, driven overwhelmingly by Industrial sites (82.4% share). Demand dipped mid-year (Q2-Q3) before peaking in Q4, leaving H2 4.71% above H1. Peak and off-peak usage are almost balanced (49.65% peak), and commercial load is lower on hotter days. Planning should prioritise industrial efficiency and Q4 capacity readiness.
