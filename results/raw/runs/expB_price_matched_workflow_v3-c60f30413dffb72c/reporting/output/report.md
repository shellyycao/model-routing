# 2024 Electricity Consumption Analysis Report

This report details electricity consumption patterns for 2024 based on 1,428 smart-meter readings totaling 1,207,700 kWh. Industrial usage dominated the load profile, while overall consumption increased by 4.7% in the second half of the year. A significant negative correlation was found between temperature and commercial energy use.

## Key findings
- [q1] The dataset contains 1,428 readings with a total energy consumption of 1,207,699.96 kWh, resulting in a mean consumption of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial usage was the highest at 995,362.16 kWh, followed by Commercial at 196,367.15 kWh and Residential at 15,970.65 kWh.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption was highest in Q4 at 352,881.81 kWh and lowest in Q3 at 264,863.12 kWh. The full ranking from highest to lowest is Q4, Q1, Q2, Q3.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Total consumption increased from 589,955.03 kWh in H1 to 617,744.93 kWh in H2, representing a 4.71% increase.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived pct_change(kwh_h2, kwh_h1): 4.71
- [q5] On hot days (≥25°C), there were 19 commercial readings with a mean energy consumption of 415.29 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median energy consumption was 406.8 kWh with a standard deviation of 913.44 kWh. The mean temperature was 11.61°C. A strong negative correlation of -0.64 was observed between temperature and energy for commercial buildings.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Peak tariff usage (599,624.07 kWh) was slightly lower than off-peak (608,075.89 kWh), accounting for 49.65% of the total. There were 12 unique meters, with the highest single-meter usage reaching 252,241.26 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Temperature data was missing for 62 readings, which may affect the accuracy of temperature-related correlations.
- The analysis assumes the 'hot day' threshold of 25°C is the correct business logic, though the dataset mean temperature is significantly lower (11.61°C), resulting in a small sample size (19) for that subset.

## Conclusion
Electricity consumption in 2024 showed a clear dominance by the Industrial sector and a notable increase in the second half of the year. The negative correlation between temperature and commercial energy suggests different consumption drivers compared to typical cooling-load profiles. Data quality regarding temperature recording should be improved for future analysis.
