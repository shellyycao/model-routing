# 2024 Energy Consumption Analysis Report

This report presents the findings from the 2024 energy consumption analysis, focusing on total and per-building-type usage, quarterly trends, half-year changes, commercial load on hot days, and tariff and meter usage. The analysis reveals significant insights into energy consumption patterns and highlights areas for potential optimization.

## Key findings
- [q1] The total energy consumption for 2024 was 1,207,699.96 kWh, with an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Energy consumption varied significantly by building type, with Industrial (995,362.16 kWh) having the highest consumption, followed by Commercial (196,367.15 kWh) and Residential (15,970.65 kWh).
  - Reported values: kwh_residential=15970.650000000001, kwh_commercial=196367.15000000002, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] The quarterly energy consumption trend shows the highest consumption in Q4 (352,881.81 kWh) and the lowest in Q2 (270,277.36 kWh).
  - Reported values: kwh_q1=319677.67000000004, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81000000006
  - Ranking: Q4, Q1, Q3, Q2
- [q4] Energy consumption increased by 4.71% from the first half (589,955.03 kWh) to the second half (617,744.93 kWh) of the year.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived pct_change(kwh_h2, kwh_h1): 4.710511579162232
- [q5] Commercial buildings consumed an average of 415.29 kWh on hot days (temperature >= 25°C), with 19 such readings recorded.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median energy consumption was 406.8 kWh, with a standard deviation of 913.44 kWh. The mean temperature was 11.61°C, with 62 readings having missing temperature data. The correlation between temperature and energy consumption for commercial buildings was -0.638.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.6376362398654432
- [q7] Energy consumption was nearly evenly split between peak (599,624.07 kWh) and off-peak (608,075.89 kWh) tariffs, with peak consumption accounting for 49.65% of the total. There were 12 unique meters, with the highest usage by a single meter being 252,241.26 kWh.
  - Reported values: kwh_peak=599624.0700000001, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251176, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- The analysis is based on a single year of data, which may not capture long-term trends.
- Missing temperature data for 62 readings could affect the accuracy of temperature-related findings.
- The correlation between temperature and energy consumption for commercial buildings is moderate, indicating other factors may influence consumption.

## Conclusion
The 2024 energy consumption analysis provides valuable insights into consumption patterns and highlights areas for potential optimization. Continued monitoring and analysis are recommended to identify further opportunities for efficiency improvements.
