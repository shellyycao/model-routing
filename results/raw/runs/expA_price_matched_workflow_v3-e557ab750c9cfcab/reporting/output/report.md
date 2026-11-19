# 2024 Smart-Meter Electricity Consumption: Verified Findings for Business Stakeholders

This report summarises verified findings from the cleaned 2024 smart-meter export (1,428 readings). Total consumption was 1,207,699.96 kWh, averaging 845.73 kWh per reading. Industrial buildings dominate demand (995,362.16 kWh), far ahead of commercial (196,367.15 kWh) and residential (15,970.65 kWh). Usage was highest in Q4 (352,881.81 kWh) and lowest in Q3 (264,863.12 kWh), and second-half consumption was 4.71% above the first half. Peak tariffs account for 49.65% of energy, and commercial consumption correlates moderately negatively with temperature (r = -0.64).

## Key findings
- [q1] Total 2024 electricity consumption was 1,207,699.96 kWh across 1,428 smart-meter readings, an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.728263
- [q2] Industrial buildings account for the vast majority of consumption at 995,362.16 kWh (82.4% of total), followed by Commercial at 196,367.15 kWh (16.3%) and Residential at 15,970.65 kWh (1.3%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Quarterly consumption ranks Q4 highest (352,881.81 kWh), then Q1 (319,677.67 kWh), Q2 (270,277.36 kWh) and Q3 lowest (264,863.12 kWh); Q4 exceeded Q3 by 88,018.69 kWh, a strong year-end rebound after a mid-year dip.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
  - Derived difference(kwh_q4, kwh_q3): 88018.69
- [q4] Second-half (July-December) consumption of 617,744.93 kWh was 4.71% higher than first-half (January-June) consumption of 589,955.03 kWh, an absolute increase of 27,789.90 kWh.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710512
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] Commercial buildings logged 19 readings on hot days (temperature at or above 25°C), averaging 415.29 kWh per reading; given the small count, this mean should be interpreted cautiously.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.293684
- [q6] Consumption per reading is highly variable (median 406.8 kWh; sample standard deviation 913.44 kWh), indicating a skewed distribution. Mean temperature was 11.61°C, with 62 readings missing temperature. Commercial consumption correlates moderately negatively with temperature (Pearson r = -0.64): usage tended to be lower on warmer days.
  - Reported values: kwh_median=406.8, kwh_std=913.438516, temperature_mean=11.612299, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636
- [q7] Off-peak consumption (608,075.89 kWh) slightly exceeded peak consumption (599,624.07 kWh), with peak energy representing 49.65% of the total. Twelve distinct meters were active, and the highest-use single meter consumed 252,241.26 kWh (20.9% of total), showing concentrated demand.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.650086, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak
  - Derived share(highest_use_meter_kwh, total_kwh): 20.9

## Limitations
- Temperature is missing for 62 readings; all temperature-based results (hot-day load, correlation) exclude them.
- The hot-day commercial finding rests on only 19 readings, so its mean is statistically fragile.
- The consumption distribution is strongly skewed (median 406.8 kWh vs standard deviation 913.44 kWh), so mean-based metrics are sensitive to a few very large industrial readings.
- The negative commercial temperature correlation (-0.64) is associational only; operating schedules or holidays may confound it.
- Only one year of data and 12 meters were analysed, and a single meter contributes 252,241.26 kWh, limiting generalisability.

## Conclusion
Verified 2024 results show an industrially dominated load (995,362.16 kWh), a Q4 demand peak, and modest second-half growth of 4.71%. Peak and off-peak energy are nearly balanced (49.65% peak), leaving room for tariff optimisation. Recommended focus: industrial efficiency programmes, engagement with the highest-use meter (252,241.26 kWh), and further study of the commercial temperature response (r = -0.64) with more complete weather data.
