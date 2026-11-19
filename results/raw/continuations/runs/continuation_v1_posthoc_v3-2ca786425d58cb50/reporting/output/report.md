# 2024 Electricity Consumption Analysis Report

Analysis of 2024 smart-meter data reveals a total consumption of 1,207,700 kWh across 1,428 readings. Industrial usage dominated the portfolio, while overall consumption increased by 4.7% in the second half of the year. Commercial energy usage showed a strong negative correlation with temperature.

## Key findings
- [q1] The dataset contains 1,428 readings totaling 1,207,699.96 kWh, resulting in an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial usage was the highest at 995,362.16 kWh, followed by Commercial at 196,367.15 kWh and Residential at 15,970.65 kWh.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption was highest in Q4 at 352,881.81 kWh, followed by Q1 (319,677.67 kWh), Q2 (270,277.36 kWh), and Q3 (264,863.12 kWh).
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Consumption increased from 589,955.03 kWh in H1 to 617,744.93 kWh in H2, representing a 4.71% increase.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
- [q5] There were 19 commercial readings on hot days (temperature >= 25°C), with a mean energy consumption of 415.29 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption was 406.8 kWh with a standard deviation of 913.44 kWh. The mean temperature was 11.61°C, though 62 readings had missing temperature data. Commercial consumption showed a strong negative correlation with temperature (r = -0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Peak tariff usage (599,624.07 kWh) and off-peak usage (608,075.89 kWh) were nearly balanced, with peak comprising 49.65% of the total. 12 unique meters were tracked, with the highest single-meter usage reaching 252,241.26 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Temperature data was missing for 62 readings, potentially affecting the accuracy of temperature-correlated insights.
- The analysis assumes the '2024 smart-meter export' is a complete dataset; sampling bias in meter selection is not assessed.
- Correlation analysis between temperature and consumption was restricted to Commercial readings, limiting generalizability to other building types.

## Conclusion
The 2024 data highlights Industrial dominance and a moderate H2 consumption increase. The negative correlation between temperature and commercial consumption suggests distinct usage drivers compared to typical cooling-load profiles. Further investigation into the high-consumption industrial meters is recommended.
