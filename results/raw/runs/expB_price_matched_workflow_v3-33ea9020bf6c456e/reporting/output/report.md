# 2024 Smart-Meter Electricity Consumption: Verified Findings for Stakeholders

Twelve smart meters recorded 1,428 readings in 2024, totalling 1,207,699.96 kWh. Industrial buildings drove demand with 995,362.16 kWh (82.42% of the total), versus 16.26% Commercial and 1.32% Residential. Consumption bottomed in Q3 (264,863.12 kWh) and peaked in Q4 (352,881.81 kWh); second-half usage rose 4.71% over the first half. Peak and off-peak tariffs split almost evenly (49.65% peak). Commercial usage correlates strongly and negatively with temperature (r = -0.64), and a single meter accounts for 20.89% of total consumption.

## Key findings
- [q1] The cleaned 2024 dataset holds 1,428 smart-meter readings totalling 1,207,699.96 kWh, an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial sites consumed 995,362.16 kWh (82.42% of total usage), dwarfing Commercial (196,367.15 kWh; 16.26%) and Residential (15,970.65 kWh; 1.32%); Industrial alone accounts for over four-fifths of demand.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.42
  - Derived share(kwh_commercial, total_kwh): 16.26
  - Derived share(kwh_residential, total_kwh): 1.32
- [q3] Quarterly demand was highest in Q4 (352,881.81 kWh), followed by Q1 (319,677.67 kWh), Q2 (270,277.36 kWh) and Q3 (264,863.12 kWh); the peak quarter exceeded the trough by 33.23%.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
  - Derived pct_change(kwh_q4, kwh_q3): 33.23
- [q4] Consumption increased from 589,955.03 kWh in January-June to 617,744.93 kWh in July-December, a rise of 27,789.9 kWh, or 4.71%.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] Nineteen Commercial readings with temperatures of at least 25 °C averaged 415.29 kWh, about 0.49× the overall per-reading mean of 845.73 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
  - Derived ratio(hot_commercial_mean_kwh, mean_kwh_per_reading): 0.49
- [q6] Usage is strongly right-skewed: the mean (845.73 kWh) is 2.08× the median (406.8 kWh), with a standard deviation of 913.44 kWh. Temperature averaged 11.61 °C across available readings, while 62 readings (4.34% of all rows) lack temperature values. For Commercial buildings, consumption shows a strong negative correlation with temperature (r = -0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
  - Derived ratio(mean_kwh_per_reading, kwh_median): 2.08
  - Derived share(temperature_missing_count, reading_count): 4.34
- [q7] Off-peak consumption (608,075.89 kWh; 50.35% share) slightly exceeded peak consumption (599,624.07 kWh; 49.65%) by 8,451.82 kWh. Twelve unique meters appear in the data; the highest-use meter totalled 252,241.26 kWh, 20.89% of all consumption.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak
  - Derived share(kwh_off_peak, total_kwh): 50.35
  - Derived difference(kwh_off_peak, kwh_peak): 8451.82
  - Derived share(highest_use_meter_kwh, total_kwh): 20.89

## Limitations
- Temperature data are missing for 62 readings (4.34%), so the hot-day and correlation analyses are computed on a reduced subset of the data.
- Only 19 Commercial readings qualify as hot-day observations, a small sample that makes the 415.29 kWh average sensitive to outliers.
- The Commercial temperature-consumption correlation (r = -0.64) is associational, not causal; it may reflect seasonal operating patterns rather than a direct temperature response.
- Just 12 meters are covered, with Industrial sites contributing 82.42% of consumption and Residential only 1.32%, so results may not generalise to a broader or more balanced portfolio.

## Conclusion
2024 electricity demand was concentrated in Industrial sites (82.42% of 1,207,699.96 kWh) and in the final quarter, with second-half consumption up 4.71% on the first half. The near-even peak/off-peak split (49.65% peak) suggests limited short-term gains from tariff load-shifting. Recommended priorities: audit the single meter responsible for 20.89% of total usage, target Q4 efficiency measures at Industrial sites, and improve temperature data coverage before acting on the strong negative Commercial temperature-usage correlation.
