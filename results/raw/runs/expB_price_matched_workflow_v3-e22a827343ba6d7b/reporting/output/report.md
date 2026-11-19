# 2024 Electricity Consumption Analysis Report

Analysis of 1,428 smart-meter readings from 2024 reveals a total electricity consumption of 1,207,700 kWh. Industrial usage dominated the building profile, accounting for over 80% of total load. Consumption increased by 4.7% in the second half of the year. A significant negative correlation was found between temperature and commercial energy usage, and peak tariff usage comprised nearly half of the total energy recorded.

## Key findings
- [q1] The dataset contains 1,428 readings totaling 1,207,699.96 kWh, resulting in an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed the most energy (995,362.16 kWh), followed by Commercial (196,367.15 kWh) and Residential (15,970.65 kWh).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption was highest in Q4 (352,881.81 kWh) and lowest in Q3 (264,863.12 kWh).
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Energy consumption increased by 4.71% in the second half of the year (617,744.93 kWh) compared to the first half (589,955.03 kWh).
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
- [q5] On hot days (≥25°C), 19 commercial readings were recorded with a mean consumption of 415.29 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median energy consumption was 406.8 kWh with a standard deviation of 913.44 kWh. The mean temperature was 11.61°C. Commercial energy usage showed a strong negative correlation (-0.64) with temperature.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Peak tariff usage (599,624.07 kWh) was slightly lower than off-peak usage (608,075.89 kWh), representing 49.65% of the total. 12 unique meters were tracked, with the highest single-meter usage at 252,241.26 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Temperature data was missing for 62 readings, potentially affecting the precision of temperature-correlation analysis.
- The analysis assumes a uniform distribution of missing data, though bias cannot be ruled out.
- The dataset is limited to 12 unique meters, which may not fully represent the broader building portfolio.

## Conclusion
Industrial consumption drives the overall load, while commercial usage demonstrates significant sensitivity to high temperatures. The shift toward higher usage in H2 and the balanced peak/off-peak split provide actionable insights for load management and tariff optimization strategies.
