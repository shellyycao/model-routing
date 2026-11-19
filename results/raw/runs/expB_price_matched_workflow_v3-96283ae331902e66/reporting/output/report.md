# 2024 Electricity Consumption Analysis Report

This report presents the analysis of 1,428 smart-meter readings from 2024, totaling 1,207,700 kWh of electricity consumption. Industrial usage dominated the portfolio, accounting for 82.4% of total energy. Consumption increased by 4.7% in the second half of the year. A significant negative correlation was found between temperature and commercial energy use.

## Key findings
- [q1] The dataset contains 1,428 readings with a total consumption of 1,207,700 kWh, averaging 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial consumption was the highest at 995,362 kWh, followed by Commercial (196,367 kWh) and Residential (15,971 kWh).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
- [q3] Quarterly consumption fluctuated, with Q4 being the highest (352,882 kWh) and Q3 the lowest (264,863 kWh).
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Consumption increased by 4.7% in the second half of the year (617,745 kWh) compared to the first half (589,955 kWh).
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
- [q5] On 19 hot days (temperature ≥25°C), commercial buildings consumed an average of 415.3 kWh per reading.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption was 406.8 kWh with a standard deviation of 913.4 kWh. The mean temperature was 11.6°C. Commercial consumption showed a moderate negative correlation (-0.64) with temperature.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Peak and off-peak consumption were nearly balanced, with peak usage at 599,624 kWh (49.7% of total). 12 unique meters were tracked, with the highest single meter consuming 252,241 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Temperature data was missing for 62 readings, potentially affecting the accuracy of temperature-correlation analysis.
- The analysis assumes the 'hot day' threshold of 25°C is the relevant criterion for commercial load analysis, though cooling needs may vary.
- Data is limited to the year 2024 and may not reflect long-term trends.

## Conclusion
Industrial consumption drives the majority of energy load, which peaked in Q4. The positive growth in H2 suggests increasing demand. The negative correlation between temperature and commercial consumption warrants further investigation into heating vs. cooling loads.
