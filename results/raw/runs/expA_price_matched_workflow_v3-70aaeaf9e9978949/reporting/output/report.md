# 2024 Electricity Consumption Analysis Report

Analysis of 1,428 smart-meter readings from 2024 reveals a total electricity consumption of 1,207,700 kWh. Industrial usage dominated consumption, while Q4 recorded the highest quarterly demand. A moderate increase of 4.7% was observed in the second half of the year. Commercial consumption shows a strong negative correlation with temperature.

## Key findings
- [q1] The dataset contains 1,428 readings totaling 1,207,699.96 kWh, with an average consumption of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.728263
- [q2] Industrial buildings consumed 995,362.16 kWh, ranking first and significantly outpacing Commercial (196,367.15 kWh) and Residential (15,970.65 kWh) usage.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption peaked in Q4 at 352,881.81 kWh, followed by Q1 (319,677.67 kWh), Q2 (270,277.36 kWh), and Q3 (264,863.12 kWh).
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Total consumption increased from 589,955.03 kWh in H1 to 617,744.93 kWh in H2, representing a rise of 4.71%.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710512
  - Direction: increase
- [q5] On days with temperatures of 25°C or higher, 19 commercial readings were recorded with an average consumption of 415.29 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.293684
- [q6] The median consumption was 406.8 kWh with a standard deviation of 913.44 kWh. The mean temperature was 11.61°C. Commercial consumption had a strong negative correlation with temperature (-0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.438516, temperature_mean=11.612299, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636
- [q7] Off-peak tariff usage (608,075.89 kWh) exceeded peak usage (599,624.07 kWh), accounting for 50.35% of the total. 12 unique meters were tracked, with the highest single meter consuming 252,241.26 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.650086, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak
  - Derived share(kwh_off_peak, total_kwh): 50.35

## Limitations
- Temperature data was missing for 62 readings, potentially affecting the accuracy of temperature-correlated analyses.
- The analysis is limited to the specific meters and timeframe provided and may not represent broader grid trends.

## Conclusion
Industrial consumption drives the majority of electricity usage. The increase in H2 and peak in Q4 suggest seasonal or operational load shifts. The strong negative correlation between commercial usage and temperature warrants further investigation into cooling-related efficiency opportunities.
