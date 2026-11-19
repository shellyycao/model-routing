# 2024 Electricity Consumption Analysis Report

In 2024, total electricity consumption reached 1,207,700 kWh across 1,428 readings. Industrial usage dominated the profile, accounting for the vast majority of energy drawn. Consumption increased by 4.7% in the second half of the year. A strong negative correlation was observed between temperature and commercial energy use, indicating distinct load patterns during warmer periods.

## Key findings
- [q1] The dataset records a total of 1,207,699.96 kWh of electricity consumed across 1,428 individual readings, resulting in an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings were the primary consumers with 995,362.16 kWh, followed by Commercial at 196,367.15 kWh and Residential at 15,970.65 kWh.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption was highest in Q4 at 352,881.81 kWh and lowest in Q3 at 264,863.12 kWh. Q1 and Q2 recorded 319,677.67 kWh and 270,277.36 kWh respectively.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Consumption in the second half of the year (617,744.93 kWh) exceeded the first half (589,955.03 kWh), representing an increase of 4.71%.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
- [q5] On days with temperatures of 25°C or higher, 19 commercial readings were recorded with a mean consumption of 415.29 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption was 406.8 kWh with a standard deviation of 913.44 kWh. The mean temperature was 11.61°C. Commercial consumption showed a strong negative correlation with temperature (-0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.6376362398654432
- [q7] Peak and off-peak consumption were nearly balanced, with off-peak usage (608,075.89 kWh) slightly exceeding peak (599,624.07 kWh). Peak usage accounted for 49.65% of the total. 12 unique meters were tracked, with the highest single meter consuming 252,241.26 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Temperature data was missing for 62 readings, potentially affecting the accuracy of temperature-correlated analysis.
- The analysis relies on the 'building_type' classification provided in the raw export; any misclassification in the source data would impact the group comparisons.
- The 'hot day' analysis is based on a limited sample size of 19 readings for commercial buildings, which may not be fully representative of broader trends.

## Conclusion
Industrial consumption drives the majority of the energy load. The increase in H2 and the strong negative correlation between temperature and commercial usage suggest seasonal or operational shifts that warrant further investigation for load balancing and tariff optimization.
