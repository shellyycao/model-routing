# 2024 Smart-Meter Electricity Consumption: Verified Findings Report

Verified 2024 electricity consumption totalled 1,207,699.96 kWh across 1,428 readings (mean 845.73 kWh per reading). Industrial sites dominate at 995,362.16 kWh (82.42% of total), followed by Commercial (196,367.15 kWh) and Residential (15,970.65 kWh). Demand was U-shaped, peaking in Q4 (352,881.81 kWh) and bottoming in Q3 (264,863.12 kWh); second-half consumption rose 4.71% over the first half. Peak and off-peak tariffs split almost evenly (49.65% peak). Commercial use averaged 415.29 kWh across 19 hot-day readings and correlates negatively with temperature (-0.64). Twelve meters were active; the top meter used 252,241.26 kWh (20.89% of total).

## Key findings
- [q1] Total verified 2024 consumption was 1,207,699.96 kWh across 1,428 smart-meter readings, an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings dominate electricity use with 995,362.16 kWh — 82.42% of total consumption — far ahead of Commercial (196,367.15 kWh) and Residential (15,970.65 kWh).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16, total_kwh=1207699.96
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.42
- [q3] Demand followed a U-shaped seasonal trend: Q4 was the highest quarter at 352,881.81 kWh, followed by Q1 (319,677.67 kWh), Q2 (270,277.36 kWh) and Q3 (264,863.12 kWh); Q4 exceeded the lowest quarter, Q3, by 88,018.69 kWh.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
  - Derived difference(kwh_q4, kwh_q3): 88018.69
- [q4] Consumption increased in the second half of 2024: July-December totalled 617,744.93 kWh versus 589,955.03 kWh in January-June, up 27,789.90 kWh or 4.71%.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature_c >= 25 C), Commercial buildings produced 19 readings with a mean consumption of 415.29 kWh per reading, a relatively small sample of the commercial portfolio.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] Consumption per reading is highly dispersed: the median is 406.8 kWh while the sample standard deviation is 913.44 kWh, indicating a strong right skew driven by large industrial readings. The mean recorded temperature is 11.61 C, with temperature missing for 62 readings. For Commercial readings, the Pearson correlation between temperature and energy use is -0.64, a moderately strong negative relationship: commercial consumption tends to decrease as temperatures rise.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Tariff usage is nearly balanced: off-peak consumption of 608,075.89 kWh slightly exceeds peak at 599,624.07 kWh (peak share 49.65%), a difference of 8,451.82 kWh. Twelve distinct meters were active, and the highest-use meter alone consumed 252,241.26 kWh — 20.89% of total portfolio consumption — indicating concentration in a few assets.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26, total_kwh=1207699.96
  - Ranking: off-peak, peak
  - Derived difference(kwh_off_peak, kwh_peak): 8451.82
  - Derived share(highest_use_meter_kwh, total_kwh): 20.89

## Limitations
- The cleaning stage failed its validation checks; although the analysis stage passed on the cleaned file, residual data-quality issues could affect these figures and should be reconfirmed.
- Temperature is missing for 62 readings, so the hot-day and temperature-correlation results are based on a reduced sample.
- Only 19 Commercial hot-day readings were available, a small sample for the 415.29 kWh hot-day mean.
- Consumption is highly skewed (median 406.8 kWh vs. standard deviation 913.44 kWh), so totals and means are driven by a small number of large industrial readings.
- The -0.64 commercial temperature-consumption correlation is observational and does not establish causation.

## Conclusion
The portfolio's 2024 electricity demand is concentrated in industrial buildings and a few high-use meters, follows a U-shaped seasonal pattern peaking in Q4, and grew modestly (4.71%) in the second half. With peak and off-peak use nearly equal (49.65% peak), cost savings are more likely to come from managing industrial and top-meter demand than from tariff shifting. Given the cleaning stage's failed validation, these figures should be reconfirmed once cleaning is re-validated.
