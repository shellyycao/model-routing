# 2024 Electricity Consumption Analysis Report

This report details electricity consumption for 2024 based on 1,428 smart-meter readings totaling 1,207,700 kWh. Industrial usage dominated the profile, accounting for the vast majority of consumption. Overall usage increased by 4.7% in the second half of the year. Consumption was split nearly evenly between peak and off-peak tariffs, with a moderate negative correlation observed between temperature and commercial energy use.

## Key findings
- [q1] The dataset contains 1,428 readings with a total consumption of 1,207,699.96 kWh, resulting in an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings were the top consumers with 995,362.16 kWh, followed by Commercial (196,367.15 kWh) and Residential (15,970.65 kWh).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption was highest in Q4 (352,881.81 kWh) and lowest in Q3 (264,863.12 kWh). Q1 totaled 319,677.67 kWh and Q2 totaled 270,277.36 kWh.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Total consumption increased from 589,955.03 kWh in H1 to 617,744.93 kWh in H2, representing a rise of 4.71%.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
- [q5] On days with temperatures of 25°C or higher, 19 commercial readings were recorded with a mean consumption of 415.29 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption was 406.8 kWh with a standard deviation of 913.44 kWh. The mean temperature was 11.61°C across 1,366 valid readings, while 62 readings had missing temperature data. A moderate negative correlation of -0.64 was found between temperature and commercial consumption.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
  - Derived difference(reading_count, temperature_missing_count): 1366.0
- [q7] Peak tariff usage (599,624.07 kWh) accounted for 49.65% of the total, slightly less than off-peak usage (608,075.89 kWh). 12 unique meters were tracked, with the highest single-meter usage reaching 252,241.26 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Temperature data was missing for 62 readings, potentially affecting the accuracy of temperature-correlated analyses.
- The analysis relies on a single year of data (2024), limiting the ability to identify long-term trends or seasonality beyond the observed year.
- The dataset comprises only 12 unique meters, which may not be fully representative of the broader building stock.

## Conclusion
Industrial consumption drove the majority of electricity usage in 2024. The increase in consumption during the second half of the year and the concentration of usage in Q4 warrant further investigation into seasonal operational drivers. The near-even split between peak and off-peak usage suggests a balanced load profile across tariff types.
