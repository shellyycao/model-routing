# 2024 Electricity Consumption Analysis Report

The 2024 smart-meter dataset comprises 1,428 readings totaling 1,207,700 kWh. Industrial usage dominated consumption, accounting for 82.4% of the total load. Overall consumption increased by 4.7% in the second half of the year. A significant negative correlation was observed between temperature and commercial energy usage, and peak tariff usage slightly trailed off-peak usage.

## Key findings
- [q1] The dataset contains 1,428 readings with a total consumption of 1,207,700.0 kWh, averaging 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial usage was the highest at 995,362.2 kWh (82.4% of total), followed by Commercial at 196,367.1 kWh and Residential at 15,970.7 kWh.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
- [q3] Consumption varied by quarter: Q4 was highest at 352,881.8 kWh, followed by Q1 (319,677.7 kWh), Q2 (270,277.4 kWh), and Q3 (264,863.1 kWh).
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Total consumption increased from 589,955.0 kWh in H1 to 617,744.9 kWh in H2, representing a 4.7% rise.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
- [q5] There were 19 commercial readings on hot days (temperature ≥ 25°C) with an average consumption of 415.3 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption was 406.8 kWh with a standard deviation of 913.4 kWh. The mean temperature was 11.6°C. Commercial consumption showed a strong negative correlation with temperature (r = -0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak consumption (608,075.9 kWh) exceeded peak consumption (599,624.1 kWh), with peak usage accounting for 49.7% of the total. 12 unique meters were tracked, with the highest single meter totaling 252,241.3 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Temperature data was missing for 62 readings, potentially affecting the accuracy of temperature-correlated analysis.
- The analysis assumes the 'cleaned' data accurately represents the population; anomalies removed during cleaning are not accounted for.

## Conclusion
Industrial consumption drives the majority of the load. The increase in H2 suggests seasonal or operational shifts. The negative correlation between temperature and commercial usage suggests higher cooling demands or occupancy patterns in hotter weather, warranting further investigation into efficiency opportunities during peak temperature periods.
