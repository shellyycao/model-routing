# 2024 Smart-Meter Electricity Consumption: Verified Findings for Business Stakeholders

In 2024, 1,428 cleaned smart-meter readings from 12 unique meters totalled 1,207,699.96 kWh, an average of 845.73 kWh per reading. Industrial sites drove demand with 995,362.16 kWh, about 82.4% of all consumption, far ahead of Commercial (196,367.15 kWh) and Residential (15,970.65 kWh). Usage peaked in Q4 (352,881.81 kWh) and bottomed in Q3 (264,863.12 kWh); second-half consumption rose 4.71% versus the first half. Off-peak tariff use (608,075.89 kWh) marginally exceeded peak use (599,624.07 kWh). Commercial readings on hot days averaged 415.29 kWh, and commercial consumption correlated moderately negatively with temperature (r = -0.64).

## Key findings
- [q1] The cleaned 2024 export contains 1,428 readings totalling 1,207,699.96 kWh, an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial sites dominate demand at 995,362.16 kWh, about 82.4% of total consumption, followed by Commercial (196,367.15 kWh) and then Residential (15,970.65 kWh).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
- [q3] Consumption was highest in Q4 (352,881.81 kWh), then Q1 (319,677.67 kWh), Q2 (270,277.36 kWh) and Q3 (264,863.12 kWh), a U-shaped year with strong winter quarters and a late-summer trough.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,744.93 kWh) rose 4.71% versus the first half (589,955.03 kWh), an increase of 27,789.9 kWh.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature at or above 25 °C), only 19 commercial readings were recorded, averaging 415.29 kWh each.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] Consumption is strongly right-skewed: the median reading is 406.8 kWh while the standard deviation is 913.44 kWh. Mean temperature is 11.61 °C, 62 readings lack temperature data, and commercial consumption correlates moderately negatively with temperature (r = -0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak use (608,075.89 kWh, about 50.35% of total) slightly exceeds peak use (599,624.07 kWh; peak share 49.65%). Twelve unique meters report; the highest-use meter alone consumed 252,241.26 kWh, roughly 20.9% of all energy.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak
  - Derived share(kwh_off_peak, total_kwh): 50.35
  - Derived share(highest_use_meter_kwh, total_kwh): 20.9

## Limitations
- 62 readings are missing temperature, so the hot-day and temperature-correlation results rest on a reduced sample.
- Only 19 hot-day commercial readings exist, making the 415.29 kWh hot-day average a small-sample estimate.
- Findings describe this 12-meter portfolio only; the heavy industrial skew means totals are not representative of typical buildings.
- The negative commercial temperature correlation is associative, not causal, and data cover a single year, preventing year-over-year comparison.

## Conclusion
2024 demand was concentrated in industrial sites and the winter quarters, grew modestly in the second half (+4.71%), and split almost evenly between peak and off-peak tariffs. Recommended priorities: monitor the largest meter (252,241.26 kWh, about 20.9% of total), investigate the counterintuitive negative commercial temperature correlation, and close temperature data gaps before the next planning cycle.
