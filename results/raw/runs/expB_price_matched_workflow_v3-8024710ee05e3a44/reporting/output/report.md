# 2024 Smart-Meter Electricity Consumption: Verified Findings Report

Analysis of 1,428 cleaned smart-meter readings from 12 meters shows total 2024 consumption of 1,207,699.96 kWh. Industrial sites dominate usage (995,362.16 kWh, about 82.4%), while Residential accounts for just 1.3%. Demand was lowest in Q3 (264,863.12 kWh) and highest in Q4 (352,881.81 kWh); second-half consumption rose 4.71% versus the first half. Peak and off-peak tariffs split almost evenly (49.65% peak). Commercial consumption correlates strongly negatively with temperature (-0.64), and hot-day (>=25 C) commercial load averaged a modest 415.29 kWh across 19 readings.

## Key findings
- [q1] Total 2024 electricity consumption was 1,207,699.96 kWh across 1,428 readings, an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed 995,362.16 kWh - about 82.4% of total consumption - far above Commercial (196,367.15 kWh, about 16.3%) and Residential (15,970.65 kWh, about 1.3%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Quarterly consumption was highest in Q4 (352,881.81 kWh), followed by Q1 (319,677.67 kWh), Q2 (270,277.36 kWh) and Q3 (264,863.12 kWh); the gap between the highest and lowest quarters is 88,018.69 kWh.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
  - Derived difference(kwh_q4, kwh_q3): 88018.69
- [q4] Consumption increased in the second half of the year: H2 (July-December) totalled 617,744.93 kWh versus 589,955.03 kWh in H1 (January-June), a rise of 27,789.90 kWh, or 4.71%.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature >= 25 C), Commercial sites logged 19 readings averaging 415.29 kWh, roughly half (0.49x) the overall mean of 845.73 kWh per reading.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
  - Derived ratio(hot_commercial_mean_kwh, mean_kwh_per_reading): 0.49
- [q6] Consumption is strongly right-skewed: the median reading is 406.8 kWh versus a mean of 845.73 kWh, with a large standard deviation of 913.44 kWh. Mean temperature was 11.61 C, with temperature missing for 62 readings (about 4.3% of all readings). Commercial consumption shows a strong negative Pearson correlation with temperature (-0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
  - Derived share(temperature_missing_count, reading_count): 4.3
- [q7] Off-peak consumption (608,075.89 kWh) slightly exceeded peak consumption (599,624.07 kWh) by 8,451.82 kWh, with peak tariffs accounting for 49.65% of total energy. Twelve unique meters were recorded; the highest-use single meter consumed 252,241.26 kWh, about 20.9% of total consumption.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak
  - Derived difference(kwh_off_peak, kwh_peak): 8451.82
  - Derived share(highest_use_meter_kwh, total_kwh): 20.9

## Limitations
- Temperature is missing for 62 readings; those records are excluded from all temperature-based analyses, including the correlation and hot-day results.
- Only 12 unique meters are covered, and Residential consumption is very small (15,970.65 kWh), so building-type comparisons reflect an uneven meter mix rather than a representative portfolio.
- The strong negative Commercial temperature-consumption correlation (-0.64) is associational, not causal; seasonality, occupancy and operating schedules may confound it.
- The hot-day Commercial estimate rests on only 19 qualifying readings, so it is sensitive to small-sample variation.
- Data cover a single year (2024), so the quarterly and half-year patterns cannot be validated against other years.

## Conclusion
2024 electricity demand was concentrated in Industrial sites, tilted toward Q4, and rose modestly in the second half (+4.71%). Stakeholders should prioritise Industrial efficiency programmes, investigate the counterintuitive negative temperature-consumption relationship in Commercial buildings, and treat Residential and hot-day results cautiously given the small underlying samples.
