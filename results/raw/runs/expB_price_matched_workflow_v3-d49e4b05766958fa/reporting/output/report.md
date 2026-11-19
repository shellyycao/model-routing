# 2024 Smart-Meter Electricity Consumption: Verified Findings Report

The cleaned 2024 dataset contains 1,428 readings totalling 1,207,699.96 kWh (mean 845.73 kWh per reading). Industrial sites dominate at 995,362.16 kWh, 82.4% of all consumption. Usage dipped through mid-year to a Q3 low, then rebounded to a Q4 peak; second-half consumption was 4.71% higher than the first half. Peak and off-peak tariffs are almost evenly split (49.65% peak), 12 meters reported, and Commercial consumption shows a moderate negative correlation with temperature (r = -0.64).

## Key findings
- [q1] The fleet recorded 1,428 valid readings in 2024, totalling 1,207,699.96 kWh — an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial sites consumed 995,362.16 kWh (82.4% of total), far ahead of Commercial at 196,367.15 kWh (16.3%) and Residential at 15,970.65 kWh (1.3%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Quarterly demand fell from 319,677.67 kWh in Q1 to 270,277.36 kWh in Q2 and a low of 264,863.12 kWh in Q3, then surged to a year-high 352,881.81 kWh in Q4 — 88,018.69 kWh (33.2%) above Q3.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
  - Derived difference(kwh_q4, kwh_q3): 88018.69
  - Derived pct_change(kwh_q4, kwh_q3): 33.2
- [q4] Consumption rose from 589,955.03 kWh in January–June to 617,744.93 kWh in July–December, an increase of 27,789.90 kWh (4.71%).
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] Only 19 Commercial readings occurred at temperatures of 25 °C or higher; they averaged 415.29 kWh each.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] Per-reading consumption varies widely: median 406.80 kWh with a standard deviation of 913.44 kWh, and very large Industrial readings pull the mean to 845.73 kWh (2.08x the median). Mean temperature was 11.61 °C, with 62 readings missing temperature. For Commercial readings, consumption correlates moderately negatively with temperature (r = -0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
  - Derived ratio(mean_kwh_per_reading, kwh_median): 2.08
- [q7] Tariff use is nearly balanced: 599,624.07 kWh on peak (49.65% of total) versus 608,075.89 kWh off-peak, a gap of just 8,451.82 kWh. Twelve distinct meters reported; the highest-use meter alone consumed 252,241.26 kWh (20.9% of annual total).
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak
  - Derived difference(kwh_off_peak, kwh_peak): 8451.82
  - Derived share(highest_use_meter_kwh, total_kwh): 20.9

## Limitations
- Temperature is missing for 62 of the 1,428 readings, shrinking the sample for all temperature-based analyses.
- The hot-day Commercial average rests on only 19 readings, so it is sensitive to outliers.
- Fleet-wide totals and averages are dominated by Industrial sites and do not reflect typical Residential or Commercial usage.
- Data cover a single year (2024) and only 12 meters; seasonal patterns may not generalise, and the negative Commercial temperature–consumption correlation is associational, not causal.

## Conclusion
2024 electricity demand is overwhelmingly industrial, soft mid-year with a strong Q4 rebound and a modest 4.71% H2-over-H1 rise. Stakeholders should prioritise Industrial efficiency and Q4 capacity planning, monitor the single meter driving 20.9% of annual use, and treat the balanced peak/off-peak split as an opportunity for load-shifting savings.
